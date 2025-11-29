"""
PromptBuilder - Prompt 构建器

负责读取模板并填充动态变量，生成最终的 Prompt。
"""

import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..models import TaskContext, TestMode, ErrorInfo

logger = logging.getLogger(__name__)

# 模板目录
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


@dataclass
class PromptPackage:
    """Prompt 包 - 包含完整的 CLI 调用参数"""
    prompt: str                                    # 主 Prompt 内容
    allowed_tools: List[str] = field(default_factory=list)  # 允许的工具
    phase: str = ""                                # 当前阶段名称


class PromptBuilder:
    """Prompt 构建器

    读取模板文件并填充动态变量
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self._templates_cache: Dict[str, str] = {}

    def _load_template(self, name: str) -> str:
        """加载模板文件"""
        if name in self._templates_cache:
            return self._templates_cache[name]

        template_path = self.templates_dir / f"{name}.txt"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        content = template_path.read_text(encoding='utf-8')
        self._templates_cache[name] = content
        return content

    def build_plan_prompt(self, context: TaskContext) -> PromptPackage:
        """构建规划阶段 Prompt (Phase 1)"""
        template = self._load_template("plan_prompt")

        # 根据模式决定内容
        is_complete = context.test_mode == TestMode.COMPLETE

        requirements_section = "和业务规则" if is_complete else ""
        requirements_content = ""
        if is_complete and context.requirements:
            requirements_content = f"\n## 业务规则\n{context.requirements}"

        data_content = ""
        if context.has_data_assets:
            data_content = f"\n## 业务数据\n{context.data_assets}"

        mode_note = ""
        if not is_complete:
            mode_note = "\n\n注意: 当前为轻量模式，无业务规则，仅基于Swagger进行契约测试。"

        prompt = template.format(
            requirements_section=requirements_section,
            swagger_content=context.swagger.raw_content,
            requirements_content=requirements_content,
            data_content=data_content,
            output_dir=context.output_dir,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            mode_note=mode_note
        )

        return PromptPackage(
            prompt=prompt,
            allowed_tools=["Read", "Write"],
            phase="planning"
        )

    def build_generate_prompt(self, context: TaskContext) -> PromptPackage:
        """构建生成阶段 Prompt (Phase 2)"""
        template = self._load_template("generate_prompt")

        testcases_file = f"{context.output_dir}/testcases.md"

        requirements_content = ""
        if context.test_mode == TestMode.COMPLETE and context.requirements:
            requirements_content = f"\n## 业务规则\n{context.requirements}"

        data_content = ""
        if context.has_data_assets:
            data_content = f"\n## 业务数据\n{context.data_assets}"

        prompt = template.format(
            testcases_file=testcases_file,
            swagger_content=context.swagger.raw_content,
            requirements_content=requirements_content,
            data_content=data_content,
            base_url=context.config.base_url,
            auth_token=context.config.auth_token or "",
            timeout=context.config.timeout,
            output_dir=context.output_dir
        )

        return PromptPackage(
            prompt=prompt,
            allowed_tools=["Read", "Write"],
            phase="generation"
        )

    def build_heal_syntax_prompt(self, error_info: ErrorInfo) -> PromptPackage:
        """构建语法自愈 Prompt (Phase 3 - Syntax)"""
        template = self._load_template("heal_syntax_prompt")

        prompt = template.format(
            error_type=error_info.error_type.value,
            file_path=error_info.file,
            function_name=error_info.function,
            line_number=error_info.line or "未知",
            testcase_id=error_info.testcase_id or "未知",
            error_message=error_info.message,
            traceback=error_info.traceback
        )

        return PromptPackage(
            prompt=prompt,
            allowed_tools=["Read", "Edit"],
            phase="healing_syntax"
        )

    def build_heal_logic_prompt(
        self,
        error_info: ErrorInfo,
        requirements: Optional[str] = None
    ) -> PromptPackage:
        """构建逻辑自愈 Prompt (Phase 3 - Logic)"""
        template = self._load_template("heal_logic_prompt")

        # 构建 API 描述
        api = f"{error_info.function} in {error_info.file}"

        # 响应体
        response_body = "无"
        if error_info.response_body:
            import json
            response_body = json.dumps(error_info.response_body, indent=2, ensure_ascii=False)

        requirements_section = ""
        if requirements:
            requirements_section = f"\n## 业务规则\n{requirements}"

        prompt = template.format(
            testcase_id=error_info.testcase_id or "未知",
            file_path=error_info.file,
            function_name=error_info.function,
            assertion=error_info.assertion or "未知",
            expected=error_info.expected or "未知",
            actual=error_info.actual or "未知",
            response_body=response_body,
            api=api,
            requirements_section=requirements_section
        )

        return PromptPackage(
            prompt=prompt,
            allowed_tools=["Read", "Edit"],
            phase="healing_logic"
        )

    def build_finalize_prompt(
        self,
        context: TaskContext,
        stats: Dict[str, Any],
        bugs: List[Dict[str, Any]]
    ) -> PromptPackage:
        """构建交付阶段 Prompt (Phase 4)"""
        template = self._load_template("finalize_prompt")

        # 构建 Bug 列表
        bug_list = "无" if not bugs else ""
        for i, bug in enumerate(bugs, 1):
            bug_list += f"\n{i}. [{bug.get('severity', 'MEDIUM')}] {bug.get('testcase_id')}: {bug.get('scenario')}"

        prompt = template.format(
            total_cases=stats.get('total', 0),
            passed=stats.get('passed', 0),
            failed=stats.get('failed', 0),
            pass_rate=stats.get('pass_rate', 0),
            duration=stats.get('duration', 0),
            bug_list=bug_list,
            bugs_count=len(bugs),
            testcases_file=f"{context.output_dir}/testcases.md",
            output_dir=context.output_dir
        )

        return PromptPackage(
            prompt=prompt,
            allowed_tools=["Read", "Write"],
            phase="finalization"
        )


# 便捷函数
def create_prompt_builder(templates_dir: Optional[str] = None) -> PromptBuilder:
    """创建 PromptBuilder 的便捷函数"""
    path = Path(templates_dir) if templates_dir else None
    return PromptBuilder(path)
