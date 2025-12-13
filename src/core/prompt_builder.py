"""
PromptBuilder - Prompt 构建器

负责读取模板并填充动态变量，生成最终的 Prompt。
"""

import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from collections import defaultdict

from ..models import TaskContext, TestMode, ErrorInfo
from .data_loader import DataLoader

logger = logging.getLogger(__name__)

# 模板目录
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# 统一工具权限
STANDARD_TOOLS = ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
EDIT_TOOLS = ["Read", "Edit"]  # 用于自愈阶段，只需要读取和编辑


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
        """构建规划阶段 Prompt (Phase 1)

        根据测试模式自动选择:
        - INTERFACE: 使用 plan_prompt.txt (接口测试)
        - BUSINESS/COMPLETE: 使用 business_plan_prompt.txt (业务测试)
        """
        # 业务测试模式使用专用 Prompt
        if context.test_mode in (TestMode.BUSINESS, TestMode.COMPLETE):
            return self._build_business_plan_prompt(context)

        # 接口测试模式使用原有 Prompt
        return self._build_interface_plan_prompt(context)

    def _build_interface_plan_prompt(self, context: TaskContext) -> PromptPackage:
        """构建接口测试模式 Prompt (原有逻辑)"""
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

        analysis_block = ""
        exploration_block = ""
        if getattr(context, "dependency_analysis", None):
            analysis_block = context.dependency_analysis.to_prompt_block()
        if getattr(context, "exploration_data", None):
            exploration_block = context.exploration_data.to_prompt_block()

        format_args = {
            "requirements_section": requirements_section,
            "swagger_content": context.swagger.raw_content,
            "requirements_content": requirements_content,
            "data_content": data_content,
            "output_dir": context.output_dir,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode_note": mode_note,
            "base_url": context.config.base_url,
            "auth_token": context.config.auth_token or "",
            "dependency_analysis_block": analysis_block or "（本地依赖分析结果为空）",
            "exploration_block": exploration_block or "（未启用或未获取到探测数据）"
        }

        prompt = template.format_map(defaultdict(str, format_args))

        extra_blocks = []
        analysis = getattr(context, "dependency_analysis", None)
        if analysis:
            extra_blocks.append("## 预计算依赖分析\n" + analysis.to_prompt_block())

        exploration = getattr(context, "exploration_data", None)
        if exploration:
            extra_blocks.append("## 探测数据\n" + exploration.to_prompt_block())

        if extra_blocks:
            prompt = f"{prompt}\n\n" + "\n\n".join(extra_blocks)

        return PromptPackage(
            prompt=prompt,
            allowed_tools=STANDARD_TOOLS,
            phase="planning"
        )

    def _build_business_plan_prompt(self, context: TaskContext) -> PromptPackage:
        """构建业务测试模式 Prompt (BUSINESS / COMPLETE)

        从 PRD 文档识别业务场景和规则，匹配测试数据。
        """
        template = self._load_template("business_plan_prompt")

        # 获取 PRD 内容
        prd_content = context.prd_document or context.requirements or ""
        if not prd_content:
            logger.warning("业务测试模式但未提供 PRD 文档，回退到接口测试模式")
            return self._build_interface_plan_prompt(context)

        # 测试数据部分
        test_data_section = ""
        test_data_summary = "无测试数据"

        if context.test_data_files:
            try:
                test_data = DataLoader.load_multiple(context.test_data_files)
                test_data_summary = DataLoader.summarize_for_prompt(test_data)
                test_data_section = f"\n### 测试数据\n{test_data_summary}"
            except Exception as e:
                logger.warning(f"加载测试数据失败: {e}")
                test_data_section = f"\n### 测试数据\n加载失败: {e}"

        # 数据匹配部分
        data_mapping_section = """## 3.1 测试数据智能匹配

如有上传测试数据，请执行以下匹配:

1. **列名匹配**: 将测试数据的列名与 Swagger 接口参数进行匹配
2. **数据集命名匹配**: 检查 Sheet 名或文件名是否包含接口相关关键词
3. **输出匹配结果**:

```json
{
  "data_mapping": {
    "POST /users/register": {
      "dataset": "用户注册",
      "columns": ["username", "email", "phone"],
      "row_count": 12,
      "match_score": 0.85
    }
  }
}
```

如无测试数据上传，跳过此步骤。"""

        if not context.test_data_files:
            data_mapping_section = "无测试数据上传，跳过数据匹配步骤。"

        format_args = {
            "prd_content": prd_content[:15000],  # 限制 PRD 长度
            "swagger_content": context.swagger.raw_content,
            "test_data_section": test_data_section,
            "base_url": context.config.base_url,
            "auth_token": context.config.auth_token or "",
            "output_dir": context.output_dir,
            "test_mode": context.test_mode.value,
            "data_mapping_section": data_mapping_section
        }

        prompt = template.format_map(defaultdict(str, format_args))

        return PromptPackage(
            prompt=prompt,
            allowed_tools=STANDARD_TOOLS,
            phase="planning_business"
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

        analysis_block = ""
        exploration_block = ""
        explicit_deps_block = ""

        if getattr(context, "dependency_analysis", None):
            # 生成阶段不限制依赖数量，显示完整依赖
            analysis_block = context.dependency_analysis.to_prompt_block(limit=20)

            # 提取高置信度依赖，生成强制实现清单
            high_confidence_deps = [
                dep for dep in context.dependency_analysis.dependencies
                if dep.confidence in ("最高", "高")
            ]
            if high_confidence_deps:
                explicit_deps_block = "### 必须实现的显式依赖\n\n"
                for i, dep in enumerate(high_confidence_deps, 1):
                    consumer = f"{dep.consumer.method} {dep.consumer.path}"
                    producers = ", ".join([f"{p.method} {p.path}" for p in dep.producers])
                    explicit_deps_block += f"{i}. **{consumer}** 需要先调用: {producers}\n"
                    explicit_deps_block += f"   - 字段: {dep.field.name}\n"
                    explicit_deps_block += f"   - 置信度: {dep.confidence}\n\n"
            else:
                explicit_deps_block = "（无高置信度显式依赖）"
        else:
            explicit_deps_block = "（本地依赖分析结果为空）"

        if getattr(context, "exploration_data", None):
            exploration_block = context.exploration_data.to_prompt_block(limit=10)

        format_args = {
            "testcases_file": testcases_file,
            "swagger_content": context.swagger.raw_content,
            "requirements_content": requirements_content,
            "data_content": data_content,
            "base_url": context.config.base_url,
            "auth_token": context.config.auth_token or "",
            "timeout": context.config.timeout,
            "output_dir": context.output_dir,
            "dependency_analysis_block": analysis_block or "（本地依赖分析结果为空）",
            "exploration_block": exploration_block or "（未启用或未获取到探测数据）",
            "explicit_dependencies_block": explicit_deps_block
        }

        prompt = template.format_map(defaultdict(str, format_args))

        extra_blocks = []
        analysis = getattr(context, "dependency_analysis", None)
        if analysis:
            extra_blocks.append("## 预计算依赖分析\n" + analysis.to_prompt_block(limit=20))

        exploration = getattr(context, "exploration_data", None)
        if exploration:
            extra_blocks.append("## 探测数据\n" + exploration.to_prompt_block(limit=10))

        if extra_blocks:
            prompt = f"{prompt}\n\n" + "\n\n".join(extra_blocks)

        return PromptPackage(
            prompt=prompt,
            allowed_tools=STANDARD_TOOLS,
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
            allowed_tools=EDIT_TOOLS,
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
            allowed_tools=EDIT_TOOLS,
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
            allowed_tools=STANDARD_TOOLS,
            phase="finalization"
        )


# 便捷函数
def create_prompt_builder(templates_dir: Optional[str] = None) -> PromptBuilder:
    """创建 PromptBuilder 的便捷函数"""
    path = Path(templates_dir) if templates_dir else None
    return PromptBuilder(path)
