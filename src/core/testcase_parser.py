"""
TestCase Parser - 测试用例解析器

解析 testcases.md 文件，建立 testcase_id → 用例信息 的映射。
用于在执行阶段丰富日志输出和关联测试结果。
"""

import re
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ParsedTestCase:
    """解析后的测试用例信息"""
    testcase_id: str       # TC-001
    api: str               # GET /v1/config-templates
    scenario: str          # 正常分页-默认参数
    priority: str          # P0
    test_data: str         # page=1, perPage=10
    expected_result: str   # 200, 返回分页列表


class TestCaseParser:
    """测试用例文档解析器"""

    # 匹配 API 节标题，支持多种格式:
    # - ### API-01: GET /v1/config-templates (旧格式)
    # - ### API-001 GET /v3/config-templates 描述 (新格式)
    API_HEADER_PATTERN = re.compile(
        r'^###\s+(?:API-\d+[:\s]+)?(\w+)\s+(/\S+)',
        re.MULTILINE
    )

    # 匹配测试用例表格行，支持多种用例 ID 格式:
    # - TC-001 (旧格式)
    # - API-001-01, SCN-001, RULE-001-01, DATA-001-01 (新格式)
    TESTCASE_ROW_PATTERN = re.compile(
        r'^\|\s*((?:TC|API|SCN|RULE|DATA)-[\d-]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|',
        re.MULTILINE
    )

    def parse(self, testcases_path: str) -> Dict[str, ParsedTestCase]:
        """解析 testcases.md 文件

        Args:
            testcases_path: testcases.md 文件路径

        Returns:
            Dict[str, ParsedTestCase]: testcase_id → ParsedTestCase 映射
        """
        path = Path(testcases_path)
        if not path.exists():
            logger.warning(f"testcases.md not found: {testcases_path}")
            return {}

        content = path.read_text(encoding='utf-8')
        return self._parse_content(content)

    def _parse_content(self, content: str) -> Dict[str, ParsedTestCase]:
        """解析 markdown 内容"""
        result: Dict[str, ParsedTestCase] = {}

        # 按 API 节分割
        sections = self._split_by_api_sections(content)

        for api_method, api_path, section_content in sections:
            api = f"{api_method} {api_path}"
            testcases = self._parse_testcase_table(section_content, api)
            result.update(testcases)

        logger.info(f"Parsed {len(result)} test cases from testcases.md")
        return result

    def _split_by_api_sections(self, content: str):
        """按 API 节分割内容

        Yields:
            (method, path, section_content)
        """
        # 找到所有 API 标题位置
        matches = list(self.API_HEADER_PATTERN.finditer(content))

        for i, match in enumerate(matches):
            method = match.group(1)
            path = match.group(2)

            # 确定节的内容范围
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_content = content[start:end]

            yield method, path, section_content

    def _parse_testcase_table(self, section_content: str, api: str) -> Dict[str, ParsedTestCase]:
        """解析测试用例表格

        支持多种表格格式：
        - | TC-001 | 场景 | P0 | 测试数据 | 预期结果 |
        - | API-001-01 | 场景 | 参数 | 预期结果 |
        - | RULE-001-01 | 场景 | 输入 | 预期结果 |
        """
        result: Dict[str, ParsedTestCase] = {}

        for match in self.TESTCASE_ROW_PATTERN.finditer(section_content):
            testcase_id = match.group(1).strip()
            # 第2列通常是场景/名称
            scenario = match.group(2).strip()
            # 第3列可能是优先级或参数
            col3 = match.group(3).strip()
            # 第4列通常是测试数据或预期结果
            col4 = match.group(4).strip()

            # 判断第3列是优先级还是参数
            # 优先级格式: P0, P1, P2, P3
            if col3 in ('P0', 'P1', 'P2', 'P3'):
                priority = col3
                test_data = col4
                expected_result = ""  # 4列格式时预期结果在第4列
            else:
                # 非优先级格式，第3列是参数，第4列是预期结果
                priority = "P1"  # 默认优先级
                test_data = col3
                expected_result = col4

            result[testcase_id] = ParsedTestCase(
                testcase_id=testcase_id,
                api=api,
                scenario=scenario,
                priority=priority,
                test_data=test_data,
                expected_result=expected_result
            )

        return result

    def get_label(self, testcase_id: str, testcase_map: Dict[str, ParsedTestCase]) -> str:
        """获取测试用例的展示标签

        Args:
            testcase_id: 用例 ID (如 TC-001)
            testcase_map: 解析后的用例映射

        Returns:
            格式化的标签，如 "TC-001 [GET /config-templates - 正常分页]"
        """
        tc = testcase_map.get(testcase_id)
        if tc:
            # 截断过长的 API 路径
            api_short = tc.api if len(tc.api) <= 30 else tc.api[:27] + "..."
            # 截断过长的场景描述
            scenario_short = tc.scenario if len(tc.scenario) <= 20 else tc.scenario[:17] + "..."
            return f"{testcase_id} [{api_short} - {scenario_short}]"
        return testcase_id
