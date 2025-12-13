"""
TaskContext - 任务上下文模型

存储整个测试任务的输入和状态信息
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class TestMode(Enum):
    """测试模式 - 根据上传文件组合自动判断"""
    INTERFACE = "interface"  # 接口测试模式: 仅 Swagger
    BUSINESS = "business"    # 业务测试模式: Swagger + PRD (自动生成数据)
    COMPLETE = "complete"    # 完整测试模式: Swagger + PRD + 测试数据

    # 兼容旧模式名称
    LIGHT = "interface"      # 别名，兼容旧代码


@dataclass
class EnvConfig:
    """环境配置"""
    base_url: str
    auth_token: Optional[str] = None
    extra_headers: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "auth_token": self.auth_token,
            "extra_headers": self.extra_headers,
            "timeout": self.timeout
        }


@dataclass
class SwaggerSpec:
    """解析后的Swagger规范"""
    raw_content: str              # 原始JSON内容
    title: str = ""               # API标题
    version: str = ""             # API版本
    base_path: str = ""           # 基础路径
    endpoints: List[Dict] = field(default_factory=list)  # 端点列表

    @property
    def endpoint_count(self) -> int:
        return len(self.endpoints)


@dataclass
class TaskContext:
    """
    任务上下文 - 贯穿整个测试流程的数据容器

    包含:
    - 输入数据: Swagger、PRD文档、配置、测试数据
    - 运行时状态: 测试模式、Session ID、输出目录
    - LLM分析结果: 场景、规则、数据映射
    """
    # 必填输入
    swagger: SwaggerSpec
    config: EnvConfig

    # 可选输入 (原文传递)
    requirements: Optional[str] = None  # 业务规则原文 (兼容旧字段)
    data_assets: Optional[str] = None   # 业务数据原文 (兼容旧字段)

    # 新增: PRD 和测试数据
    prd_document: Optional[str] = None       # PRD 文档内容 (MD/DOCX/TXT 解析后的文本)
    test_data_files: List[str] = field(default_factory=list)  # 测试数据文件路径列表

    # 运行时状态
    session_id: Optional[str] = None    # CLI Session ID
    output_dir: str = "./output"        # 输出目录
    dependency_analysis: Optional[Any] = None  # 静态依赖分析结果
    exploration_data: Optional[Any] = None     # 探测数据

    # LLM 分析结果 (Phase 1 智能分析后填充)
    scenarios: Optional[List[Dict[str, Any]]] = None      # 识别的业务场景
    business_rules: Optional[List[Dict[str, Any]]] = None # 提取的业务规则
    data_mapping: Optional[Dict[str, Any]] = None         # 测试数据与接口的映射关系

    # 自动计算
    @property
    def test_mode(self) -> TestMode:
        """
        根据上传文件组合自动判断测试模式:
        - 仅 Swagger → INTERFACE (接口测试)
        - Swagger + PRD → BUSINESS (业务测试, 自动生成数据)
        - Swagger + PRD + 测试数据 → COMPLETE (完整测试, 使用指定数据)
        """
        has_prd = bool(self.prd_document and self.prd_document.strip())
        has_test_data = bool(self.test_data_files)

        # 兼容旧逻辑: requirements 也视为 PRD
        if not has_prd and self.requirements and self.requirements.strip():
            has_prd = True

        if has_prd and has_test_data:
            return TestMode.COMPLETE
        elif has_prd:
            return TestMode.BUSINESS
        else:
            return TestMode.INTERFACE

    @property
    def has_prd(self) -> bool:
        """是否有 PRD 文档"""
        return bool(
            (self.prd_document and self.prd_document.strip()) or
            (self.requirements and self.requirements.strip())
        )

    @property
    def has_test_data(self) -> bool:
        """是否有测试数据文件"""
        return bool(self.test_data_files)

    @property
    def has_data_assets(self) -> bool:
        """是否有业务数据 (兼容旧属性)"""
        return bool(self.data_assets and self.data_assets.strip())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "swagger_title": self.swagger.title,
            "swagger_endpoints": self.swagger.endpoint_count,
            "config": self.config.to_dict(),
            "has_requirements": self.requirements is not None,
            "has_prd": self.has_prd,
            "has_test_data": self.has_test_data,
            "has_data_assets": self.has_data_assets,
            "test_mode": self.test_mode.value,
            "session_id": self.session_id,
            "output_dir": self.output_dir,
            "scenarios_count": len(self.scenarios) if self.scenarios else 0,
            "rules_count": len(self.business_rules) if self.business_rules else 0,
        }
