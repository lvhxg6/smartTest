"""
BMS WebAPI 测试配置文件
基线管理系统接口自动化测试配置
"""
import pytest
import requests
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 环境配置
BASE_URL = "https://localhost:4089"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyZWFsTmFtZSI6ImM1NjBjNTVjZmViOGEzNTFkOGUwNjMzMjM1MmQ4NWQ4IiwiY2xpZW50SXAiOiIxOTIuMTY4LjE0LjEwMSIsInVzZXJQaG9uZSI6IjM5YTNhNDgyZmUwYzYyYjNiMThlNTQxNjdhNWZkNTAwIiwicmlnaHRDb2RlcyI6IkdaOn46eMOafVVbw5rDoyBcYsOdUMKeZlx1MDAwN1RJw4rDlMKIwp_Cl8Omw6_Dv8Oiw753MXjCiW3DknbCnsKCXHUwMDFDwoRcdTAwMDNcdTAwMDHCtFx1MDAxQ0lhXsOBw4LCgsOTw43DsmZQL0NcdTAwMDEhYMOMw7HDoXDCisK4Olx1MDAwM3FAXHUwMDExw4Jtwpc3w7bCt1xiXHUwMDE3woM5XFx5wpvDiMOlwqDDgMOmYjI5Vl3CgMKzX8OFw4bCoMKKXHJcdTAwMEXCjyAhRGdnWsK6w4HDojnCuS7Dj8OkcVx1MDAwM2PCmnXDk21cYjfCt8OpwqbCqsKEXHUwMDAywprCuUliw5rCrS4gWsKyw5jDjcO2PMOYwqHCl8OvU3Enw5zDusKVTsKzczLCvExcdTAwMDFVw7JcdTAwMTRcdTAwMUbDmcKxIcO1wphcdTAwMDbDt1NZw57DtMOFayXCk1x1MDAwMsO6w51KwpMwVFx1MDAwNsOBSn41ZcKbXHUwMDA1McKPwoDCr8O5acKCQ8K-PMOPNcKRQ8OeR8OoU8KZdsOsWMKIZGkmw5R5ZUvCkcO9wp5scsKLXHUwMDA3LVx1MDAxNMORXHUwMDE5fnTDgn5aUcOIwozCk2bClVbCtMKjUMKgdcK-csKIXHUwMDAybMOWMMOowpHDv0TCq2NcdTAwMUZcdTAwMULDmkpObMKzR8OFXktMwqtywohcdTAwMTBTaHLDv8O9PThZw4HCpHTDvcK4w6dxUsKfXHUwMDE4J8KnS8OcfsOyKMK2PsOuw4fDk8KBw53CuGVPXjVGwqBxwpJcdTAwMTbDiHtuT1x1MDAwQsKDccOMXGIswpPDs3zCpVx1MDAwQsOFw5rDvcOtf0thwpogw6XCi01cdTAwMTJGYsOvw6TDmlZKUHXDnVXClVxyK8Opwo0rw5jCpSvCvsOWwrTCoCNMwo7DnMOnwqVHWcO5LsOtw6B5fVVHXHUwMDBGNsOMXCLCsF_DgMOSb8O9XHUwMDFCXHLCukBUw5dcdTAwMUHDvcO1wpzDrFnDs8OKwrVpIMOFK3vDusOFPcO0wp1vOMK0byE-XHUwMDE1wqBSfFbCq1x1MDAxRMKfNWvDp1x1MDAxRcOZwrMswppiWsKFalTCpVx1MDAwRVx1MDAwN8O9NsKUwppXwpBcdDMkPVx1MDAxOMOSw6XDtUjCjsOsw4xNw4ZcdTAwMUbDhyHDuXLDjcKJesOJQW94eVfCi287wq18IVx0aiXClcOgUMOJLMKpwpZpXHUwMDA3wqRccsOeMWUkw6s2dsOSLFFcdTAwMTZFXHUwMDE5wobCg03DvsKze8KQwqVcdTAwMDBWwpVcdTAwMTXDsMOuwqjDjFxmSllIf8KOXm7CrDIrw747XFxaw7orwqhcZsKnwrPDq8KgPMK5wrLCtW0swqPCr8KuKMKNejQhwoHDvDtbXHUwMDE5SMKQwqdcdTAwMDHCpMKGwp9uw73Cp2LCpcKLeMKmwp_CqXTDk8KZT1tYZcKrw6VcdTAwMUFhX8OBJVx1MDAwNFx1MDAxNcKoK8Kkw5RuPDbDu2pvw4lcdTAwMUNcdTAwMTfDvcOTVcO5w6fCsihcdTAwMUPDuMOaw5HDicKMXsOad8KvJjXDvMOLXHUwMDEzd09GwqpccsKSwog8XHUwMDEywpPDh8KlwpBveFnClMOVRnjDvFx1MDAxNVxuw4PDhcKrw5vDssOGwpbCnVMoXHUwMDFFwrjDvVx1MDAwM8Olw7w_w5EiLCJzaWduIjoiYTE2ZWJkZWJiNjQ4YzAzYjI4Y2M0Y2ZiNTEyODA3Y2YiLCJpc1N1cGVyVXNlciI6InRydWUiLCJ1c2VyRW1haWwiOiI2MTNjODlmNjRhMWMzYTc4ZmM1NDc0ZDMxMjczZWQ4ZiIsInJvbGVDb2RlcyI6IkdaOn46eMOaw5NcdMOyw7dxwo1cdTAwMEbCjlxmXHUwMDBFccO1wo3Dt3XDtHN0d1xyw5JcdFx1MDAwRVxycFxywoLDs8KwwqlcdTAwMDBcdTAwMDDDicKkXHUwMDEwOiIsInVzZXJOYW1lIjoiYWRtaW4iLCJ1c2VySWQiOiIxMzkwYTQ5NDA3Nzg0OTIxODY4YTFhNTUxMTZjMzUxYSIsInRlbmFudCI6IiIsImV4cCI6MTc2NDQ3MTg5MH0.Z7uzBQlj-MIBYDJ78EjpNIcDrYlGxbFcFvIzrRSPxd4"
TIMEOUT = 30


@pytest.fixture(scope="session")
def base_url():
    """返回API基础URL"""
    return BASE_URL


@pytest.fixture(scope="session")
def auth_token():
    """返回认证Token"""
    return AUTH_TOKEN


@pytest.fixture(scope="session")
def auth_headers():
    """返回包含认证信息的请求头"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    return headers


@pytest.fixture(scope="session")
def api_client(base_url, auth_headers):
    """返回配置好的API客户端Session"""
    session = requests.Session()
    session.headers.update(auth_headers)
    session.verify = False  # 禁用SSL验证（开发/测试环境）
    session.timeout = TIMEOUT
    return session


@pytest.fixture
def created_template_ids():
    """存储测试过程中创建的模板ID，用于清理"""
    return []


@pytest.fixture(autouse=False)
def cleanup_templates(api_client, base_url, created_template_ids):
    """测试后清理创建的模板"""
    yield
    for template_id in created_template_ids:
        try:
            api_client.delete(f"{base_url}/v1/config-templates/{template_id}")
        except Exception:
            pass


def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "p0: 核心功能，必须通过"
    )
    config.addinivalue_line(
        "markers", "p1: 重要功能，应该通过"
    )
    config.addinivalue_line(
        "markers", "p2: 边界场景，建议通过"
    )
