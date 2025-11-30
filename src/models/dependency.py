"""
依赖分析模型

用于描述接口资源、字段及依赖关系，便于在 Prompt 和报告中复用。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json


ID_HINTS = ("id", "pk", "key", "code", "uuid", "no", "num")


def _is_id_like(name: str) -> bool:
    """判断字段名是否可能是 ID/主键"""
    lname = name.lower()
    return any(hint in lname for hint in ID_HINTS)


def _normalize_id(name: str) -> str:
    """简单归一化 ID 字段名"""
    lname = name.replace("_", "")
    for prefix in ("pk", "id", "uuid"):
        if lname.lower().startswith(prefix):
            lname = lname[len(prefix) :]
    # 保留末尾 id
    if not lname.lower().endswith("id"):
        lname = lname + "Id"
    return lname[0].lower() + lname[1:]


@dataclass
class FieldRef:
    """接口字段引用"""
    name: str
    location: str               # path/query/body
    required: bool = False
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "location": self.location,
            "required": self.required,
            "description": self.description
        }

    @property
    def normalized_id(self) -> Optional[str]:
        if _is_id_like(self.name):
            return _normalize_id(self.name)
        return None


@dataclass
class EndpointRef:
    """接口引用"""
    path: str
    method: str
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method,
            "summary": self.summary
        }


@dataclass
class ResourceInfo:
    """资源信息"""
    name: str
    primary_keys: List[str] = field(default_factory=list)
    endpoints: List[EndpointRef] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "primary_keys": self.primary_keys,
            "endpoints": [e.to_dict() for e in self.endpoints]
        }


@dataclass
class DependencyLink:
    """依赖关系"""
    consumer: EndpointRef                   # 依赖者
    field: FieldRef                         # 依赖字段
    producers: List[EndpointRef] = field(default_factory=list)  # 可能提供者
    normalized_id: Optional[str] = None
    confidence: str = "中"
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "consumer": self.consumer.to_dict(),
            "field": self.field.to_dict(),
            "producers": [p.to_dict() for p in self.producers],
            "normalized_id": self.normalized_id,
            "confidence": self.confidence,
            "reason": self.reason
        }


@dataclass
class DependencyAnalysisResult:
    """依赖分析结果"""
    resources: Dict[str, ResourceInfo] = field(default_factory=dict)
    dependencies: List[DependencyLink] = field(default_factory=list)
    sorted_endpoints: List[Dict[str, Any]] = field(default_factory=list)  # 拓扑排序后的接口列表
    generated_by: str = "static-analyzer"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_by": self.generated_by,
            "resource_count": len(self.resources),
            "dependency_count": len(self.dependencies),
            "endpoint_count": len(self.sorted_endpoints),
            "resources": {k: v.to_dict() for k, v in self.resources.items()},
            "dependencies": [d.to_dict() for d in self.dependencies],
            "sorted_endpoints": self.sorted_endpoints
        }

    def save(self, output_dir: str) -> str:
        """保存为 JSON 文件"""
        path = f"{output_dir}/dependency_analysis.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return path

    def to_prompt_block(self, limit: int = 8) -> str:
        """生成适用于 Prompt 的简要 Markdown 段落"""
        lines = []
        lines.append(f"- 资源数: {len(self.resources)}, 依赖数: {len(self.dependencies)}, 接口数: {len(self.sorted_endpoints)}")

        # 显示拓扑排序后的接口清单
        if self.sorted_endpoints:
            lines.append("### 接口清单（按依赖顺序）")
            for i, ep in enumerate(self.sorted_endpoints[:limit], 1):
                method = ep.get("method", "")
                path = ep.get("path", "")
                summary = ep.get("summary", "")
                lines.append(f"{i}. {method} {path} - {summary}")
            if len(self.sorted_endpoints) > limit:
                lines.append(f"   ... 共 {len(self.sorted_endpoints)} 个接口")

        if self.resources:
            lines.append("### 资源与主键")
            for name, res in list(self.resources.items())[:limit]:
                pk = ", ".join(res.primary_keys) if res.primary_keys else "未知"
                lines.append(f"- {name}: 主键 {pk}")

        if self.dependencies:
            lines.append("### 依赖示例")
            for dep in self.dependencies[:limit]:
                pid = dep.normalized_id or dep.field.name
                consumer = f"{dep.consumer.method} {dep.consumer.path}"
                producers = ", ".join({f"{p.method} {p.path}" for p in dep.producers}) or "未知"
                lines.append(f"- {consumer} 依赖 {pid} ← {producers} ({dep.confidence})")

        return "\n".join(lines)
