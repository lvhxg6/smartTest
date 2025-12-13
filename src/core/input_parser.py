"""
InputParser - 输入解析器

负责解析和验证用户输入:
- Swagger/OpenAPI 文件解析
- 环境配置解析
- PRD 文档解析 (MD/DOCX/TXT)
- 测试数据文件解析 (Excel/CSV)
- 业务规则读取 (兼容旧版)
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union, List

from ..models import TaskContext, EnvConfig, SwaggerSpec
from .prd_parser import PRDParser
from .data_loader import DataLoader

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
        prd_input: Optional[Union[str, Path]] = None,
        test_data_inputs: Optional[List[Union[str, Path]]] = None,
        output_dir: str = "./output"
    ) -> TaskContext:
        """解析所有输入，构建 TaskContext

        测试模式根据输入自动判断:
        - 仅 Swagger → INTERFACE (接口测试)
        - Swagger + PRD → BUSINESS (业务测试，自动生成数据)
        - Swagger + PRD + 测试数据 → COMPLETE (完整测试)

        Args:
            swagger_input: Swagger 文件路径、URL 或已解析的 dict
            base_url: API 基础 URL
            auth_token: 认证 Token (可选)
            extra_headers: 额外请求头 (可选)
            requirements_input: 业务规则文件路径或内容 (可选，兼容旧版)
            data_assets_input: 测试数据文件路径或内容 (可选，兼容旧版)
            prd_input: PRD 文档路径 (可选，支持 .md/.docx/.txt)
            test_data_inputs: 测试数据文件路径列表 (可选，支持 .xlsx/.csv)
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

        # 读取业务规则 (兼容旧版)
        requirements = None
        if requirements_input:
            requirements = self._read_text_input(requirements_input, "requirements")

        # 读取旧版测试数据 (兼容旧版)
        data_assets = None
        if data_assets_input:
            data_assets = self._read_text_input(data_assets_input, "data_assets")

        # 解析 PRD 文档 (新版)
        prd_document = None
        if prd_input:
            prd_document = self._parse_prd(prd_input)

        # 解析测试数据文件 (新版)
        test_data_files: List[str] = []
        if test_data_inputs:
            test_data_files = self._parse_test_data_files(test_data_inputs)

        return TaskContext(
            swagger=swagger,
            config=config,
            requirements=requirements,
            data_assets=data_assets,
            prd_document=prd_document,
            test_data_files=test_data_files,
            output_dir=output_dir
        )

    def _parse_prd(self, prd_input: Union[str, Path]) -> Optional[str]:
        """解析 PRD 文档

        支持格式: .md, .docx, .txt

        Args:
            prd_input: PRD 文件路径或直接内容

        Returns:
            解析后的 PRD 文本内容
        """
        # 如果是路径，使用 PRDParser 解析
        if isinstance(prd_input, Path):
            path = prd_input
        elif isinstance(prd_input, str):
            # 检查是否是文件路径
            if PRDParser.is_supported(prd_input):
                path = Path(prd_input)
                if path.exists():
                    logger.info(f"解析 PRD 文档: {path}")
                    return PRDParser.parse(str(path))

            # 检查是否可能是文件路径 (带路径分隔符)
            if len(prd_input) < 500 and ('/' in prd_input or '\\' in prd_input):
                path = Path(prd_input)
                if path.exists() and PRDParser.is_supported(str(path)):
                    logger.info(f"解析 PRD 文档: {path}")
                    return PRDParser.parse(str(path))

            # 假设是直接的文本内容
            logger.info("PRD 输入作为直接文本内容处理")
            return prd_input

        if not path.exists():
            raise InputParseError(f"PRD 文档不存在: {path}")

        return PRDParser.parse(str(path))

    def _parse_test_data_files(
        self,
        test_data_inputs: List[Union[str, Path]]
    ) -> List[str]:
        """解析测试数据文件列表

        验证文件存在并返回规范化的路径列表。

        Args:
            test_data_inputs: 测试数据文件路径列表

        Returns:
            验证后的文件路径字符串列表
        """
        valid_files = []

        for input_item in test_data_inputs:
            path = Path(input_item) if isinstance(input_item, str) else input_item

            if not path.exists():
                logger.warning(f"测试数据文件不存在，跳过: {path}")
                continue

            ext = path.suffix.lower()
            if ext not in ('.xlsx', '.csv'):
                logger.warning(f"不支持的测试数据格式 {ext}，跳过: {path}")
                continue

            # 验证文件可读
            try:
                DataLoader.load(str(path))
                valid_files.append(str(path.resolve()))
                logger.info(f"验证测试数据文件: {path}")
            except Exception as e:
                logger.warning(f"测试数据文件无法解析，跳过: {path} - {e}")

        return valid_files

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
    prd_path: Optional[str] = None,
    test_data_paths: Optional[List[str]] = None,
    output_dir: str = "./output"
) -> TaskContext:
    """解析输入的便捷函数

    根据提供的文件自动判断测试模式:
    - 仅 Swagger → INTERFACE (接口测试)
    - Swagger + PRD → BUSINESS (业务测试)
    - Swagger + PRD + 测试数据 → COMPLETE (完整测试)

    Args:
        swagger_path: Swagger 文件路径
        base_url: API 基础 URL
        auth_token: 认证 Token (可选)
        requirements_path: 业务规则文件路径 (可选，兼容旧版)
        data_assets_path: 测试数据文件路径 (可选，兼容旧版)
        prd_path: PRD 文档路径 (可选，支持 .md/.docx/.txt)
        test_data_paths: 测试数据文件路径列表 (可选，支持 .xlsx/.csv)
        output_dir: 输出目录

    Returns:
        TaskContext 实例
    """
    parser = InputParser()
    return parser.parse(
        swagger_input=swagger_path,
        base_url=base_url,
        auth_token=auth_token,
        requirements_input=requirements_path,
        data_assets_input=data_assets_path,
        prd_input=prd_path,
        test_data_inputs=test_data_paths,
        output_dir=output_dir
    )
