"""
TaskContext - 任务上下文模型

存储整个测试任务的输入和状态信息
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class TestMode(Enum):
    """测试模式"""
    COMPLETE = "complete"  # 完整模式: 有业务规则
    LIGHT = "light"        # 轻量模式: 仅Swagger


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
    - 输入数据: Swagger、业务规则、配置、测试数据
    - 运行时状态: 测试模式、Session ID、输出目录
    """
    # 必填输入
    swagger: SwaggerSpec
    config: EnvConfig

    # 可选输入 (原文传递)
    requirements: Optional[str] = None  # 业务规则原文
    data_assets: Optional[str] = None   # 业务数据原文

    # 运行时状态
    session_id: Optional[str] = None    # CLI Session ID
    output_dir: str = "./output"        # 输出目录
    dependency_analysis: Optional[Any] = None  # 静态依赖分析结果
    exploration_data: Optional[Any] = None     # 探测数据

    # 自动计算
    @property
    def test_mode(self) -> TestMode:
        """根据是否有业务规则判断测试模式"""
        if self.requirements and self.requirements.strip():
            return TestMode.COMPLETE
        return TestMode.LIGHT

    @property
    def has_data_assets(self) -> bool:
        """是否有业务数据"""
        return bool(self.data_assets and self.data_assets.strip())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "swagger_title": self.swagger.title,
            "swagger_endpoints": self.swagger.endpoint_count,
            "config": self.config.to_dict(),
            "has_requirements": self.requirements is not None,
            "has_data_assets": self.has_data_assets,
            "test_mode": self.test_mode.value,
            "session_id": self.session_id,
            "output_dir": self.output_dir
        }
