"""
基线核查模板管理 - 查询接口测试
GET /v1/config-templates - 采集指纹模板分页
"""
import pytest


class TestConfigTemplatesQuery:
    """采集指纹模板分页查询接口测试"""

    # TestCase: TC-001
    def test_query_with_default_pagination(self, api_client, base_url):
        """正常查询-默认分页"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "params.templateName": "测试模板"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "totalCount" in data
        assert "pageCount" in data
        assert "perPage" in data
        assert "page" in data
        assert isinstance(data["data"], list)

    # TestCase: TC-002
    def test_query_with_custom_pagination(self, api_client, base_url):
        """正常查询-指定分页参数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 2,
                "perPage": 20,
                "params.templateName": "模板"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("page") == 2 or data.get("page") is None
        assert data.get("perPage") == 20 or data.get("perPage") is None

    # TestCase: TC-003
    def test_query_with_multiple_conditions(self, api_client, base_url):
        """正常查询-多条件筛选"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "params.templateName": "测试",
                "params.isUse": "1",
                "params.isDefault": "0"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    # TestCase: TC-004
    def test_query_with_time_range(self, api_client, base_url):
        """正常查询-时间范围筛选"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "params.templateName": "",
                "params.updateStartTime": "2025-01-01",
                "params.updateEndTime": "2025-12-31"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    # TestCase: TC-005
    def test_query_with_sorting(self, api_client, base_url):
        """正常查询-排序功能"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "params.templateName": "",
                "params.field": "createTime",
                "params.order": "desc"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    # TestCase: TC-006
    def test_query_missing_required_params(self, api_client, base_url):
        """必填参数缺失-params"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 1,
                "perPage": 10
            }
        )
        # 预期400错误或服务端有默认处理返回200
        assert response.status_code in [200, 400]

    # TestCase: TC-007
    def test_query_invalid_page_type(self, api_client, base_url):
        """参数类型错误-page非整数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": "abc",
                "perPage": 10,
                "params.templateName": "测试"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-008
    def test_query_invalid_perpage_type(self, api_client, base_url):
        """参数类型错误-perPage非整数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 1,
                "perPage": "xyz",
                "params.templateName": "测试"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-009
    def test_query_page_zero(self, api_client, base_url):
        """边界测试-page为0"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 0,
                "perPage": 10,
                "params.templateName": "测试"
            }
        )
        # 服务端可能自动调整为1或返回400
        assert response.status_code in [200, 400]

    # TestCase: TC-010
    def test_query_page_negative(self, api_client, base_url):
        """边界测试-page为负数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": -1,
                "perPage": 10,
                "params.templateName": "测试"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-011
    def test_query_perpage_zero(self, api_client, base_url):
        """边界测试-perPage为0"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 1,
                "perPage": 0,
                "params.templateName": "测试"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-012
    def test_query_perpage_large_value(self, api_client, base_url):
        """边界测试-perPage超大值"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 1,
                "perPage": 10000,
                "params.templateName": "测试"
            }
        )
        # 服务端可能限制最大值或正常返回
        assert response.status_code == 200

    # TestCase: TC-013
    def test_query_empty_template_name(self, api_client, base_url):
        """边界测试-templateName为空字符串"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "params.templateName": ""
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    # TestCase: TC-014
    def test_query_special_characters(self, api_client, base_url):
        """边界测试-特殊字符"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "params.templateName": "<script>alert(1)</script>"
            }
        )
        # 应正确处理特殊字符，返回空结果或200
        assert response.status_code == 200

    # TestCase: TC-015
    def test_query_long_string(self, api_client, base_url):
        """边界测试-超长字符串"""
        long_name = "a" * 300
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "params.templateName": long_name
            }
        )
        # 可能返回400(参数过长)或200(正常处理)
        assert response.status_code in [200, 400]
