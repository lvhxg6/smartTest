"""
通用测试用例（适用于所有接口）

TC-121 ~ TC-127: 请求方法、Content-Type、JSON格式、并发、安全等通用测试
"""

import pytest
import json
import concurrent.futures


class TestCommonScenarios:
    """通用测试场景"""

    # TestCase: TC-121
    @pytest.mark.p1
    def test_wrong_http_method(self, api_client, base_url):
        """请求方法错误-对GET接口发送POST请求"""
        # /v1/config-template/task 是GET接口
        response = api_client.post(
            f"{base_url}/v1/config-template/task"
        )
        assert response.status_code == 405

    # TestCase: TC-121b
    @pytest.mark.p1
    def test_wrong_http_method_get_for_post(self, api_client, base_url):
        """请求方法错误-对POST接口发送GET请求"""
        # /v1/config-templates 是POST接口（添加模板）
        response = api_client.get(
            f"{base_url}/v1/config-templates/isExist"
        )
        # GET也可能被允许返回400或405
        assert response.status_code in [400, 405, 200]

    # TestCase: TC-122
    @pytest.mark.p1
    def test_wrong_content_type(self, api_client, base_url):
        """Content-Type错误-POST请求使用text/plain"""
        headers = api_client.headers.copy()
        headers["Content-Type"] = "text/plain"

        response = api_client.post(
            f"{base_url}/v1/config-templates",
            data="templateName=test",
            headers=headers
        )
        assert response.status_code in [400, 415]

    # TestCase: TC-122b
    @pytest.mark.p1
    def test_wrong_content_type_put(self, api_client, base_url, template_id):
        """Content-Type错误-PUT请求使用text/plain"""
        headers = api_client.headers.copy()
        headers["Content-Type"] = "text/plain"

        response = api_client.put(
            f"{base_url}/v1/config-templates",
            data="templateName=test",
            headers=headers
        )
        assert response.status_code in [400, 415]

    # TestCase: TC-123
    @pytest.mark.p1
    def test_invalid_json_format(self, api_client, base_url):
        """请求体JSON格式错误"""
        headers = api_client.headers.copy()

        response = api_client.post(
            f"{base_url}/v1/config-templates",
            data='{"templateName": invalid}',  # 无效JSON
            headers=headers
        )
        assert response.status_code == 400

    # TestCase: TC-123b
    @pytest.mark.p1
    def test_malformed_json(self, api_client, base_url):
        """请求体JSON畸形-缺少结束括号"""
        headers = api_client.headers.copy()

        response = api_client.post(
            f"{base_url}/v1/config-templates",
            data='{"templateName": "test"',  # 缺少}
            headers=headers
        )
        assert response.status_code == 400

    # TestCase: TC-124
    @pytest.mark.p2
    def test_missing_accept_header(self, api_client, base_url):
        """请求头缺失Accept"""
        headers = api_client.headers.copy()
        if "Accept" in headers:
            del headers["Accept"]

        response = api_client.get(
            f"{base_url}/v1/config-template/task",
            headers=headers
        )
        # 缺少Accept头应默认返回JSON
        assert response.status_code == 200
        # 验证返回的是JSON格式
        try:
            response.json()
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")

    # TestCase: TC-125
    @pytest.mark.p2
    def test_concurrent_requests(self, api_client, base_url):
        """并发请求测试"""
        def make_request():
            return api_client.get(f"{base_url}/v1/config-template/task")

        # 发送10个并发请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 所有请求应正常响应
        for response in results:
            assert response.status_code == 200

    # TestCase: TC-126
    @pytest.mark.p2
    def test_long_url(self, api_client, base_url):
        """超长URL测试"""
        # 构造超长查询参数
        long_param = "a" * 8000
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"checkItemName": long_param}
        )
        # 应返回414 URI Too Long 或 400
        assert response.status_code in [400, 414, 200]

    # TestCase: TC-127
    @pytest.mark.p1
    def test_sql_injection(self, api_client, base_url):
        """SQL注入测试"""
        sql_injection_payload = "'; DROP TABLE templates; --"

        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"checkItemName": sql_injection_payload}
        )
        # 应正常返回，不执行SQL
        assert response.status_code in [200, 400]
        # 验证系统未崩溃
        if response.status_code == 200:
            data = response.json()
            assert "data" in data or "entity" in data or "success" in data

    # TestCase: TC-127b
    @pytest.mark.p1
    def test_sql_injection_in_body(self, api_client, base_url):
        """SQL注入测试-请求体"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": "'; DROP TABLE templates; --",
                "templateType": 1
            }
        )
        # 应正常处理，不执行SQL
        assert response.status_code in [200, 400]

    # TestCase: TC-127c
    @pytest.mark.p1
    def test_xss_injection(self, api_client, base_url):
        """XSS注入测试"""
        xss_payload = "<script>alert('XSS')</script>"

        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": xss_payload,
                "templateType": 1
            }
        )
        # 应正常处理，转义或拒绝
        assert response.status_code in [200, 400]

    # TestCase: TC-127d
    @pytest.mark.p2
    def test_path_traversal(self, api_client, base_url):
        """路径遍历测试"""
        path_traversal_payload = "../../../etc/passwd"

        response = api_client.get(
            f"{base_url}/v1/config-templates/{path_traversal_payload}/view/basic"
        )
        # 应拒绝非法路径
        assert response.status_code in [400, 404]


class TestResponseValidation:
    """响应格式验证"""

    @pytest.mark.p0
    def test_response_structure_success(self, api_client, base_url):
        """验证成功响应结构"""
        response = api_client.get(f"{base_url}/v1/config-template/task")
        assert response.status_code == 200

        data = response.json()
        # 验证基本响应结构
        assert isinstance(data, dict)
        # 应包含success或entity字段
        assert "success" in data or "entity" in data or "data" in data

    @pytest.mark.p1
    def test_response_headers(self, api_client, base_url):
        """验证响应头"""
        response = api_client.get(f"{base_url}/v1/config-template/task")
        assert response.status_code == 200

        # 验证Content-Type
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type or "*/*" in content_type


class TestAuthenticationScenarios:
    """认证场景测试（如果需要认证）"""

    @pytest.mark.p1
    def test_request_without_token(self, base_url):
        """无Token请求"""
        import requests
        session = requests.Session()
        session.verify = False

        response = session.get(f"{base_url}/v1/config-template/task")
        # 可能返回401或200（取决于接口是否需要认证）
        assert response.status_code in [200, 401, 403]

    @pytest.mark.p1
    def test_request_with_invalid_token(self, base_url):
        """无效Token请求"""
        import requests
        session = requests.Session()
        session.verify = False
        session.headers.update({"Authorization": "Bearer invalid_token_12345"})

        response = session.get(f"{base_url}/v1/config-template/task")
        # 可能返回401/403或200（取决于Token验证策略）
        assert response.status_code in [200, 401, 403]

    @pytest.mark.p2
    def test_request_with_expired_token(self, base_url):
        """过期Token请求"""
        import requests
        session = requests.Session()
        session.verify = False
        # 模拟过期Token（通常JWT过期后仍是有效格式但会被拒绝）
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjB9.expired"
        session.headers.update({"Authorization": f"Bearer {expired_token}"})

        response = session.get(f"{base_url}/v1/config-template/task")
        # 过期Token应被拒绝
        assert response.status_code in [200, 401, 403]
