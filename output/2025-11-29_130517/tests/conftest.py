"""
BMS WebAPI 接口测试配置文件
基线管理系统 - 基线核查模板管理接口测试

生成时间: 2025-11-29 13:05:18
"""

import pytest
import requests
import urllib3
from typing import Generator

# 禁用SSL警告（测试环境使用自签名证书）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 环境配置
BASE_URL = "https://localhost:4089"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyZWFsTmFtZSI6ImM1NjBjNTVjZmViOGEzNTFkOGUwNjMzMjM1MmQ4NWQ4IiwiY2xpZW50SXAiOiIxOTIuMTY4LjE0LjEwMSIsInVzZXJQaG9uZSI6IjM5YTNhNDgyZmUwYzYyYjNiMThlNTQxNjdhNWZkNTAwIiwicmlnaHRDb2RlcyI6IkdaOn46eMOafVVbw5rDoyBcYsOdUMKeZlx1MDAwN1RJw4rDlMKIwp_Cl8Omw6_Dv8Oiw753MXjCiW3DknbCnsKCXHUwMDFDwoRcdTAwMDNcdTAwMDHCtFx1MDAxQ0lhXsOBw4LCgsOTw43DsmZQL0NcdTAwMDEhYMOMw7HDoXDCisK4Olx1MDAwM3FAXHUwMDExw4Jtwpc3w7bCt1xiXHUwMDE3woM5XFx5wpvDiMOlwqDDgMOmYjI5Vl3CgMKzX8OFw4bCoMKKXHJcdTAwMEXCjyAhRGdnWsK6w4HDojnCuS7Dj8OkcVx1MDAwM2PCmnXDk21cYjfCt8OpwqbCqsKEXHUwMDAywprCuUliw5rCrS4gWsKyw5jDjcO2PMOYwqHCl8OvU3Enw5zDusKVTsKzczLCvExcdTAwMDFVw7JcdTAwMTRcdTAwMUbDmcKxIcO1wphcdTAwMDbDt1NZw57DtMOFayXCk1x1MDAwMsO6w51KwpMwVFx1MDAwNsOBSn41ZcKbXHUwMDA1McKPwoDCr8O5acKCQ8K-PMOPNcKRQ8OeR8OoU8KZdsOsWMKIZGkmw5R5ZUvCkcO9wp5scsKLXHUwMDA3LVx1MDAxNMORXHUwMDE5fnTDgn5aUcOIwozCk2bClVbCtMKjUMKgdcK-csKIXHUwMDAybMOWMMOowpHDv0TCq2NcdTAwMUZcdTAwMULDmkpObMKzR8OFXktMwqtywohcdTAwMTBTaHLDv8O9PThZw4HCpHTDvcK4w6dxUsKfXHUwMDE4J8KnS8OcfsOyKMK2PsOuw4fDk8KBw53CuGVPXjVGwqBxwpJcdTAwMTbDiHtuT1x1MDAwQsKDccOMXGIswpPDs3zCpVx1MDAwQsOFw5rDvcOtf0thwpogw6XCi01cdTAwMTJGYsOvw6TDmlZKUHXDnVXClVxyK8Opwo0rw5jCpSvCvsOWwrTCoCNMwo7DnMOnwqVHWcO5LsOtw6B5fVVHXHUwMDBGNsOMXCLCsF_DgMOSb8O9XHUwMDFCXHLCukBUw5dcdTAwMUHDvcO1wpzDrFnDs8OKwrVpIMOFK3vDusOFPcO0wp1vOMK0byE-XHUwMDE1wqBSfFbCq1x1MDAxRMKfNWvDp1x1MDAxRcOZwrMswppiWsKFalTCpVx1MDAwRVx1MDAwN8O9NsKUwppXwpBcdDMkPVx1MDAxOMOSw6XDtUjCjsOsw4xNw4ZcdTAwMUbDhyHDuXLDjcKJesOJQW94eVfCi287wq18IVx0aiXClcOgUMOJLMKpwpZpXHUwMDA3wqRccsOeMWUkw6s2dsOSLFFcdTAwMTZFXHUwMDE5wobCg03DvsKze8KQwqVcdTAwMDBWwpVcdTAwMTXDsMOuwqjDjFxmSllIf8KOXm7CrDIrw747XFxaw7orwqhcZsKnwrPDq8KgPMK5wrLCtW0swqPCr8KuKMKNejQhwoHDvDtbXHUwMDE5SMKQwqdcdTAwMDHCpMKGwp9uw73Cp2LCpcKLeMKmwp_CqXTDk8KZT1tYZcKrw6VcdTAwMUFhX8OBJVx1MDAwNFx1MDAxNcKoK8Kkw5RuPDbDu2pvw4lcdTAwMUNcdTAwMTfDvcOTVcO5w6fCsihcdTAwMUPDuMOaw5HDicKMXsOad8KvJjXDvMOLXHUwMDEzd09GwqpccsKSwog8XHUwMDEywpPDh8KlwpBveFnClMOVRnjDvFx1MDAxNVxuw4PDhcKrw5vDssOGwpbCnVMoXHUwMDFFwrjDvVx1MDAwM8Olw7w_w5EiLCJzaWduIjoiYTE2ZWJkZWJiNjQ4YzAzYjI4Y2M0Y2ZiNTEyODA3Y2YiLCJpc1N1cGVyVXNlciI6InRydWUiLCJ1c2VyRW1haWwiOiI2MTNjODlmNjRhMWMzYTc4ZmM1NDc0ZDMxMjczZWQ4ZiIsInJvbGVDb2RlcyI6IkdaOn46eMOaw5NcdMOyw7dxwo1cdTAwMEbCjlxmXHUwMDBFccO1wo3Dt3XDtHN0d1xyw5JcdFx1MDAwRVxycFxywoLDs8KwwqlcdTAwMDBcdTAwMDDDicKkXHUwMDEwOiIsInVzZXJOYW1lIjoiYWRtaW4iLCJ1c2VySWQiOiIxMzkwYTQ5NDA3Nzg0OTIxODY4YTFhNTUxMTZjMzUxYSIsInRlbmFudCI6IiIsImV4cCI6MTc2NDQ3MTg5MH0.Z7uzBQlj-MIBYDJ78EjpNIcDrYlGxbFcFvIzrRSPxd4"
TIMEOUT = 30


@pytest.fixture(scope="session")
def base_url() -> str:
    """返回API基础URL"""
    return BASE_URL


@pytest.fixture(scope="session")
def auth_token() -> str:
    """返回认证Token"""
    return AUTH_TOKEN


@pytest.fixture(scope="session")
def auth_headers() -> dict:
    """返回带认证信息的请求头"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if AUTH_TOKEN:
        # 使用小写的 authorization，不加 Bearer 前缀
        headers["authorization"] = AUTH_TOKEN
    return headers


@pytest.fixture(scope="session")
def api_client(auth_headers) -> Generator[requests.Session, None, None]:
    """创建API客户端Session"""
    session = requests.Session()
    session.headers.update(auth_headers)
    session.verify = False  # 测试环境禁用SSL验证
    session.timeout = TIMEOUT
    yield session
    session.close()


@pytest.fixture
def template_id() -> str:
    """返回测试用模板ID（需根据实际环境配置）"""
    return "tpl-001"


@pytest.fixture
def non_existent_id() -> str:
    """返回不存在的ID"""
    return "non-existent-id-12345"


@pytest.fixture
def sample_template_data() -> dict:
    """返回示例模板数据"""
    return {
        "templateName": "pytest_test_template",
        "templateDesc": "Pytest自动化测试模板",
        "templateType": 1,
        "isDefault": 0,
        "isUse": 1
    }


@pytest.fixture
def sample_global_config() -> dict:
    """返回示例全局配置数据"""
    return {
        "saveOriginalResult": True,
        "pageShowOriginalResult": False,
        "enableAssetTypeCheck": True,
        "originalResultSaveType": 1,
        "taskRedundancyTime": 30,
        "pointCount": 100
    }


# Pytest标记定义
def pytest_configure(config):
    """配置自定义标记"""
    config.addinivalue_line("markers", "p0: 核心功能测试，必须通过")
    config.addinivalue_line("markers", "p1: 重要功能测试，应该通过")
    config.addinivalue_line("markers", "p2: 边界/异常场景测试，建议通过")
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "api01: GET /v1/config-templates 模板分页查询")
    config.addinivalue_line("markers", "api02: PUT /v1/config-templates 编辑模板")
    config.addinivalue_line("markers", "api03: POST /v1/config-templates 添加模板")
    config.addinivalue_line("markers", "api04: DELETE /v1/config-templates/{templateId} 删除模板")
    config.addinivalue_line("markers", "api05: PATCH /v1/config-templates/{templateId}/enable 启用模板")
    config.addinivalue_line("markers", "api06: PATCH /v1/config-templates/{templateId}/disable 禁用模板")
    config.addinivalue_line("markers", "api07: PATCH /v1/config-templates/{templateId}/default 设置默认模板")
    config.addinivalue_line("markers", "api08: GET /v1/config-templates/{templateId}/{optType}/basic 查询模板基本信息")
    config.addinivalue_line("markers", "api09: GET /v1/config-templates/{templateId}/list 查询模板指纹列表")
    config.addinivalue_line("markers", "api10: GET /v1/config-templates/choose 指纹分页列表")
    config.addinivalue_line("markers", "api11: POST /v1/config-templates/isExist 唯一性校验")
    config.addinivalue_line("markers", "api12: PUT /v1/config-templates/selectTemplate/{templateId} 添加全部指纹")
    config.addinivalue_line("markers", "api13: PATCH /v1/config-templates/selectTemplate/{templateId} 添加选中指纹")
    config.addinivalue_line("markers", "api14: PUT /v1/config-templates/temps/{templateId} 删除全部指纹")
    config.addinivalue_line("markers", "api15: PATCH /v1/config-templates/temps/{templateId} 批量删除指纹")
    config.addinivalue_line("markers", "api16: GET /v1/config-template/globalConf 获取全局配置")
    config.addinivalue_line("markers", "api17: POST /v1/config-template/globalConf 保存全局配置")
    config.addinivalue_line("markers", "api18: GET /v1/config-template/task 查询任务模板列表")
