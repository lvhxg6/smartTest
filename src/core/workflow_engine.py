"""
WorkflowEngine - 工作流引擎

核心编排器，负责:
- 四阶段流程控制 (规划 → 生成 → 执行+自愈 → 交付)
- CLI 会话管理
- 自愈循环控制
- 日志和状态通知
"""

import logging
import json
import time
from pathlib import Path
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable

from ..models import (
    TaskContext, FinalReport, BugReport, TestCaseDoc,
    TestCaseResult, TestStatus, HealingType, BugSeverity
)
from .cli_adapter import CLIAdapter, CLISession, CLIConfig, ExecutionMode
from .prompt_builder import PromptBuilder
from .pytest_runner import PytestRunner, PytestConfig
from .result_judge import ResultJudge

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    """工作流状态"""
    INIT = "初始化"
    PLANNING = "规划测试场景"
    GENERATING = "生成测试代码"
    EXECUTING = "执行测试"
    HEALING = "自愈修复中"
    FINALIZING = "生成报告"
    COMPLETED = "已完成"
    FAILED = "失败"


@dataclass
class WorkflowConfig:
    """工作流配置"""
    max_healing_attempts: int = 3       # 最大自愈次数
    cli_timeout: int = 180              # CLI 调用超时
    test_timeout: int = 120             # 单个测试用例超时
    on_state_change: Optional[Callable[[WorkflowState, str], None]] = None
    on_log: Optional[Callable[[str, str, str], None]] = None  # (level, phase, message)


class WorkflowEngine:
    """工作流引擎

    编排整个测试流程:
    Phase 1: 规划 - 生成 testcases.md
    Phase 2: 生成 - 生成 test_*.py
    Phase 3: 执行 + 自愈 - 运行测试并修复
    Phase 4: 交付 - 生成报告
    """

    def __init__(
        self,
        context: TaskContext,
        config: Optional[WorkflowConfig] = None
    ):
        self.context = context
        self.config = config or WorkflowConfig()
        self.state = WorkflowState.INIT

        # 初始化组件
        cli_config = CLIConfig(timeout=self.config.cli_timeout)
        self.cli_adapter = CLIAdapter(cli_config)
        self.cli_session = CLISession(self.cli_adapter)
        self.prompt_builder = PromptBuilder()
        self.pytest_runner = PytestRunner(
            PytestConfig(timeout=self.config.test_timeout)
        )
        self.result_judge = ResultJudge(
            context.test_mode,
            self.config.max_healing_attempts
        )

        # 运行时数据
        self.test_results: List[TestCaseResult] = []
        self.bugs: List[BugReport] = []
        self.start_time: Optional[float] = None

    def _set_state(self, state: WorkflowState, message: str = "") -> None:
        """更新状态"""
        self.state = state
        logger.info(f"[{state.value}] {message}")
        if self.config.on_state_change:
            self.config.on_state_change(state, message)

    def _log(self, level: str, phase: str, message: str) -> None:
        """记录日志"""
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{phase}] {message}")
        if self.config.on_log:
            self.config.on_log(level, phase, message)

    def run(self) -> FinalReport:
        """执行完整工作流

        Returns:
            FinalReport 最终测试报告
        """
        self.start_time = time.time()

        try:
            # Phase 1: 规划
            self._set_state(WorkflowState.PLANNING)
            self._phase_planning()

            # Phase 2: 生成
            self._set_state(WorkflowState.GENERATING)
            self._phase_generation()

            # Phase 3: 执行 + 自愈
            self._set_state(WorkflowState.EXECUTING)
            self._phase_execution()

            # Phase 4: 交付
            self._set_state(WorkflowState.FINALIZING)
            report = self._phase_finalization()

            self._set_state(WorkflowState.COMPLETED, f"通过率: {report.pass_rate:.1f}%")
            return report

        except Exception as e:
            self._set_state(WorkflowState.FAILED, str(e))
            logger.exception("Workflow failed")
            raise

        finally:
            self.cli_session.end()

    def _phase_planning(self) -> None:
        """Phase 1: 规划"""
        self._log("info", "planning", "开始规划测试场景...")

        # 构建 Prompt
        prompt_pkg = self.prompt_builder.build_plan_prompt(self.context)

        # 更新 CLI 权限
        self.cli_adapter.config.allowed_tools = prompt_pkg.allowed_tools

        # 调用 CLI
        self._log("info", "planning", "调用 CLI 分析 Swagger...")
        result = self.cli_session.start(prompt_pkg.prompt)

        if not result.success:
            raise RuntimeError(f"规划阶段失败: {result.error}")

        self._log("info", "planning", f"规划完成，用例文档已生成")

    def _phase_generation(self) -> None:
        """Phase 2: 生成"""
        self._log("info", "generation", "开始生成测试代码...")

        # 构建 Prompt
        prompt_pkg = self.prompt_builder.build_generate_prompt(self.context)

        # 更新 CLI 权限
        self.cli_adapter.config.allowed_tools = prompt_pkg.allowed_tools

        # 调用 CLI (继续会话)
        self._log("info", "generation", "调用 CLI 生成 Pytest 代码...")
        result = self.cli_session.send(prompt_pkg.prompt)

        if not result.success:
            raise RuntimeError(f"生成阶段失败: {result.error}")

        self._log("info", "generation", "代码生成完成")

    def _phase_execution(self) -> None:
        """Phase 3: 执行 + 自愈"""
        test_dir = Path(self.context.output_dir) / "tests"
        output_dir = Path(self.context.output_dir) / "reports"

        self._log("info", "execution", f"开始执行测试: {test_dir}")

        # 运行 pytest
        pytest_result = self.pytest_runner.run(
            str(test_dir),
            str(output_dir)
        )

        self._log(
            "info", "execution",
            f"初始执行完成: 通过 {pytest_result.passed}/{pytest_result.total}"
        )

        # 处理失败的用例
        failed_results = pytest_result.get_failed_results()

        for result in failed_results:
            self._handle_failed_test(result, test_dir, output_dir)

        # 合并结果
        self.test_results = pytest_result.test_results

    def _handle_failed_test(
        self,
        result: TestCaseResult,
        test_dir: Path,
        output_dir: Path
    ) -> None:
        """处理失败的测试用例"""
        judge_result = self.result_judge.judge(result)

        self._log(
            "warning", "execution",
            f"{result.testcase_id}: {judge_result.error_detail}"
        )

        if not judge_result.need_healing:
            # 不需要自愈
            if judge_result.is_bug:
                self._record_bug(result, judge_result.error_detail)
            return

        # 需要自愈
        self._set_state(WorkflowState.HEALING)

        if judge_result.healing_type == HealingType.SYNTAX:
            self._heal_syntax(result)
        elif judge_result.healing_type == HealingType.LOGIC:
            self._heal_logic(result)

    def _heal_syntax(self, result: TestCaseResult) -> None:
        """语法自愈"""
        self._log("info", "healing", f"触发语法自愈: {result.testcase_id}")

        if result.error_info is None:
            return

        # 构建自愈 Prompt
        prompt_pkg = self.prompt_builder.build_heal_syntax_prompt(result.error_info)
        self.cli_adapter.config.allowed_tools = prompt_pkg.allowed_tools

        # 调用 CLI 修复
        cli_result = self.cli_session.send(prompt_pkg.prompt)

        if cli_result.success:
            result.healing_attempts += 1
            result.healed = True
            self._log("info", "healing", f"语法修复完成: {result.testcase_id}")
        else:
            self._log("error", "healing", f"语法修复失败: {cli_result.error}")

    def _heal_logic(self, result: TestCaseResult) -> None:
        """逻辑自愈"""
        self._log("info", "healing", f"触发逻辑自愈: {result.testcase_id}")

        if result.error_info is None:
            return

        # 构建自愈 Prompt
        prompt_pkg = self.prompt_builder.build_heal_logic_prompt(
            result.error_info,
            self.context.requirements
        )
        self.cli_adapter.config.allowed_tools = prompt_pkg.allowed_tools

        # 调用 CLI 判定
        cli_result = self.cli_session.send(prompt_pkg.prompt)

        if cli_result.success and cli_result.output:
            # 解析 CLI 响应判断是 Bug 还是代码问题
            is_bug = self._parse_logic_healing_result(cli_result.output)

            if is_bug:
                self._record_bug(result, cli_result.output)
                self._log("info", "healing", f"判定为真 Bug: {result.testcase_id}")
            else:
                result.healing_attempts += 1
                result.healed = True
                self._log("info", "healing", f"断言已修正: {result.testcase_id}")

    def _parse_logic_healing_result(self, output: str) -> bool:
        """解析逻辑自愈结果，判断是否为 Bug"""
        try:
            # 尝试从输出中提取 JSON
            if '"verdict": "BUG_FOUND"' in output:
                return True
            if '"verdict":' in output and 'BUG' in output.upper():
                return True
        except:
            pass
        return False

    def _record_bug(self, result: TestCaseResult, detail: str) -> None:
        """记录 Bug"""
        bug = BugReport(
            testcase_id=result.testcase_id,
            api=f"{result.function_name} in {result.file_path}",
            scenario=result.function_name,
            expected=result.error_info.expected if result.error_info else "未知",
            actual=result.error_info.actual if result.error_info else "未知",
            severity=BugSeverity.MEDIUM,
            root_cause=detail
        )
        self.bugs.append(bug)

    def _phase_finalization(self) -> FinalReport:
        """Phase 4: 交付"""
        self._log("info", "finalization", "生成最终报告...")

        duration = time.time() - self.start_time if self.start_time else 0

        # 统计结果
        passed = sum(1 for r in self.test_results if r.status == TestStatus.PASS)
        failed = sum(1 for r in self.test_results if r.status != TestStatus.PASS)
        healed = sum(1 for r in self.test_results if r.healed)

        # 构建报告
        report = FinalReport(
            project_name=self.context.swagger.title or "API Test",
            generated_at=datetime.now().isoformat(),
            execution_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_cases=len(self.test_results),
            passed=passed,
            failed=failed,
            bugs_found=len(self.bugs),
            healed_count=healed,
            total_duration=duration,
            test_results=self.test_results,
            bugs=self.bugs,
            output_dir=self.context.output_dir,
            testcases_file=f"{self.context.output_dir}/testcases.md",
            report_html=f"{self.context.output_dir}/reports/report.html",
            report_xml=f"{self.context.output_dir}/reports/results.xml",
            bug_report_file=f"{self.context.output_dir}/bug_report.json"
        )

        # 保存 Bug 报告
        self._save_bug_report(report)

        self._log(
            "info", "finalization",
            f"报告生成完成: 通过率 {report.pass_rate:.1f}%"
        )

        return report

    def _save_bug_report(self, report: FinalReport) -> None:
        """保存 Bug 报告"""
        if not self.bugs:
            return

        output_path = Path(self.context.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        bug_data = {
            "summary": {
                "total": len(self.bugs),
                "high": sum(1 for b in self.bugs if b.severity == BugSeverity.HIGH),
                "medium": sum(1 for b in self.bugs if b.severity == BugSeverity.MEDIUM),
                "low": sum(1 for b in self.bugs if b.severity == BugSeverity.LOW)
            },
            "bugs": [b.to_dict() for b in self.bugs]
        }

        bug_file = output_path / "bug_report.json"
        bug_file.write_text(
            json.dumps(bug_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )


# 便捷函数
def run_workflow(
    context: TaskContext,
    on_log: Optional[Callable[[str, str, str], None]] = None
) -> FinalReport:
    """运行工作流的便捷函数"""
    config = WorkflowConfig(on_log=on_log)
    engine = WorkflowEngine(context, config)
    return engine.run()
