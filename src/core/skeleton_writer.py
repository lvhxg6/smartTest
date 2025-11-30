"""
SkeletonWriter - 本地生成测试骨架文件

负责生成固定的基础文件，避免交给模型重复创建:
- conftest.py
- pytest.ini
- requirements.txt
"""

from pathlib import Path
from typing import Optional


CONFTEXT_TEMPLATE = """\"\"\"Pytest 基础配置与通用 fixture\"\"\"
import pytest
import requests
from requests.adapters import HTTPAdapter
import json
import urllib3
from pathlib import Path
from typing import Optional

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "{base_url}"
AUTH_TOKEN = "{auth_token}"
TIMEOUT = {timeout}

EXPLORED_DATA_FILE = Path(__file__).parent.parent / "explored_data.json"


class TimeoutHTTPAdapter(HTTPAdapter):
    \"\"\"带默认超时的 HTTPAdapter\"\"\"
    def __init__(self, timeout=30, *args, **kwargs):
        self.timeout = timeout
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return super().send(request, **kwargs)


def load_explored_data():
    \"\"\"加载探测数据\"\"\"
    if EXPLORED_DATA_FILE.exists():
        try:
            with open(EXPLORED_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {{"overall_success": False, "extracted_resources": {{}}, "exploration_notes": ["探测数据文件解析失败"]}}
    return {{"overall_success": False, "extracted_resources": {{}}, "exploration_notes": ["探测数据文件不存在"]}}


EXPLORED_DATA = load_explored_data()


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def auth_headers():
    headers = {{"Content-Type": "application/json"}}
    if AUTH_TOKEN:
        headers["authorization"] = AUTH_TOKEN
    return headers


@pytest.fixture(scope="session")
def api_client(auth_headers):
    session = requests.Session()
    session.headers.update(auth_headers)
    session.verify = False
    # 使用 TimeoutHTTPAdapter 设置默认超时
    adapter = TimeoutHTTPAdapter(timeout=TIMEOUT)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    yield session
    session.close()


@pytest.fixture(scope="session")
def explored_data():
    return EXPLORED_DATA


@pytest.fixture(scope="session")
def explored_resources():
    return EXPLORED_DATA.get("extracted_resources", {{}})


def get_explored_id(resource_name: str, index: int = 0, default: Optional[str] = None):
    ids = EXPLORED_DATA.get("extracted_resources", {{}}).get(resource_name, [])
    if ids and len(ids) > index:
        return ids[index]
    return default
"""

PYTEST_INI_TEMPLATE = """[pytest]
addopts = -q
testpaths = tests
markers =
    p0: 核心功能
    p1: 重要功能
    p2: 边界测试
timeout = {timeout}
"""

REQUIREMENTS_CONTENT = """requests
pytest
pytest-timeout
"""


class SkeletonWriter:
    """写入固定骨架文件"""

    def __init__(self, base_url: str, auth_token: str, timeout: int):
        self.base_url = base_url
        self.auth_token = auth_token
        self.timeout = timeout

    def write(self, output_dir: str) -> None:
        root = Path(output_dir)
        tests_dir = root / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)

        conftest_path = tests_dir / "conftest.py"
        pytest_ini_path = tests_dir / "pytest.ini"
        requirements_path = tests_dir / "requirements.txt"

        if not conftest_path.exists():
            # 清理 auth_token 中的非 ASCII 字符（避免 HTTP 头 latin-1 编码错误）
            clean_token = ''.join(c for c in (self.auth_token or '') if ord(c) < 128)
            conftest_path.write_text(
                CONFTEXT_TEMPLATE.format(
                    base_url=self.base_url,
                    auth_token=clean_token,
                    timeout=self.timeout
                ),
                encoding="utf-8"
            )

        if not pytest_ini_path.exists():
            pytest_ini_path.write_text(
                PYTEST_INI_TEMPLATE.format(timeout=self.timeout),
                encoding="utf-8"
            )

        if not requirements_path.exists():
            requirements_path.write_text(REQUIREMENTS_CONTENT, encoding="utf-8")
