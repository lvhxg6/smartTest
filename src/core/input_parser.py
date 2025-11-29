"""
InputParser - 输入解析器

负责解析和验证用户输入:
- Swagger/OpenAPI 文件解析
- 环境配置解析
- 业务规则读取
- 测试数据资产读取
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

from ..models import TaskContext, EnvConfig, SwaggerSpec

logger = logging.getLogger(__name__)


class InputParseError(Exception):
    """输入解析错误"""
    pass


class InputParser:
    """输入解析器

    将用户提供的各种输入统一解析为 TaskContext
    """

    def parse(
        self,
        swagger_input: Union[str, Path, Dict],
        base_url: str,
        auth_token: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        requirements_input: Optional[Union[str, Path]] = None,
        data_assets_input: Optional[Union[str, Path]] = None,
        output_dir: str = "./output"
    ) -> TaskContext:
        """解析所有输入，构建 TaskContext

        Args:
            swagger_input: Swagger 文件路径、URL 或已解析的 dict
            base_url: API 基础 URL
            auth_token: 认证 Token (可选)
            extra_headers: 额外请求头 (可选)
            requirements_input: 业务规则文件路径或内容 (可选)
            data_assets_input: 测试数据文件路径或内容 (可选)
            output_dir: 输出目录

        Returns:
            TaskContext 实例
        """
        # 解析 Swagger
        swagger = self._parse_swagger(swagger_input)

        # 构建环境配置
        config = EnvConfig(
            base_url=base_url.rstrip("/"),
            auth_token=auth_token,
            extra_headers=extra_headers or {}
        )

        # 读取业务规则 (可选)
        requirements = None
        if requirements_input:
            requirements = self._read_text_input(requirements_input, "requirements")

        # 读取测试数据 (可选)
        data_assets = None
        if data_assets_input:
            data_assets = self._read_text_input(data_assets_input, "data_assets")

        return TaskContext(
            swagger=swagger,
            config=config,
            requirements=requirements,
            data_assets=data_assets,
            output_dir=output_dir
        )

    def _parse_swagger(self, input_source: Union[str, Path, Dict]) -> SwaggerSpec:
        """解析 Swagger/OpenAPI 规范

        支持:
        - 文件路径 (JSON/YAML)
        - JSON 字符串
        - 已解析的 dict
        """
        raw_content: str
        spec_dict: Dict[str, Any]

        if isinstance(input_source, dict):
            # 已经是解析后的 dict
            spec_dict = input_source
            raw_content = json.dumps(input_source, ensure_ascii=False)

        elif isinstance(input_source, Path) or (
            isinstance(input_source, str) and
            (input_source.endswith('.json') or input_source.endswith('.yaml') or input_source.endswith('.yml'))
        ):
            # 文件路径
            path = Path(input_source)
            if not path.exists():
                raise InputParseError(f"Swagger file not found: {path}")

            raw_content = path.read_text(encoding='utf-8')
            spec_dict = self._parse_spec_content(raw_content, path.suffix)

        else:
            # 假设是 JSON 字符串
            raw_content = input_source
            try:
                spec_dict = json.loads(input_source)
            except json.JSONDecodeError as e:
                raise InputParseError(f"Invalid JSON content: {e}")

        # 提取关键信息
        return self._build_swagger_spec(raw_content, spec_dict)

    def _parse_spec_content(self, content: str, suffix: str) -> Dict[str, Any]:
        """根据文件类型解析内容"""
        if suffix in ['.yaml', '.yml']:
            try:
                import yaml
                return yaml.safe_load(content)
            except ImportError:
                raise InputParseError("PyYAML not installed. Run: pip install pyyaml")
            except yaml.YAMLError as e:
                raise InputParseError(f"Invalid YAML content: {e}")
        else:
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise InputParseError(f"Invalid JSON content: {e}")

    def _build_swagger_spec(self, raw_content: str, spec_dict: Dict) -> SwaggerSpec:
        """从 OpenAPI/Swagger dict 构建 SwaggerSpec"""

        # 判断版本 (OpenAPI 3.x vs Swagger 2.x)
        is_openapi3 = spec_dict.get('openapi', '').startswith('3.')

        # 提取基本信息
        info = spec_dict.get('info', {})
        title = info.get('title', 'API')
        version = info.get('version', '1.0')

        # 提取基础路径
        if is_openapi3:
            servers = spec_dict.get('servers', [])
            base_path = servers[0].get('url', '') if servers else ''
        else:
            base_path = spec_dict.get('basePath', '')

        # 提取端点列表
        endpoints = self._extract_endpoints(spec_dict, is_openapi3)

        logger.info(
            f"Parsed Swagger: {title} v{version}, "
            f"{len(endpoints)} endpoints"
        )

        return SwaggerSpec(
            raw_content=raw_content,
            title=title,
            version=version,
            base_path=base_path,
            endpoints=endpoints
        )

    def _extract_endpoints(self, spec_dict: Dict, is_openapi3: bool) -> list:
        """提取所有 API 端点"""
        endpoints = []
        paths = spec_dict.get('paths', {})

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue

            for method, details in methods.items():
                # 跳过非 HTTP 方法的键 (如 parameters, summary 等)
                if method.lower() not in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                    continue

                if not isinstance(details, dict):
                    continue

                endpoint = {
                    'path': path,
                    'method': method.upper(),
                    'operationId': details.get('operationId', f"{method}_{path}"),
                    'summary': details.get('summary', ''),
                    'description': details.get('description', ''),
                    'tags': details.get('tags', []),
                    'parameters': details.get('parameters', []),
                }

                # 请求体 (OpenAPI 3.x vs Swagger 2.x)
                if is_openapi3:
                    request_body = details.get('requestBody', {})
                    if request_body:
                        endpoint['requestBody'] = request_body
                else:
                    # Swagger 2.x 在 parameters 里有 body 类型
                    body_params = [
                        p for p in details.get('parameters', [])
                        if isinstance(p, dict) and p.get('in') == 'body'
                    ]
                    if body_params:
                        endpoint['requestBody'] = body_params[0]

                # 响应定义
                endpoint['responses'] = details.get('responses', {})

                endpoints.append(endpoint)

        return endpoints

    def _read_text_input(
        self,
        input_source: Union[str, Path],
        input_name: str
    ) -> str:
        """读取文本输入 (文件路径或直接内容)"""

        # 尝试作为文件路径处理
        if isinstance(input_source, Path):
            path = input_source
        elif isinstance(input_source, str):
            # 检查是否像文件路径
            if len(input_source) < 500 and (
                input_source.endswith('.md') or
                input_source.endswith('.txt') or
                input_source.endswith('.json') or
                '/' in input_source or
                '\\' in input_source
            ):
                path = Path(input_source)
                if path.exists():
                    logger.info(f"Reading {input_name} from file: {path}")
                    return path.read_text(encoding='utf-8')

            # 不是文件，返回原内容
            return input_source
        else:
            raise InputParseError(f"Invalid {input_name} input type: {type(input_source)}")

        if not path.exists():
            raise InputParseError(f"{input_name} file not found: {path}")

        return path.read_text(encoding='utf-8')


# 便捷函数
def parse_inputs(
    swagger_path: str,
    base_url: str,
    auth_token: Optional[str] = None,
    requirements_path: Optional[str] = None,
    data_assets_path: Optional[str] = None,
    output_dir: str = "./output"
) -> TaskContext:
    """解析输入的便捷函数"""
    parser = InputParser()
    return parser.parse(
        swagger_input=swagger_path,
        base_url=base_url,
        auth_token=auth_token,
        requirements_input=requirements_path,
        data_assets_input=data_assets_path,
        output_dir=output_dir
    )
