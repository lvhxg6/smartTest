"""
DependencyExplorer - 轻量级依赖探测器

基于静态依赖分析结果，尝试调用无依赖或低依赖的接口，提取可用的 ID。
默认不启用，需在 WorkflowConfig.enable_exploration 打开。
"""

import logging
import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path

import requests

from ..models import TaskContext
from ..models.dependency import DependencyAnalysisResult, EndpointRef

logger = logging.getLogger(__name__)


@dataclass
class ExplorationStep:
    step: int
    endpoint: str
    method: str
    url: str
    status: Optional[int] = None
    success: bool = False
    message: str = ""
    extracted: Dict[str, List[Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step": self.step,
            "endpoint": self.endpoint,
            "method": self.method,
            "url": self.url,
            "status": self.status,
            "success": self.success,
            "message": self.message,
            "extracted": self.extracted
        }


@dataclass
class ExplorationResult:
    steps: List[ExplorationStep] = field(default_factory=list)
    extracted_values: Dict[str, List[Any]] = field(default_factory=dict)
    overall_success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_success": self.overall_success,
            "steps": [s.to_dict() for s in self.steps],
            "extracted_values": self.extracted_values
        }

    def save(self, output_dir: str) -> Dict[str, str]:
        paths = {}
        log_path = f"{output_dir}/exploration_log.json"
        data_path = f"{output_dir}/explored_data.json"
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(self.extracted_values, f, ensure_ascii=False, indent=2)
        paths["log"] = log_path
        paths["data"] = data_path
        return paths

    def to_prompt_block(self, limit: int = 5) -> str:
        lines = [f"- 探测步骤: {len(self.steps)}, 提取字段: {len(self.extracted_values)}"]
        for step in self.steps[:limit]:
            status = step.status or "N/A"
            ok = "✓" if step.success else "✗"
            lines.append(f"- {ok} {step.method} {step.endpoint} ({status}) {step.message}")
        if self.extracted_values:
            items = list(self.extracted_values.items())[:limit]
            lines.append("### 已提取ID示例")
            for k, vals in items:
                preview = ", ".join(map(str, vals[:3]))
                lines.append(f"- {k}: {preview}")
        return "\n".join(lines)


class DependencyExplorer:
    """简单的依赖探测"""

    def __init__(self, timeout: int = 5, max_endpoints: int = 10):
        self.timeout = timeout
        self.max_endpoints = max_endpoints

    def explore(self, context: TaskContext, analysis: DependencyAnalysisResult) -> ExplorationResult:
        """
        仅对无路径参数的 GET 接口做轻量探测，尝试提取 ID。
        更复杂的创建/更新不自动执行，避免破坏性操作。
        """
        result = ExplorationResult()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if context.config.auth_token:
            headers["Authorization"] = context.config.auth_token
        headers.update(context.config.extra_headers or {})

        step_idx = 1
        for res in list(analysis.resources.values())[: self.max_endpoints]:
            get_candidates = [
                ep for ep in res.endpoints
                if ep.method == "GET" and "{" not in ep.path
            ]
            if not get_candidates:
                continue

            ep = get_candidates[0]
            url = self._build_url(context.config.base_url, ep.path)
            step = ExplorationStep(
                step=step_idx,
                endpoint=ep.path,
                method=ep.method,
                url=url
            )
            step_idx += 1

            try:
                resp = requests.get(url, headers=headers, timeout=self.timeout, verify=False)
                step.status = resp.status_code

                if resp.status_code == 200:
                    payload = self._safe_json(resp)
                    extracted = self._extract_ids(payload)
                    step.extracted = extracted
                    step.success = True
                    step.message = f"提取 {sum(len(v) for v in extracted.values())} 个字段值"
                    self._merge_extracted(result.extracted_values, extracted)
                else:
                    step.success = False
                    step.message = f"状态码 {resp.status_code}"
            except Exception as exc:
                step.success = False
                step.message = f"请求失败: {exc}"

            result.steps.append(step)

        result.overall_success = any(s.success for s in result.steps)
        return result

    def _build_url(self, base_url: str, path: str) -> str:
        return f"{base_url.rstrip('/')}/{path.lstrip('/')}"

    def _safe_json(self, resp) -> Any:
        try:
            return resp.json()
        except Exception:
            return {}

    def _extract_ids(self, payload: Any) -> Dict[str, List[Any]]:
        """从响应体中粗略提取 id-like 字段值"""
        collected: Dict[str, List[Any]] = {}

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if "id" in k.lower() and v not in (None, "", []):
                        collected.setdefault(k, []).append(v)
                    walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    walk(item)

        walk(payload)
        return collected

    def _merge_extracted(self, target: Dict[str, List[Any]], new: Dict[str, List[Any]]) -> None:
        for k, vals in new.items():
            if k not in target:
                target[k] = []
            for v in vals:
                if v not in target[k]:
                    target[k].append(v)
