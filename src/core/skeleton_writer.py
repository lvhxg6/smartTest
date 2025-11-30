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
    session.timeout = TIMEOUT
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
            conftest_path.write_text(
                CONFTEXT_TEMPLATE.format(
                    base_url=self.base_url,
                    auth_token=self.auth_token or "",
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
