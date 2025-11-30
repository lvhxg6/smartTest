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
from .dependency_analyzer import DependencyAnalyzer
from .dependency_explorer import DependencyExplorer
from .skeleton_writer import SkeletonWriter
from .testcase_parser import TestCaseParser, ParsedTestCase
from .report_generator import BusinessReportGenerator

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
    cli_timeout: int = 1200             # CLI 调用超时 (20分钟)
    test_timeout: int = 120             # 单个测试用例超时
    enable_exploration: bool = False    # 是否启用依赖探测（默认关闭）
    cancel_event: Optional[Any] = None  # 取消信号（由外部传入 threading.Event）
    on_state_change: Optional[Callable[[WorkflowState, str], None]] = None
    on_log: Optional[Callable[[str, str, str], None]] = None  # (level, phase, message)
    on_todo_update: Optional[Callable[[List[Dict[str, Any]]], None]] = None  # Todo 更新回调


class WorkflowCancelled(RuntimeError):
    """工作流被用户取消"""
    pass


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

        # 初始化组件 - 设置 CLI 工作目录为输出目录的父目录
        cli_config = CLIConfig(
            timeout=self.config.cli_timeout,
            working_dir=str(Path(context.output_dir).parent.parent),  # 项目根目录
            on_output=lambda msg: self._log("info", "cli", msg),  # 实时进度回调
            on_todo_update=self.config.on_todo_update,  # Todo 进度回调
            cancel_event=self.config.cancel_event
        )
        self.cli_adapter = CLIAdapter(cli_config)
        self.cli_session = CLISession(self.cli_adapter)
        self.prompt_builder = PromptBuilder()
        self.pytest_runner = PytestRunner(
            PytestConfig(
                timeout=self.config.test_timeout,
                on_output=lambda line: self._log("info", "pytest", line.rstrip())
            )
        )
        self.result_judge = ResultJudge(
            context.test_mode,
            self.config.max_healing_attempts
        )
        self.dependency_analyzer = DependencyAnalyzer()
        # 探测仅做快速 GET 提取，限制超时/数量，避免拖慢流程
        self.dependency_explorer = DependencyExplorer(
            timeout=min(self.config.test_timeout, 5)
        )
        self.skeleton_writer = SkeletonWriter(
            base_url=context.config.base_url,
            auth_token=context.config.auth_token or "",
            timeout=self.config.test_timeout
        )

        # 运行时数据
        self.test_results: List[TestCaseResult] = []
        self.bugs: List[BugReport] = []
        self.start_time: Optional[float] = None
        # 测试用例解析器和映射表
        self.testcase_parser = TestCaseParser()
        self.testcase_map: Dict[str, ParsedTestCase] = {}
        # 业务报告生成器
        self.report_generator = BusinessReportGenerator()


    def _check_cancel(self) -> None:
        """若收到取消信号则中断"""
        if self.config.cancel_event and getattr(self.config.cancel_event, "is_set", lambda: False)():
            self._set_state(WorkflowState.FAILED, "任务已被取消")
            raise RuntimeError("任务已被取消")

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
            self._check_cancel()
            self._set_state(WorkflowState.PLANNING)
            self._phase_planning()

            # Phase 2: 生成
            self._check_cancel()
            self._set_state(WorkflowState.GENERATING)
            self._phase_generation()

            # Phase 3: 执行 + 自愈
            self._check_cancel()
            self._set_state(WorkflowState.EXECUTING)
            self._phase_execution()

            # Phase 4: 交付
            self._check_cancel()
            self._set_state(WorkflowState.FINALIZING)
            report = self._phase_finalization()

            self._set_state(WorkflowState.COMPLETED, f"通过率: {report.pass_rate:.1f}%")
            return report

        except WorkflowCancelled:
            self._set_state(WorkflowState.FAILED, "任务已取消")
            logger.warning("Workflow cancelled by user")
            return None
        except Exception as e:
            # 若是取消，记录友好日志，避免打印大段异常
            is_cancel = self.config.cancel_event and getattr(self.config.cancel_event, "is_set", lambda: False)()
            self._set_state(WorkflowState.FAILED, str(e) if not is_cancel else "任务已取消")
            if is_cancel:
                logger.warning("Workflow cancelled by user")
            else:
                logger.exception("Workflow failed")
            raise

        finally:
            self.cli_session.end()

    def _phase_planning(self) -> None:
        """Phase 1: 规划"""
        self._log("info", "planning", "开始规划测试场景...")

        # 预创建输出目录，确保 CLI 可以写入文件
        output_path = Path(self.context.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        self._log("info", "planning", f"输出目录: {output_path}")

        # 静态依赖分析
        self._log("info", "planning", "执行静态依赖分析...")
        analysis = self.dependency_analyzer.analyze(self.context.swagger)
        analysis.save(str(output_path))
        self.context.dependency_analysis = analysis

        # 可选依赖探测（默认关闭）
        if self.config.enable_exploration:
            self._log("info", "planning", "执行依赖探测以获取真实ID...")
            exploration = self.dependency_explorer.explore(self.context, analysis)
            exploration.save(str(output_path))
            self.context.exploration_data = exploration
            self._log(
                "info", "planning",
                f"探测完成，提取字段: {len(exploration.extracted_values)}"
            )

        # 构建 Prompt
        prompt_pkg = self.prompt_builder.build_plan_prompt(self.context)

        # 更新 CLI 权限
        self.cli_adapter.config.allowed_tools = prompt_pkg.allowed_tools

        # 调用 CLI
        self._log("info", "planning", "调用 CLI 分析 Swagger...")
        result = self.cli_session.start(prompt_pkg.prompt)

        if not result.success:
            detail = result.error or result.output or ""
            # 追加退出码信息，便于定位 CLI 失败原因
            extra = f" (exit_code={result.exit_code})" if result.exit_code not in (0, None) else ""
            if isinstance(result.parsed_output, dict) and not detail:
                detail = str(result.parsed_output.get("error") or result.parsed_output.get("result") or "")
            self._log("error", "planning", f"规划失败: {detail or '未知错误'}{extra}")
            # 用户主动取消时，抛出特定异常，外层不再打印大段栈
            if ("任务已取消" in (detail or "")) or result.exit_code == -2:
                raise WorkflowCancelled("任务已取消")
            raise RuntimeError(f"规划阶段失败: {detail or '未知错误'}{extra}")

        self._log("info", "planning", f"规划完成，用例文档已生成")

    def _phase_generation(self) -> None:
        """Phase 2: 生成"""
        self._log("info", "generation", "开始生成测试代码...")

        # 先写入固定骨架，避免模型重复生成
        self.skeleton_writer.write(self.context.output_dir)

        # 构建 Prompt
        prompt_pkg = self.prompt_builder.build_generate_prompt(self.context)

        # 更新 CLI 权限
        self.cli_adapter.config.allowed_tools = prompt_pkg.allowed_tools

        # 调用 CLI (继续会话)
        self._check_cancel()
        self._log("info", "generation", "调用 CLI 生成 Pytest 代码...")
        result = self.cli_session.send(prompt_pkg.prompt)

        if not result.success:
            raise RuntimeError(f"生成阶段失败: {result.error}")

        self._log("info", "generation", "代码生成完成")

    def _phase_execution(self) -> None:
        """Phase 3: 执行 + 自愈"""
        test_dir = Path(self.context.output_dir) / "tests"
        output_dir = Path(self.context.output_dir) / "reports"

        # 解析 testcases.md 建立用例映射，用于丰富日志输出
        testcases_path = Path(self.context.output_dir) / "testcases.md"
        self.testcase_map = self.testcase_parser.parse(str(testcases_path))
        self._log("info", "execution", f"加载测试用例映射: {len(self.testcase_map)} 条")

        self._log("info", "execution", f"开始执行测试: {test_dir}")

        # 运行 pytest
        self._check_cancel()
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

        # 使用解析器获取丰富的展示标签
        label = self.testcase_parser.get_label(result.testcase_id, self.testcase_map)
        self._log(
            "warning", "execution",
            f"{label}: {judge_result.error_detail}"
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

        # 关联测试用例设计与执行结果
        self._populate_test_cases(report)

        # 生成业务级 HTML 报告
        business_report_path = self.report_generator.generate(
            report, self.context.output_dir
        )
        report.business_report = business_report_path
        self._log("info", "finalization", f"业务报告已生成: {Path(business_report_path).name}")

        # 保存 Bug 报告
        self._save_bug_report(report)

        self._log(
            "info", "finalization",
            f"报告生成完成: 通过率 {report.pass_rate:.1f}%"
        )

        return report

    def _populate_test_cases(self, report: FinalReport) -> None:
        """填充 test_cases，关联测试用例设计与执行结果"""
        # 构建 testcase_id -> result 的映射
        result_map: Dict[str, TestCaseResult] = {
            r.testcase_id: r for r in self.test_results if r.testcase_id
        }

        for tc_id, parsed_tc in self.testcase_map.items():
            result = result_map.get(tc_id)
            doc = TestCaseDoc(
                testcase_id=tc_id,
                api=parsed_tc.api,
                scenario=parsed_tc.scenario,
                precondition="",
                test_data=parsed_tc.test_data,
                expected_result=parsed_tc.expected_result,
                priority=parsed_tc.priority,
                status=result.status if result else None,
                linked_function=result.function_name if result else None,
                linked_file=result.file_path if result else None
            )
            report.test_cases.append(doc)

        self._log(
            "info", "finalization",
            f"已关联 {len(report.test_cases)} 个测试用例"
        )

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
