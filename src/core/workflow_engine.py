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
    TestCaseResult, TestStatus, HealingType, BugSeverity, TestMode
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
    CANCELLED = "已取消"


@dataclass
class WorkflowConfig:
    """工作流配置"""
    max_healing_attempts: int = 3       # 最大自愈次数
    cli_timeout: int = 1200             # CLI 调用超时 (20分钟)
    test_timeout: int = 45              # 单个测试用例超时
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
            self._set_state(WorkflowState.CANCELLED, "任务已被取消")
            raise WorkflowCancelled("任务已被取消")

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
            self._set_state(WorkflowState.CANCELLED, "任务已取消")
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

        # 显示测试模式
        mode_desc = {
            TestMode.INTERFACE: "接口测试 (仅 Swagger)",
            TestMode.BUSINESS: "业务测试 (Swagger + PRD，自动生成数据)",
            TestMode.COMPLETE: "完整测试 (Swagger + PRD + 测试数据)"
        }
        current_mode = self.context.test_mode
        self._log("info", "planning", f"测试模式: {mode_desc.get(current_mode, current_mode.value)}")

        # 显示输入文件统计
        if self.context.has_prd:
            self._log("info", "planning", "PRD 文档: 已加载")
        if self.context.has_test_data:
            self._log("info", "planning", f"测试数据: {len(self.context.test_data_files)} 个文件")

        # 预创建输出目录，确保 CLI 可以写入文件
        output_path = Path(self.context.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        self._log("info", "planning", f"输出目录: {output_path}")

        # 静态依赖分析 (接口测试模式和业务测试模式都需要)
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

        # 构建 Prompt (根据测试模式自动选择)
        prompt_pkg = self.prompt_builder.build_plan_prompt(self.context)

        # 更新 CLI 权限
        self.cli_adapter.config.allowed_tools = prompt_pkg.allowed_tools

        # 调用 CLI
        if current_mode in (TestMode.BUSINESS, TestMode.COMPLETE):
            self._log("info", "planning", "调用 CLI 分析 PRD + Swagger...")
        else:
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

        # 解析业务分析结果 (如果是业务测试模式)
        if current_mode in (TestMode.BUSINESS, TestMode.COMPLETE):
            self._parse_business_analysis(output_path)

        self._log("info", "planning", f"规划完成，用例文档已生成")

    def _fix_llm_json_syntax(self, json_text: str) -> str:
        """修复 LLM 生成的常见 JSON 语法错误

        处理的问题:
        - JavaScript 语法如 "A".repeat(100) -> 替换为实际的重复字符串
        - 尾部多余逗号
        """
        import re

        # 修复 "X".repeat(N) 语法 -> 实际的重复字符串
        # 匹配模式: "单个字符".repeat(数字)
        repeat_pattern = r'"([^"]{1,3})"\.repeat\((\d+)\)'

        def replace_repeat(match):
            char = match.group(1)
            count = int(match.group(2))
            # 限制最大长度，避免生成过大的字符串
            max_count = min(count, 1000)
            return '"' + (char * max_count) + '"'

        fixed_text = re.sub(repeat_pattern, replace_repeat, json_text)

        # 修复尾部多余逗号 (trailing comma)
        # 匹配 ,] 或 ,} 并移除逗号
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)

        return fixed_text

    def _parse_business_analysis(self, output_path: Path) -> None:
        """解析业务分析结果，更新 context

        从 analysis_result.json 中读取:
        - scenarios: 业务场景
        - rules: 业务规则
        - data_mapping: 数据映射
        """
        analysis_file = output_path / "analysis_result.json"
        if not analysis_file.exists():
            self._log("warning", "planning", "未找到业务分析结果文件，跳过解析")
            return

        try:
            json_text = analysis_file.read_text(encoding='utf-8')

            # 第一次尝试：直接解析
            try:
                analysis_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                # 第二次尝试：修复常见 LLM 语法错误后重新解析
                self._log("warning", "planning",
                          f"JSON 解析失败，尝试修复 LLM 语法错误: {e}")
                fixed_text = self._fix_llm_json_syntax(json_text)

                # 保存修复后的文件（用于调试）
                fixed_file = output_path / "analysis_result_fixed.json"
                fixed_file.write_text(fixed_text, encoding='utf-8')

                analysis_data = json.loads(fixed_text)
                self._log("info", "planning", "JSON 语法修复成功")

            # 更新 context
            if 'scenarios' in analysis_data:
                self.context.scenarios = analysis_data['scenarios']
                self._log("info", "planning",
                          f"识别业务场景: {len(self.context.scenarios)} 个")

            if 'rules' in analysis_data:
                self.context.business_rules = analysis_data['rules']
                self._log("info", "planning",
                          f"提取业务规则: {len(self.context.business_rules)} 条")

            if 'data_mapping' in analysis_data:
                self.context.data_mapping = analysis_data['data_mapping']
                self._log("info", "planning",
                          f"数据映射: {len(self.context.data_mapping)} 个接口")

            # 统计信息
            stats = analysis_data.get('statistics', {})
            if stats:
                self._log("info", "planning",
                          f"预计测试用例: {stats.get('estimated_cases', '未知')} 个")

        except Exception as e:
            self._log("warning", "planning", f"解析业务分析结果失败: {e}")

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
            if ("任务已取消" in (result.error or "")) or result.exit_code == -2:
                raise WorkflowCancelled("任务已取消")
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

        # 构建业务规则内容（优先使用 PRD，其次用 requirements）
        business_context = ""
        if getattr(self.context, "business_rules", None) and self.context.business_rules:
            # 使用 Phase 1 提取的结构化规则
            business_context = "## 业务规则（从 PRD 提取）\n"
            for rule in self.context.business_rules:
                rule_name = rule.get('name', '未命名规则')
                rule_desc = rule.get('description', '')
                rule_assertion = rule.get('assertion', '')
                business_context += f"- {rule_name}: {rule_desc}\n"
                if rule_assertion:
                    business_context += f"  断言: {rule_assertion}\n"
        elif getattr(self.context, "prd_document", None) and self.context.prd_document:
            # 使用 PRD 原文（截取关键部分）
            business_context = f"## PRD 文档摘要\n{self.context.prd_document[:5000]}"
        elif self.context.requirements:
            # 兼容旧版
            business_context = self.context.requirements

        # 构建自愈 Prompt
        prompt_pkg = self.prompt_builder.build_heal_logic_prompt(
            result.error_info,
            business_context
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

        # 保存完整执行报告
        self._save_execution_report(report)

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

    def _save_execution_report(self, report: FinalReport) -> None:
        """保存完整执行报告，方便后续溯源"""
        output_path = Path(self.context.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        report_file = output_path / "execution_report.json"
        report_file.write_text(
            report.to_json(),
            encoding='utf-8'
        )
        self._log("info", "finalization", f"执行报告已保存: execution_report.json")


# 便捷函数
def run_workflow(
    context: TaskContext,
    on_log: Optional[Callable[[str, str, str], None]] = None
) -> FinalReport:
    """运行工作流的便捷函数"""
    config = WorkflowConfig(on_log=on_log)
    engine = WorkflowEngine(context, config)
    return engine.run()
