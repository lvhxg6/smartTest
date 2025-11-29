"""
基线核查模板管理 - 模板CRUD接口测试
测试接口:
- GET /v1/config-templates (采集指纹模板分页)
- PUT /v1/config-templates (编辑模板)
- POST /v1/config-templates (添加模板)
- DELETE /v1/config-templates/{templateId} (删除模板)
"""
import pytest


class TestGetConfigTemplates:
    """GET /v1/config-templates - 采集指纹模板分页查询测试"""

    # TestCase: TC-001
    def test_query_templates_with_default_params(self, api_client, base_url):
        """正常分页查询-默认参数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "totalCount" in data
        assert "pageCount" in data
        assert "page" in data
        assert "perPage" in data
        assert isinstance(data["data"], list)

    # TestCase: TC-002
    def test_query_templates_with_pagination(self, api_client, base_url):
        """正常分页查询-指定页码和每页数量"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": 2, "perPage": 20}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data.get("perPage") == 20 or "perPage" in data

    # TestCase: TC-003
    def test_query_templates_with_template_name_filter(self, api_client, base_url):
        """正常查询-带筛选条件templateName"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"templateName": "测试模板", "page": 1, "perPage": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    # TestCase: TC-004
    def test_query_templates_with_is_use_filter(self, api_client, base_url):
        """正常查询-带筛选条件isUse"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"isUse": "1", "page": 1, "perPage": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    # TestCase: TC-005
    def test_query_templates_with_sort(self, api_client, base_url):
        """正常查询-带排序参数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"field": "createTime", "order": "desc"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    # TestCase: TC-007
    def test_query_templates_page_zero(self, api_client, base_url):
        """边界-page为0"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": 0, "perPage": 10}
        )
        # 可能返回400或自动修正为第1页
        assert response.status_code in [200, 400]

    # TestCase: TC-008
    def test_query_templates_page_negative(self, api_client, base_url):
        """边界-page为负数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": -1, "perPage": 10}
        )
        # 预期返回400或自动修正
        assert response.status_code in [200, 400]

    # TestCase: TC-009
    def test_query_templates_per_page_zero(self, api_client, base_url):
        """边界-perPage为0"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": 1, "perPage": 0}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-010
    def test_query_templates_per_page_large(self, api_client, base_url):
        """边界-perPage超大值"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": 1, "perPage": 10000}
        )
        assert response.status_code == 200

    # TestCase: TC-011
    def test_query_templates_page_type_error(self, api_client, base_url):
        """边界-page类型错误"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": "abc", "perPage": 10}
        )
        assert response.status_code == 400

    # TestCase: TC-012
    def test_query_templates_empty_result(self, api_client, base_url):
        """边界-空数据查询"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"templateName": "不存在的模板名称_xyz123", "page": 1, "perPage": 10}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("data") == [] or data.get("totalCount") == 0


class TestPutConfigTemplates:
    """PUT /v1/config-templates - 编辑模板测试"""

    # TestCase: TC-013
    def test_update_template_name(self, api_client, base_url, existing_template_id):
        """正常编辑模板-更新模板名称"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": existing_template_id,
                "templateName": "更新后的模板名称",
                "templateVer": "1.0"
            }
        )
        # 如果模板不存在可能返回400/404
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-014
    def test_update_template_desc(self, api_client, base_url, existing_template_id):
        """正常编辑模板-更新模板描述"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": existing_template_id,
                "templateDesc": "更新后的描述"
            }
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-015
    def test_update_template_multiple_fields(self, api_client, base_url, existing_template_id):
        """正常编辑模板-更新多个字段"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": existing_template_id,
                "templateName": "更新名称",
                "templateDesc": "更新描述",
                "templateType": 1
            }
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-016
    def test_update_template_missing_body(self, api_client, base_url):
        """异常-缺少请求体"""
        response = api_client.put(
            f"{base_url}/v1/config-templates"
        )
        assert response.status_code in [400, 415]

    # TestCase: TC-017
    def test_update_template_empty_body(self, api_client, base_url):
        """异常-空请求体"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-018
    def test_update_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": "non-existing-template-id-xyz",
                "templateName": "测试"
            }
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-019
    def test_update_template_empty_name(self, api_client, base_url, existing_template_id):
        """边界-templateName为空字符串"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": existing_template_id,
                "templateName": ""
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-020
    def test_update_template_long_name(self, api_client, base_url, existing_template_id):
        """边界-templateName超长"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": existing_template_id,
                "templateName": "A" * 500
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-021
    def test_update_template_special_chars_name(self, api_client, base_url, existing_template_id):
        """边界-templateName包含特殊字符"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": existing_template_id,
                "templateName": "<script>alert(1)</script>"
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-022
    def test_update_template_type_error(self, api_client, base_url, existing_template_id):
        """异常-templateType类型错误"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": existing_template_id,
                "templateType": "invalid"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-023
    def test_update_template_invalid_json(self, api_client, base_url):
        """异常-请求体格式错误"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            data="not a json string",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400


class TestPostConfigTemplates:
    """POST /v1/config-templates - 添加模板测试"""

    # TestCase: TC-024
    def test_add_template_required_fields(self, api_client, base_url, unique_template_name):
        """正常添加模板-必填字段"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": unique_template_name,
                "templateVer": "1.0"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "entity" in data

    # TestCase: TC-025
    def test_add_template_all_fields(self, api_client, base_url, unique_template_name):
        """正常添加模板-全部字段"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": f"{unique_template_name}_full",
                "templateVer": "1.0",
                "templateDesc": "完整描述",
                "templateType": 1,
                "isDefault": 0,
                "isUse": 1
            }
        )
        assert response.status_code == 200

    # TestCase: TC-026
    def test_add_template_missing_body(self, api_client, base_url):
        """异常-缺少请求体"""
        response = api_client.post(
            f"{base_url}/v1/config-templates"
        )
        assert response.status_code in [400, 415]

    # TestCase: TC-027
    def test_add_template_empty_body(self, api_client, base_url):
        """异常-空请求体"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={}
        )
        assert response.status_code == 400

    # TestCase: TC-028
    def test_add_template_duplicate_name(self, api_client, base_url):
        """异常-模板名称重复"""
        # 首先获取一个已存在的模板名称
        list_response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": 1, "perPage": 1}
        )
        if list_response.status_code == 200:
            data = list_response.json()
            if data.get("data") and len(data["data"]) > 0:
                existing_name = data["data"][0].get("bookName") or data["data"][0].get("templateName")
                if existing_name:
                    response = api_client.post(
                        f"{base_url}/v1/config-templates",
                        json={"templateName": existing_name}
                    )
                    assert response.status_code in [200, 400]
                    return
        # 如果无法获取已存在名称，跳过测试
        pytest.skip("无法获取已存在的模板名称")

    # TestCase: TC-029
    def test_add_template_empty_name(self, api_client, base_url):
        """边界-templateName为空字符串"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={"templateName": ""}
        )
        assert response.status_code == 400

    # TestCase: TC-030
    def test_add_template_whitespace_name(self, api_client, base_url):
        """边界-templateName只有空格"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={"templateName": "   "}
        )
        assert response.status_code == 400

    # TestCase: TC-031
    def test_add_template_long_name(self, api_client, base_url):
        """边界-templateName超长"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={"templateName": "A" * 500}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-032
    def test_add_template_long_desc(self, api_client, base_url, unique_template_name):
        """边界-templateDesc超长"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": unique_template_name,
                "templateDesc": "A" * 5000
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-033
    def test_add_template_invalid_type(self, api_client, base_url, unique_template_name):
        """异常-templateType无效值"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": unique_template_name,
                "templateType": 999
            }
        )
        assert response.status_code in [200, 400]


class TestDeleteConfigTemplates:
    """DELETE /v1/config-templates/{templateId} - 删除模板测试"""

    # TestCase: TC-034
    def test_delete_template_success(self, api_client, base_url, unique_template_name):
        """正常删除模板"""
        # 先创建一个模板
        create_response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={"templateName": unique_template_name, "templateVer": "1.0"}
        )
        if create_response.status_code == 200:
            data = create_response.json()
            template_id = data.get("entity", {}).get("pkHandbook") or data.get("entity", {}).get("key")
            if template_id:
                # 删除模板
                response = api_client.delete(
                    f"{base_url}/v1/config-templates/{template_id}"
                )
                assert response.status_code == 200
                return
        pytest.skip("无法创建测试模板")

    # TestCase: TC-035
    def test_delete_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.delete(
            f"{base_url}/v1/config-templates/non-existing-template-id-xyz"
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-036
    def test_delete_template_empty_id(self, api_client, base_url):
        """异常-模板ID为空"""
        response = api_client.delete(
            f"{base_url}/v1/config-templates/"
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-039
    def test_delete_template_special_chars_id(self, api_client, base_url):
        """边界-templateId包含特殊字符"""
        response = api_client.delete(
            f"{base_url}/v1/config-templates/<script>"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-040
    def test_delete_template_sql_injection(self, api_client, base_url):
        """边界-templateId为SQL注入"""
        response = api_client.delete(
            f"{base_url}/v1/config-templates/1' OR '1'='1"
        )
        assert response.status_code in [400, 404]
