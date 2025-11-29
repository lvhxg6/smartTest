"""
PytestRunner - Pytest 执行器

负责:
- 通过 subprocess 调用 pytest
- 解析 JUnit XML 结果
- 提取测试用例 ID (从 # TestCase: TC-XXX 注释)
- 返回结构化的测试结果
"""

import subprocess
import xml.etree.ElementTree as ET
import re
import logging
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple, Callable

from ..models import (
    PytestResult, TestCaseResult, TestStatus,
    ErrorInfo, ErrorType
)

logger = logging.getLogger(__name__)


@dataclass
class PytestConfig:
    """Pytest 配置"""
    timeout: int = 120                  # 单个测试用例超时 (秒)
    junit_xml: str = "results.xml"      # JUnit XML 输出文件名
    html_report: str = "report.html"    # HTML 报告文件名
    verbose: bool = True                # 详细输出
    capture: str = "no"                 # 不捕获输出 (-s)
    # 日志回调
    on_output: Optional[Callable[[str], None]] = None


class PytestRunner:
    """Pytest 执行器

    通过 subprocess 调用 pytest 并解析结果
    """

    def __init__(self, config: Optional[PytestConfig] = None):
        self.config = config or PytestConfig()
        # 用例 ID 正则
        self._testcase_pattern = re.compile(r'#\s*TestCase:\s*(TC-\d+)')

    def run(
        self,
        test_dir: str,
        output_dir: str,
        test_file: Optional[str] = None
    ) -> PytestResult:
        """执行 pytest

        Args:
            test_dir: 测试文件目录
            output_dir: 输出目录 (存放报告)
            test_file: 指定测试文件 (可选，不指定则运行整个目录)

        Returns:
            PytestResult 包含执行结果
        """
        test_path = Path(test_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 构建命令
        cmd = self._build_command(test_path, output_path, test_file)
        logger.info(f"Running pytest: {' '.join(cmd)}")

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout * 100,  # 整体超时
                cwd=str(test_path.parent)
            )

            duration = time.time() - start_time

            # 回调输出
            if self.config.on_output:
                self.config.on_output(result.stdout)
                if result.stderr:
                    self.config.on_output(result.stderr)

            # 解析结果 - JUnit XML 路径相对于 cwd
            junit_path = test_path.parent / output_path.name / self.config.junit_xml
            test_results = self._parse_junit_xml(junit_path, test_path)

            # 统计
            passed = sum(1 for r in test_results if r.status == TestStatus.PASS)
            failed = sum(1 for r in test_results if r.status == TestStatus.FAIL)
            errors = sum(1 for r in test_results if r.status == TestStatus.ERROR)
            skipped = sum(1 for r in test_results if r.status == TestStatus.SKIP)

            return PytestResult(
                exit_code=result.returncode,
                total=len(test_results),
                passed=passed,
                failed=failed,
                errors=errors,
                skipped=skipped,
                duration=duration,
                test_results=test_results,
                stdout=result.stdout,
                stderr=result.stderr
            )

        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            logger.error(f"Pytest execution timed out after {duration:.1f}s")
            return PytestResult(
                exit_code=-1,
                duration=duration,
                stdout="",
                stderr=f"Timeout after {self.config.timeout * 100}s"
            )

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Pytest execution failed: {e}")
            return PytestResult(
                exit_code=-1,
                duration=duration,
                stdout="",
                stderr=str(e)
            )

    def run_single_test(
        self,
        test_file: str,
        function_name: str,
        output_dir: str
    ) -> TestCaseResult:
        """执行单个测试函数

        Args:
            test_file: 测试文件路径
            function_name: 测试函数名
            output_dir: 输出目录

        Returns:
            TestCaseResult 单个用例结果
        """
        test_path = Path(test_file)
        output_path = Path(output_dir)

        # pytest path/to/test.py::ClassName::test_function
        # 或 pytest path/to/test.py::test_function
        test_spec = f"{test_file}::{function_name}"

        cmd = [
            "pytest",
            test_spec,
            f"--timeout={self.config.timeout}",
            f"--junitxml={output_path / self.config.junit_xml}",
            "-v"
        ]

        logger.info(f"Running single test: {function_name}")

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout + 10,
                cwd=str(test_path.parent)
            )

            duration = time.time() - start_time

            # 提取用例 ID
            testcase_id = self._extract_testcase_id(test_path, function_name)

            # 判断状态
            if result.returncode == 0:
                status = TestStatus.PASS
                error_info = None
            else:
                status, error_info = self._parse_failure(
                    result.stdout + result.stderr,
                    str(test_file),
                    function_name,
                    testcase_id
                )

            return TestCaseResult(
                testcase_id=testcase_id or "UNKNOWN",
                function_name=function_name,
                file_path=str(test_file),
                status=status,
                duration=duration,
                error_info=error_info
            )

        except subprocess.TimeoutExpired:
            testcase_id = self._extract_testcase_id(test_path, function_name)
            return TestCaseResult(
                testcase_id=testcase_id or "UNKNOWN",
                function_name=function_name,
                file_path=str(test_file),
                status=TestStatus.TIMEOUT,
                duration=self.config.timeout,
                error_info=ErrorInfo(
                    error_type=ErrorType.TIMEOUT,
                    file=str(test_file),
                    function=function_name,
                    message=f"Timeout after {self.config.timeout}s"
                )
            )

    def _build_command(
        self,
        test_path: Path,
        output_path: Path,
        test_file: Optional[str] = None
    ) -> List[str]:
        """构建 pytest 命令"""
        cmd = ["pytest"]

        # 测试目标 - 使用相对于 cwd (test_path.parent) 的路径
        if test_file:
            cmd.append(f"{test_path.name}/{test_file}")
        else:
            cmd.append(test_path.name)  # 只用目录名 "tests"

        # JUnit XML 报告 - 使用相对于 cwd (test_path.parent) 的路径
        cmd.append(f"--junitxml={output_path.name}/{self.config.junit_xml}")

        # HTML 报告
        cmd.append(f"--html={output_path.name}/{self.config.html_report}")
        cmd.append("--self-contained-html")

        # 超时
        cmd.append(f"--timeout={self.config.timeout}")

        # 详细输出
        if self.config.verbose:
            cmd.append("-v")

        # 捕获设置
        if self.config.capture == "no":
            cmd.append("-s")

        return cmd

    def _parse_junit_xml(
        self,
        xml_path: Path,
        test_dir: Path
    ) -> List[TestCaseResult]:
        """解析 JUnit XML 结果"""
        results = []

        if not xml_path.exists():
            logger.warning(f"JUnit XML not found: {xml_path}")
            return results

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            for testcase in root.iter('testcase'):
                name = testcase.get('name', '')
                classname = testcase.get('classname', '')
                time_str = testcase.get('time', '0')

                # 提取文件名
                file_path = self._classname_to_filepath(classname, test_dir)

                # 提取用例 ID
                testcase_id = self._extract_testcase_id(
                    Path(file_path) if file_path else test_dir,
                    name
                )

                # 判断状态
                failure = testcase.find('failure')
                error = testcase.find('error')
                skipped = testcase.find('skipped')

                if failure is not None:
                    status = TestStatus.FAIL
                    error_info = self._parse_xml_failure(failure, file_path or "", name, testcase_id)
                elif error is not None:
                    status = TestStatus.ERROR
                    error_info = self._parse_xml_error(error, file_path or "", name, testcase_id)
                elif skipped is not None:
                    status = TestStatus.SKIP
                    error_info = None
                else:
                    status = TestStatus.PASS
                    error_info = None

                results.append(TestCaseResult(
                    testcase_id=testcase_id or "UNKNOWN",
                    function_name=name,
                    file_path=file_path or classname,
                    status=status,
                    duration=float(time_str),
                    error_info=error_info
                ))

        except ET.ParseError as e:
            logger.error(f"Failed to parse JUnit XML: {e}")

        return results

    def _classname_to_filepath(self, classname: str, test_dir: Path) -> Optional[str]:
        """将 classname 转换为文件路径"""
        # classname 格式: tests.test_order_api.TestOrderAPI
        parts = classname.split('.')

        # 尝试找到测试文件
        for i in range(len(parts)):
            potential_file = '/'.join(parts[:i+1]) + '.py'
            full_path = test_dir / potential_file
            if full_path.exists():
                return str(full_path)

        return None

    def _extract_testcase_id(
        self,
        file_path: Path,
        function_name: str
    ) -> Optional[str]:
        """从测试文件中提取用例 ID"""
        if not file_path.exists():
            return None

        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # 找到函数定义行
            func_pattern = re.compile(rf'def\s+{re.escape(function_name)}\s*\(')

            for i, line in enumerate(lines):
                if func_pattern.search(line):
                    # 向上查找 # TestCase: TC-XXX 注释
                    for j in range(i - 1, max(i - 5, -1), -1):
                        match = self._testcase_pattern.search(lines[j])
                        if match:
                            return match.group(1)
                    break

        except Exception as e:
            logger.warning(f"Failed to extract testcase ID: {e}")

        return None

    def _parse_failure(
        self,
        output: str,
        file_path: str,
        function_name: str,
        testcase_id: Optional[str]
    ) -> Tuple[TestStatus, Optional[ErrorInfo]]:
        """解析失败输出"""
        # 判断错误类型
        if "AssertionError" in output:
            error_type = ErrorType.ASSERTION
            status = TestStatus.FAIL
        elif "SyntaxError" in output or "NameError" in output or "ImportError" in output:
            error_type = ErrorType.SYNTAX
            status = TestStatus.ERROR
        elif "ConnectionError" in output or "Timeout" in output:
            error_type = ErrorType.CONNECTION
            status = TestStatus.ERROR
        else:
            error_type = ErrorType.UNKNOWN
            status = TestStatus.ERROR

        # 提取行号
        line_match = re.search(rf'{re.escape(file_path)}:(\d+)', output)
        line = int(line_match.group(1)) if line_match else None

        # 提取错误消息
        error_lines = [l for l in output.split('\n') if 'Error' in l or 'assert' in l.lower()]
        message = error_lines[0] if error_lines else "Unknown error"

        error_info = ErrorInfo(
            error_type=error_type,
            file=file_path,
            function=function_name,
            testcase_id=testcase_id,
            line=line,
            message=message,
            traceback=output
        )

        # 如果是断言失败，尝试提取期望值和实际值
        if error_type == ErrorType.ASSERTION:
            self._extract_assertion_details(output, error_info)

        return status, error_info

    def _extract_assertion_details(self, output: str, error_info: ErrorInfo) -> None:
        """提取断言详情"""
        # 匹配 assert xxx == yyy 类型
        assert_match = re.search(r'assert\s+(.+?)\s*==\s*(.+)', output)
        if assert_match:
            error_info.assertion = f"assert {assert_match.group(1)} == {assert_match.group(2)}"

        # 尝试提取期望值和实际值
        expected_match = re.search(r'expected[:\s]+([^\n]+)', output, re.IGNORECASE)
        actual_match = re.search(r'actual[:\s]+([^\n]+)', output, re.IGNORECASE)

        if expected_match:
            error_info.expected = expected_match.group(1).strip()
        if actual_match:
            error_info.actual = actual_match.group(1).strip()

    def _parse_xml_failure(
        self,
        failure_elem: ET.Element,
        file_path: str,
        function_name: str,
        testcase_id: Optional[str]
    ) -> ErrorInfo:
        """解析 XML 中的 failure 元素"""
        message = failure_elem.get('message', '')
        traceback = failure_elem.text or ''

        return ErrorInfo(
            error_type=ErrorType.ASSERTION,
            file=file_path,
            function=function_name,
            testcase_id=testcase_id,
            message=message,
            traceback=traceback
        )

    def _parse_xml_error(
        self,
        error_elem: ET.Element,
        file_path: str,
        function_name: str,
        testcase_id: Optional[str]
    ) -> ErrorInfo:
        """解析 XML 中的 error 元素"""
        message = error_elem.get('message', '')
        traceback = error_elem.text or ''

        # 判断错误类型
        if 'SyntaxError' in message or 'NameError' in message:
            error_type = ErrorType.SYNTAX
        elif 'Connection' in message or 'Timeout' in message:
            error_type = ErrorType.CONNECTION
        else:
            error_type = ErrorType.UNKNOWN

        return ErrorInfo(
            error_type=error_type,
            file=file_path,
            function=function_name,
            testcase_id=testcase_id,
            message=message,
            traceback=traceback
        )


# 便捷函数
def run_pytest(
    test_dir: str,
    output_dir: str,
    timeout: int = 120
) -> PytestResult:
    """运行 pytest 的便捷函数"""
    config = PytestConfig(timeout=timeout)
    runner = PytestRunner(config)
    return runner.run(test_dir, output_dir)
