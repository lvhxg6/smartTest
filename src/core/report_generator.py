"""
Report Generator - 业务级测试报告生成器

生成直观的业务报告，展示：
- 测试结果概览
- 每个测试用例的场景、预期结果、实际结果
- 失败用例的详细信息
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..models import FinalReport, TestCaseDoc, TestCaseResult, TestStatus

logger = logging.getLogger(__name__)


class BusinessReportGenerator:
    """业务级测试报告生成器"""

    def generate(self, report: FinalReport, output_path: str) -> str:
        """生成业务级 HTML 报告

        Args:
            report: FinalReport 对象
            output_path: 输出目录路径

        Returns:
            生成的报告文件路径
        """
        html = self._render_html(report)

        # 保存到 reports 目录
        reports_dir = Path(output_path) / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_file = reports_dir / "business_report.html"
        report_file.write_text(html, encoding='utf-8')

        logger.info(f"Business report generated: {report_file}")
        return str(report_file)

    def _render_html(self, report: FinalReport) -> str:
        """渲染 HTML 报告"""
        # 构建结果映射
        result_map: Dict[str, TestCaseResult] = {
            r.testcase_id: r for r in report.test_results if r.testcase_id
        }

        # 按状态分组测试用例
        passed_cases: List[TestCaseDoc] = []
        failed_cases: List[TestCaseDoc] = []

        for tc in report.test_cases:
            if tc.status == TestStatus.PASS:
                passed_cases.append(tc)
            else:
                failed_cases.append(tc)

        # 生成用例列表 HTML
        testcases_html = self._render_testcases(report.test_cases, result_map)

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告 - {report.project_name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid #2d2d44;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 28px;
            color: #00d4ff;
            margin-bottom: 10px;
        }}
        .header .meta {{
            color: #888;
            font-size: 14px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .summary-card .value {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .summary-card .label {{
            color: #888;
            font-size: 14px;
        }}
        .summary-card.total .value {{ color: #00d4ff; }}
        .summary-card.passed .value {{ color: #00ff88; }}
        .summary-card.failed .value {{ color: #ff4757; }}
        .summary-card.rate .value {{ color: #ffd93d; }}
        .section {{
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .section-header {{
            background: rgba(255,255,255,0.05);
            padding: 15px 20px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        .section-header .count {{
            background: rgba(255,255,255,0.1);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
        }}
        .testcase {{
            padding: 15px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            transition: background 0.2s;
        }}
        .testcase:hover {{
            background: rgba(255,255,255,0.03);
        }}
        .testcase:last-child {{
            border-bottom: none;
        }}
        .testcase-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
        }}
        .status-icon {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }}
        .status-icon.pass {{
            background: rgba(0, 255, 136, 0.2);
            color: #00ff88;
        }}
        .status-icon.fail {{
            background: rgba(255, 71, 87, 0.2);
            color: #ff4757;
        }}
        .testcase-id {{
            font-family: monospace;
            font-weight: 600;
            color: #00d4ff;
        }}
        .testcase-api {{
            font-family: monospace;
            font-size: 13px;
            color: #888;
            background: rgba(255,255,255,0.05);
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .testcase-scenario {{
            color: #e0e0e0;
            font-weight: 500;
        }}
        .testcase-details {{
            margin-top: 10px;
            padding: 12px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            font-size: 13px;
        }}
        .testcase-details .row {{
            display: flex;
            margin-bottom: 6px;
        }}
        .testcase-details .row:last-child {{
            margin-bottom: 0;
        }}
        .testcase-details .label {{
            color: #888;
            width: 80px;
            flex-shrink: 0;
        }}
        .testcase-details .value {{
            color: #e0e0e0;
            word-break: break-all;
        }}
        .testcase-details .value.expected {{
            color: #00ff88;
        }}
        .testcase-details .value.actual {{
            color: #ff4757;
        }}
        .footer {{
            text-align: center;
            padding: 30px 0;
            color: #666;
            font-size: 13px;
        }}
        .toggle-btn {{
            background: rgba(255,255,255,0.1);
            border: none;
            color: #888;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }}
        .toggle-btn:hover {{
            background: rgba(255,255,255,0.15);
            color: #e0e0e0;
        }}
        .collapsed .testcase {{
            display: none;
        }}
        .collapsed .testcase:nth-child(-n+5) {{
            display: block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{report.project_name} - 测试报告</h1>
            <div class="meta">
                生成时间: {report.execution_time} |
                执行耗时: {report.total_duration:.2f}s
            </div>
        </div>

        <div class="summary">
            <div class="summary-card total">
                <div class="value">{report.total_cases}</div>
                <div class="label">总用例数</div>
            </div>
            <div class="summary-card passed">
                <div class="value">{report.passed}</div>
                <div class="label">通过</div>
            </div>
            <div class="summary-card failed">
                <div class="value">{report.failed}</div>
                <div class="label">失败</div>
            </div>
            <div class="summary-card rate">
                <div class="value">{report.pass_rate:.1f}%</div>
                <div class="label">通过率</div>
            </div>
        </div>

        {testcases_html}

        <div class="footer">
            Powered by Smart Dev Mantis
        </div>
    </div>

    <script>
        function toggleSection(id) {{
            const section = document.getElementById(id);
            section.classList.toggle('collapsed');
            const btn = section.querySelector('.toggle-btn');
            if (section.classList.contains('collapsed')) {{
                btn.textContent = '展开全部';
            }} else {{
                btn.textContent = '收起';
            }}
        }}
    </script>
</body>
</html>"""

    def _render_testcases(
        self,
        testcases: List[TestCaseDoc],
        result_map: Dict[str, TestCaseResult]
    ) -> str:
        """渲染测试用例列表"""
        if not testcases:
            return '<div class="section"><div class="section-header">暂无测试用例数据</div></div>'

        # 分离通过和失败用例
        passed = [tc for tc in testcases if tc.status == TestStatus.PASS]
        failed = [tc for tc in testcases if tc.status != TestStatus.PASS and tc.status is not None]
        pending = [tc for tc in testcases if tc.status is None]

        html_parts = []

        # 失败用例（优先展示）
        if failed:
            html_parts.append(self._render_section(
                "failed-section",
                "失败用例",
                failed,
                result_map,
                collapsed=False
            ))

        # 通过用例
        if passed:
            html_parts.append(self._render_section(
                "passed-section",
                "通过用例",
                passed,
                result_map,
                collapsed=len(passed) > 10
            ))

        # 未执行用例
        if pending:
            html_parts.append(self._render_section(
                "pending-section",
                "未执行",
                pending,
                result_map,
                collapsed=True
            ))

        return '\n'.join(html_parts)

    def _render_section(
        self,
        section_id: str,
        title: str,
        testcases: List[TestCaseDoc],
        result_map: Dict[str, TestCaseResult],
        collapsed: bool = False
    ) -> str:
        """渲染测试用例区块"""
        collapsed_class = 'collapsed' if collapsed else ''
        toggle_text = '展开全部' if collapsed else '收起'

        cases_html = '\n'.join(
            self._render_testcase(tc, result_map.get(tc.testcase_id))
            for tc in testcases
        )

        return f"""
        <div id="{section_id}" class="section {collapsed_class}">
            <div class="section-header">
                <span>{title}</span>
                <span class="count">{len(testcases)}</span>
                {'<button class="toggle-btn" onclick="toggleSection(\'' + section_id + '\')">' + toggle_text + '</button>' if len(testcases) > 5 else ''}
            </div>
            {cases_html}
        </div>
        """

    def _render_testcase(
        self,
        tc: TestCaseDoc,
        result: Optional[TestCaseResult]
    ) -> str:
        """渲染单个测试用例"""
        is_pass = tc.status == TestStatus.PASS
        status_class = 'pass' if is_pass else 'fail'
        status_icon = '&#10003;' if is_pass else '&#10007;'

        # 详细信息（仅失败时显示）
        details_html = ''
        if not is_pass and tc.status is not None:
            actual_value = ''
            if result and result.error_info:
                actual_value = result.error_info.actual or result.error_info.message or ''

            details_html = f"""
            <div class="testcase-details">
                <div class="row">
                    <span class="label">预期结果:</span>
                    <span class="value expected">{tc.expected_result}</span>
                </div>
                <div class="row">
                    <span class="label">实际结果:</span>
                    <span class="value actual">{actual_value}</span>
                </div>
                {('<div class="row"><span class="label">测试数据:</span><span class="value">' + tc.test_data + '</span></div>') if tc.test_data else ''}
            </div>
            """

        return f"""
        <div class="testcase">
            <div class="testcase-header">
                <span class="status-icon {status_class}">{status_icon}</span>
                <span class="testcase-id">{tc.testcase_id}</span>
                <span class="testcase-api">{tc.api}</span>
                <span class="testcase-scenario">{tc.scenario}</span>
            </div>
            {details_html}
        </div>
        """
