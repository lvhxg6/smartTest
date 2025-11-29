"""
Result Models - 执行结果模型

包含:
- CLIResult: Claude CLI 调用结果
- PytestResult: Pytest 执行结果
- TestCaseResult: 单个测试用例结果
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class TestStatus(Enum):
    """测试状态"""
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    TIMEOUT = "timeout"
    SKIP = "skip"


class ErrorType(Enum):
    """错误类型"""
    SYNTAX = "syntax"          # 语法错误 (SyntaxError, NameError, etc.)
    ASSERTION = "assertion"    # 断言失败 (AssertionError)
    CONNECTION = "connection"  # 连接错误
    TIMEOUT = "timeout"        # 超时
    UNKNOWN = "unknown"        # 未知错误


class HealingType(Enum):
    """自愈类型"""
    SYNTAX = "syntax"   # 语法自愈: 修复代码错误
    LOGIC = "logic"     # 逻辑自愈: 判断是脚本问题还是真Bug


@dataclass
class CLIResult:
    """Claude CLI 执行结果"""
    success: bool
    output: Optional[str] = None
    parsed_output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    exit_code: int = 0
    execution_time: float = 0.0
    session_id: Optional[str] = None
    cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "session_id": self.session_id,
            "cost_usd": self.cost_usd
        }


@dataclass
class ErrorInfo:
    """错误信息 (Driver -> CLI 传递格式)"""
    error_type: ErrorType
    file: str
    function: str
    testcase_id: Optional[str] = None
    line: Optional[int] = None
    message: str = ""
    traceback: str = ""
    # 断言失败时的额外信息
    assertion: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None
    response_body: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "error_type": self.error_type.value,
            "file": self.file,
            "function": self.function,
            "testcase_id": self.testcase_id,
            "line": self.line,
            "message": self.message,
            "traceback": self.traceback
        }
        if self.error_type == ErrorType.ASSERTION:
            result.update({
                "assertion": self.assertion,
                "expected": self.expected,
                "actual": self.actual,
                "response_body": self.response_body
            })
        return result


@dataclass
class TestCaseResult:
    """单个测试用例结果"""
    testcase_id: str                # TC-XXX
    function_name: str              # test_xxx
    file_path: str                  # test_order_api.py
    status: TestStatus              # PASS / FAIL / ERROR / TIMEOUT
    duration: float = 0.0           # 执行时间 (秒)
    error_info: Optional[ErrorInfo] = None
    healing_attempts: int = 0       # 自愈尝试次数
    healed: bool = False            # 是否自愈成功

    @property
    def passed(self) -> bool:
        return self.status == TestStatus.PASS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "testcase_id": self.testcase_id,
            "function_name": self.function_name,
            "file_path": self.file_path,
            "status": self.status.value,
            "duration": self.duration,
            "error_info": self.error_info.to_dict() if self.error_info else None,
            "healing_attempts": self.healing_attempts,
            "healed": self.healed
        }


@dataclass
class PytestResult:
    """Pytest 执行结果"""
    exit_code: int                  # pytest 退出码
    total: int = 0                  # 总用例数
    passed: int = 0                 # 通过数
    failed: int = 0                 # 失败数
    errors: int = 0                 # 错误数
    skipped: int = 0                # 跳过数
    duration: float = 0.0           # 总执行时间
    test_results: List[TestCaseResult] = field(default_factory=list)
    stdout: str = ""                # 标准输出
    stderr: str = ""                # 标准错误

    @property
    def success(self) -> bool:
        """是否全部通过"""
        return self.exit_code == 0 and self.failed == 0 and self.errors == 0

    @property
    def pass_rate(self) -> float:
        """通过率"""
        if self.total == 0:
            return 0.0
        return self.passed / self.total * 100

    def get_failed_results(self) -> List[TestCaseResult]:
        """获取失败的用例结果"""
        return [r for r in self.test_results if not r.passed]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "errors": self.errors,
            "skipped": self.skipped,
            "duration": self.duration,
            "pass_rate": self.pass_rate,
            "test_results": [r.to_dict() for r in self.test_results]
        }


@dataclass
class JudgeResult:
    """结果仲裁判定"""
    verdict: TestStatus             # 判定结果
    need_healing: bool              # 是否需要自愈
    healing_type: Optional[HealingType] = None  # 自愈类型
    is_bug: bool = False            # 是否为真Bug (逻辑自愈判定)
    error_detail: str = ""          # 错误详情

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict.value,
            "need_healing": self.need_healing,
            "healing_type": self.healing_type.value if self.healing_type else None,
            "is_bug": self.is_bug,
            "error_detail": self.error_detail
        }
