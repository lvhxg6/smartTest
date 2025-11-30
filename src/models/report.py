"""
Report Models - 报告模型

包含:
- BugReport: Bug报告
- FinalReport: 最终测试报告
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from .result import TestCaseResult, TestStatus


class BugSeverity(Enum):
    """Bug严重程度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class BugReport:
    """Bug报告"""
    testcase_id: str                # TC-XXX
    api: str                        # POST /api/v1/order
    scenario: str                   # 场景描述
    expected: str                   # 期望结果
    actual: str                     # 实际结果
    severity: BugSeverity           # 严重程度
    root_cause: str = ""            # 根因分析
    evidence: Optional[Dict] = None # 证据 (request/response)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "testcase_id": self.testcase_id,
            "api": self.api,
            "scenario": self.scenario,
            "expected": self.expected,
            "actual": self.actual,
            "severity": self.severity.value,
            "root_cause": self.root_cause,
            "evidence": self.evidence
        }


@dataclass
class TestCaseDoc:
    """测试用例文档项"""
    testcase_id: str                # TC-XXX
    api: str                        # POST /api/v1/order
    scenario: str                   # 场景描述
    precondition: str = ""          # 前置条件
    test_data: str = ""             # 测试数据
    expected_result: str = ""       # 预期结果
    priority: str = "P1"            # 优先级
    # 执行后更新
    status: Optional[TestStatus] = None
    linked_function: Optional[str] = None  # 关联的测试函数
    linked_file: Optional[str] = None      # 关联的测试文件

    def to_dict(self) -> Dict[str, Any]:
        return {
            "testcase_id": self.testcase_id,
            "api": self.api,
            "scenario": self.scenario,
            "precondition": self.precondition,
            "test_data": self.test_data,
            "expected_result": self.expected_result,
            "priority": self.priority,
            "status": self.status.value if self.status else None,
            "linked_function": self.linked_function,
            "linked_file": self.linked_file
        }


@dataclass
class FinalReport:
    """最终测试报告"""
    # 基本信息
    project_name: str = "API Test"
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    execution_time: str = ""        # 执行完成时间

    # 统计数据
    total_cases: int = 0            # 总用例数
    passed: int = 0                 # 通过数
    failed: int = 0                 # 失败数
    bugs_found: int = 0             # 发现的Bug数
    healed_count: int = 0           # 自愈成功次数
    total_duration: float = 0.0     # 总执行时间 (秒)

    # 详细数据
    test_cases: List[TestCaseDoc] = field(default_factory=list)
    test_results: List[TestCaseResult] = field(default_factory=list)
    bugs: List[BugReport] = field(default_factory=list)

    # 输出文件
    output_dir: str = ""
    testcases_file: str = ""        # testcases.md
    report_html: str = ""           # report.html
    report_xml: str = ""            # results.xml
    bug_report_file: str = ""       # bug_report.json
    business_report: str = ""       # business_report.html (业务级报告)

    @property
    def pass_rate(self) -> float:
        """通过率"""
        if self.total_cases == 0:
            return 0.0
        return self.passed / self.total_cases * 100

    @property
    def success(self) -> bool:
        """是否全部通过"""
        return self.failed == 0

    def get_summary(self) -> Dict[str, Any]:
        """获取摘要信息"""
        return {
            "project_name": self.project_name,
            "generated_at": self.generated_at,
            "total_cases": self.total_cases,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": f"{self.pass_rate:.1f}%",
            "bugs_found": self.bugs_found,
            "healed_count": self.healed_count,
            "total_duration": f"{self.total_duration:.2f}s"
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.get_summary(),
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "test_results": [tr.to_dict() for tr in self.test_results],
            "bugs": [b.to_dict() for b in self.bugs],
            "output_files": {
                "testcases_file": self.testcases_file,
                "report_html": self.report_html,
                "report_xml": self.report_xml,
                "bug_report_file": self.bug_report_file,
                "business_report": self.business_report
            }
        }

    def to_json(self) -> str:
        """导出为JSON字符串"""
        import json
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
