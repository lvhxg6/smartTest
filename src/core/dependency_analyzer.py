"""
DependencyAnalyzer - 静态依赖分析器

基于 Swagger 内容提取资源、主键、依赖字段，生成依赖图。
旨在提供可复用的分析结果给 Prompt 和代码生成阶段，减少对大模型"自觉执行"指令的依赖。
"""

import logging
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Tuple, Set

from pathlib import Path

from ..models import SwaggerSpec
from ..models.dependency import (
    ResourceInfo,
    DependencyAnalysisResult,
    FieldRef,
    EndpointRef,
    DependencyLink,
    _is_id_like,
    _normalize_id
)

logger = logging.getLogger(__name__)

# HTTP 方法优先级（用于同层级排序）
METHOD_PRIORITY = {
    'GET': 1,      # 查询无副作用，最先执行
    'POST': 2,     # 创建资源
    'PUT': 3,      # 更新资源
    'PATCH': 4,    # 部分更新
    'DELETE': 5,   # 删除最后执行
    'OPTIONS': 6,
    'HEAD': 7,
}


class DependencyAnalyzer:
    """静态依赖分析器"""

    def __init__(self, max_dependencies: int = 200):
        self.max_dependencies = max_dependencies

    def analyze(self, swagger: SwaggerSpec) -> DependencyAnalysisResult:
        """执行静态依赖分析"""
        resources: Dict[str, ResourceInfo] = {}
        dependencies: List[DependencyLink] = []

        for ep in swagger.endpoints:
            endpoint_ref = EndpointRef(
                path=ep.get("path", ""),
                method=ep.get("method", "").upper(),
                summary=ep.get("summary", "")
            )

            resource_name = self._infer_resource_name(endpoint_ref.path)
            if resource_name not in resources:
                resources[resource_name] = ResourceInfo(name=resource_name)
            resources[resource_name].endpoints.append(endpoint_ref)

            # 提取字段
            fields = self._extract_fields(ep)

            # 主键候选
            for f in fields:
                if f.location == "path" and _is_id_like(f.name):
                    norm = f.normalized_id or f.name
                    if norm not in resources[resource_name].primary_keys:
                        resources[resource_name].primary_keys.append(norm)

            # 依赖候选
            for f in fields:
                if not _is_id_like(f.name):
                    continue
                norm_id = f.normalized_id or f.name
                producers = self._find_producers(resources, norm_id)

                dependencies.append(
                    DependencyLink(
                        consumer=endpoint_ref,
                        field=f,
                        producers=producers,
                        normalized_id=norm_id,
                        confidence=self._confidence_for(f),
                        reason=self._reason_for(f, resource_name)
                    )
                )

                if len(dependencies) >= self.max_dependencies:
                    logger.warning("Dependency count hit max limit, truncating...")
                    break

        # 拓扑排序接口列表
        sorted_endpoints = self._topological_sort(swagger.endpoints, dependencies)

        result = DependencyAnalysisResult(
            resources=resources,
            dependencies=dependencies,
            sorted_endpoints=sorted_endpoints,
            generated_by="static-analyzer"
        )

        logger.info(
            f"Dependency analysis: resources={len(resources)}, dependencies={len(dependencies)}, sorted_endpoints={len(sorted_endpoints)}"
        )
        return result

    def _infer_resource_name(self, path: str) -> str:
        """根据路径推断资源名"""
        parts = [p for p in path.split("/") if p and not p.startswith("{")]
        if not parts:
            return "root"
        # 取最后一个非参数段作为资源名
        return parts[-1].replace("-", "_")

    def _extract_fields(self, ep: Dict[str, Any]) -> List[FieldRef]:
        """从 endpoint 定义中抽取字段"""
        fields: List[FieldRef] = []

        # parameters 数组
        for p in ep.get("parameters", []) or []:
            if not isinstance(p, dict):
                continue
            name = p.get("name", "")
            location = p.get("in", "query")
            required = bool(p.get("required", False))
            desc = p.get("description", "")
            fields.append(FieldRef(name=name, location=location, required=required, description=desc))

        # requestBody (OpenAPI3)
        rb = ep.get("requestBody")
        if isinstance(rb, dict):
            content = rb.get("content", {})
            for media in content.values():
                if not isinstance(media, dict):
                    continue
                schema = media.get("schema", {})
                fields.extend(self._extract_schema_fields(schema, location="body"))
                break  # 仅取第一个 content

        return fields

    def _extract_schema_fields(self, schema: Dict[str, Any], location: str) -> List[FieldRef]:
        """从 schema properties 提取字段"""
        fields: List[FieldRef] = []
        if not isinstance(schema, dict):
            return fields

        props = schema.get("properties", {})
        required_list = schema.get("required", []) or []

        for name, prop in props.items():
            desc = prop.get("description", "") if isinstance(prop, dict) else ""
            required = name in required_list
            fields.append(FieldRef(name=name, location=location, required=required, description=desc))

        return fields

    def _find_producers(self, resources: Dict[str, ResourceInfo], norm_id: str) -> List[EndpointRef]:
        """寻找可能生成该 ID 的接口"""
        producers: List[EndpointRef] = []
        for res in resources.values():
            if norm_id in res.primary_keys:
                for ep in res.endpoints:
                    if ep.method in ("POST", "PUT", "PATCH", "GET"):
                        producers.append(ep)
        return producers

    def _confidence_for(self, field: FieldRef) -> str:
        """根据字段位置简单评估置信度"""
        if field.location == "path":
            return "高"
        if field.required:
            return "中"
        return "低"

    def _reason_for(self, field: FieldRef, resource: str) -> str:
        """构造原因描述"""
        if field.location == "path":
            return f"路径参数，属于 {resource}"
        if field.required:
            return f"必填字段 {field.name}"
        return f"可选字段 {field.name}"

    def _topological_sort(
        self,
        endpoints: List[Dict[str, Any]],
        dependencies: List[DependencyLink]
    ) -> List[Dict[str, Any]]:
        """拓扑排序接口列表，确保生产者在消费者之前

        使用 Kahn 算法：
        1. 构建依赖图（邻接表）
        2. 找出所有入度为 0 的节点
        3. BFS 遍历，依次移除入度为 0 的节点
        4. 同层级按 HTTP 方法优先级排序
        """
        if not endpoints:
            return []

        # 构建依赖图
        graph, in_degree = self._build_dependency_graph(endpoints, dependencies)

        # 构建 endpoint key -> endpoint 的映射
        ep_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for ep in endpoints:
            key = (ep.get("path", ""), ep.get("method", "").upper())
            ep_map[key] = ep

        # 初始化队列（入度为 0 的节点）
        queue: List[Dict[str, Any]] = []
        for ep in endpoints:
            key = (ep.get("path", ""), ep.get("method", "").upper())
            if in_degree.get(key, 0) == 0:
                queue.append(ep)

        # 按 HTTP 方法优先级排序
        queue.sort(key=lambda x: METHOD_PRIORITY.get(x.get("method", "").upper(), 99))

        sorted_endpoints: List[Dict[str, Any]] = []
        visited: Set[Tuple[str, str]] = set()

        while queue:
            # 取出队首
            ep = queue.pop(0)
            key = (ep.get("path", ""), ep.get("method", "").upper())

            if key in visited:
                continue
            visited.add(key)
            sorted_endpoints.append(ep)

            # 更新邻居入度
            for neighbor_key in graph.get(key, []):
                if neighbor_key in visited:
                    continue
                in_degree[neighbor_key] -= 1
                if in_degree[neighbor_key] == 0:
                    neighbor_ep = ep_map.get(neighbor_key)
                    if neighbor_ep:
                        queue.append(neighbor_ep)

            # 保持队列按优先级排序
            queue.sort(key=lambda x: METHOD_PRIORITY.get(x.get("method", "").upper(), 99))

        # 处理未被排序的节点（可能存在循环依赖或孤立节点）
        if len(sorted_endpoints) < len(endpoints):
            remaining = [
                ep for ep in endpoints
                if (ep.get("path", ""), ep.get("method", "").upper()) not in visited
            ]
            if remaining:
                logger.warning(f"检测到 {len(remaining)} 个未排序节点（可能存在循环依赖），追加到末尾")
                # 按优先级排序后追加
                remaining.sort(key=lambda x: METHOD_PRIORITY.get(x.get("method", "").upper(), 99))
                sorted_endpoints.extend(remaining)

        return sorted_endpoints

    def _build_dependency_graph(
        self,
        endpoints: List[Dict[str, Any]],
        dependencies: List[DependencyLink]
    ) -> Tuple[Dict[Tuple[str, str], List[Tuple[str, str]]], Dict[Tuple[str, str], int]]:
        """构建依赖图

        Returns:
            graph: 邻接表，producer -> [consumers]
            in_degree: 每个节点的入度
        """
        graph: Dict[Tuple[str, str], List[Tuple[str, str]]] = defaultdict(list)
        in_degree: Dict[Tuple[str, str], int] = defaultdict(int)

        # 初始化所有节点入度为 0
        for ep in endpoints:
            key = (ep.get("path", ""), ep.get("method", "").upper())
            in_degree[key] = 0

        # 根据依赖关系构建边
        for dep in dependencies:
            consumer_key = (dep.consumer.path, dep.consumer.method.upper())

            for producer in dep.producers:
                producer_key = (producer.path, producer.method.upper())

                # 避免自依赖
                if producer_key == consumer_key:
                    continue

                # producer -> consumer（producer 必须在 consumer 之前）
                if consumer_key not in graph[producer_key]:
                    graph[producer_key].append(consumer_key)
                    in_degree[consumer_key] += 1

        return graph, in_degree


def load_dependency_analysis(path: str) -> Optional[DependencyAnalysisResult]:
    """读取已保存的依赖分析结果"""
    import json
    if not Path(path).exists():
        return None
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        # 轻量重建，仅用于 prompt 展示
        resources = {
            name: ResourceInfo(
                name=name,
                primary_keys=info.get("primary_keys", []),
                endpoints=[EndpointRef(**ep) for ep in info.get("endpoints", [])]
            )
            for name, info in data.get("resources", {}).items()
        }
        deps = [
            DependencyLink(
                consumer=EndpointRef(**d.get("consumer", {})),
                field=FieldRef(**d.get("field", {})),
                producers=[EndpointRef(**p) for p in d.get("producers", [])],
                normalized_id=d.get("normalized_id"),
                confidence=d.get("confidence", "中"),
                reason=d.get("reason", "")
            )
            for d in data.get("dependencies", [])
        ]
        return DependencyAnalysisResult(
            resources=resources,
            dependencies=deps,
            generated_by=data.get("generated_by", "static-analyzer")
        )
    except Exception as exc:
        logger.warning(f"Failed to load dependency analysis: {exc}")
        return None
