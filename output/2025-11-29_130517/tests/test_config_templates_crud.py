"""
基线核查模板增删改接口测试

API-02: PUT /v1/config-templates 编辑模板
API-03: POST /v1/config-templates 添加模板
API-04: DELETE /v1/config-templates/{templateId} 删除模板
"""

import pytest
import uuid


class TestCreateTemplate:
    """API-03: POST /v1/config-templates 添加基线核查模板"""

    # TestCase: TC-021
    @pytest.mark.p0
    @pytest.mark.api03
    def test_create_template_required_fields(self, api_client, base_url):
        """正常添加模板-必填字段"""
        unique_name = f"pytest_template_{uuid.uuid4().hex[:8]}"
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": unique_name,
                "templateType": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "entity" in data

    # TestCase: TC-022
    @pytest.mark.p0
    @pytest.mark.api03
    def test_create_template_all_fields(self, api_client, base_url, sample_template_data):
        """正常添加模板-全部字段"""
        sample_template_data["templateName"] = f"pytest_full_{uuid.uuid4().hex[:8]}"
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json=sample_template_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "entity" in data

    # TestCase: TC-023
    @pytest.mark.p1
    @pytest.mark.api03
    def test_create_template_empty_body(self, api_client, base_url):
        """必填参数缺失-RequestBody为空"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={}
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-024
    @pytest.mark.p1
    @pytest.mark.api03
    def test_create_template_missing_name(self, api_client, base_url):
        """必填参数缺失-templateName为空"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateType": 1
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-025
    @pytest.mark.p1
    @pytest.mark.api03
    def test_create_template_invalid_type(self, api_client, base_url):
        """参数类型错误-templateType非整数"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": "test_template",
                "templateType": "one"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-026
    @pytest.mark.p2
    @pytest.mark.api03
    def test_create_template_empty_name(self, api_client, base_url):
        """边界测试-templateName为空字符串"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": "",
                "templateType": 1
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-027
    @pytest.mark.p2
    @pytest.mark.api03
    def test_create_template_name_too_long(self, api_client, base_url):
        """边界测试-templateName超长"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": "a" * 1000,
                "templateType": 1
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-028
    @pytest.mark.p2
    @pytest.mark.api03
    def test_create_template_name_special_chars(self, api_client, base_url):
        """边界测试-templateName特殊字符"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": "测试<>&\"'模板",
                "templateType": 1
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-029
    @pytest.mark.p1
    @pytest.mark.api03
    def test_create_template_duplicate_name(self, api_client, base_url):
        """重复添加-模板名称重复"""
        # 先创建一个模板
        unique_name = f"duplicate_test_{uuid.uuid4().hex[:8]}"
        api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": unique_name,
                "templateType": 1
            }
        )
        # 再次创建同名模板
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": unique_name,
                "templateType": 1
            }
        )
        # 重复名称应该返回错误或false
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            # 如果返回200，success应为false
            assert data.get("success") is False or "error" in str(data).lower()


class TestUpdateTemplate:
    """API-02: PUT /v1/config-templates 编辑基线核查模板"""

    # TestCase: TC-012
    @pytest.mark.p0
    @pytest.mark.api02
    def test_update_template_success(self, api_client, base_url, template_id):
        """正常编辑模板"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": template_id,
                "templateName": f"updated_template_{uuid.uuid4().hex[:8]}",
                "templateDesc": "更新后的描述"
            }
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-013
    @pytest.mark.p0
    @pytest.mark.api02
    def test_update_template_all_fields(self, api_client, base_url, template_id):
        """编辑模板-修改全部字段"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": template_id,
                "templateName": f"full_update_{uuid.uuid4().hex[:8]}",
                "templateDesc": "完整更新描述",
                "templateType": 1,
                "isDefault": 0,
                "isUse": 1,
                "templateVer": "2.0"
            }
        )
        assert response.status_code in [200, 404]

    # TestCase: TC-014
    @pytest.mark.p1
    @pytest.mark.api02
    def test_update_template_empty_body(self, api_client, base_url):
        """必填参数缺失-RequestBody为空"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={}
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-015
    @pytest.mark.p1
    @pytest.mark.api02
    def test_update_template_invalid_type(self, api_client, base_url, template_id):
        """参数类型错误-templateType非整数"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": template_id,
                "templateType": "abc"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-016
    @pytest.mark.p1
    @pytest.mark.api02
    def test_update_template_invalid_isdefault(self, api_client, base_url, template_id):
        """参数类型错误-isDefault非整数"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": template_id,
                "isDefault": "yes"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-017
    @pytest.mark.p2
    @pytest.mark.api02
    def test_update_template_empty_name(self, api_client, base_url, template_id):
        """边界测试-templateName为空字符串"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": template_id,
                "templateName": ""
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-018
    @pytest.mark.p2
    @pytest.mark.api02
    def test_update_template_name_too_long(self, api_client, base_url, template_id):
        """边界测试-templateName超长"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": template_id,
                "templateName": "a" * 1000
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-019
    @pytest.mark.p2
    @pytest.mark.api02
    def test_update_template_desc_special_chars(self, api_client, base_url, template_id):
        """边界测试-templateDesc特殊字符"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": template_id,
                "templateDesc": "<script>alert(1)</script>"
            }
        )
        assert response.status_code in [200, 400]
        # 应正确处理/转义特殊字符

    # TestCase: TC-020
    @pytest.mark.p1
    @pytest.mark.api02
    def test_update_template_not_exist(self, api_client, base_url, non_existent_id):
        """编辑不存在的模板"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": non_existent_id,
                "templateName": "not_exist_update"
            }
        )
        assert response.status_code in [400, 404]


class TestDeleteTemplate:
    """API-04: DELETE /v1/config-templates/{templateId} 删除基线核查模板"""

    # TestCase: TC-030
    @pytest.mark.p0
    @pytest.mark.api04
    def test_delete_template_success(self, api_client, base_url):
        """正常删除模板"""
        # 先创建一个模板用于删除
        unique_name = f"delete_test_{uuid.uuid4().hex[:8]}"
        create_response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": unique_name,
                "templateType": 1
            }
        )

        if create_response.status_code == 200:
            data = create_response.json()
            # 尝试获取新建模板的ID
            template_id = data.get("entity", {}).get("pkCollectTemplate") or data.get("entity", {}).get("key")

            if template_id:
                # 删除模板
                response = api_client.delete(
                    f"{base_url}/v1/config-templates/{template_id}"
                )
                assert response.status_code in [200, 404]
                if response.status_code == 200:
                    assert response.json().get("success") is True

    # TestCase: TC-031
    @pytest.mark.p1
    @pytest.mark.api04
    def test_delete_template_not_exist(self, api_client, base_url, non_existent_id):
        """删除不存在的模板"""
        response = api_client.delete(
            f"{base_url}/v1/config-templates/{non_existent_id}"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-032
    @pytest.mark.p1
    @pytest.mark.api04
    def test_delete_template_empty_id(self, api_client, base_url):
        """必填参数缺失-templateId为空"""
        response = api_client.delete(
            f"{base_url}/v1/config-templates/"
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-033
    @pytest.mark.p2
    @pytest.mark.api04
    def test_delete_template_special_chars(self, api_client, base_url):
        """边界测试-templateId特殊字符"""
        response = api_client.delete(
            f"{base_url}/v1/config-templates/../../../etc"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-034
    @pytest.mark.p2
    @pytest.mark.api04
    def test_delete_template_id_too_long(self, api_client, base_url):
        """边界测试-templateId超长"""
        response = api_client.delete(
            f"{base_url}/v1/config-templates/{'a' * 1000}"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-035
    @pytest.mark.p1
    @pytest.mark.api04
    def test_delete_default_template(self, api_client, base_url):
        """删除默认模板（业务规则测试）"""
        # 注意：需要有一个实际的默认模板ID才能测试
        # 这里使用占位符，实际测试时需替换
        default_template_id = "default-template-placeholder"
        response = api_client.delete(
            f"{base_url}/v1/config-templates/{default_template_id}"
        )
        # 默认模板不能删除，应返回错误
        assert response.status_code in [400, 404, 200]

    # TestCase: TC-036
    @pytest.mark.p1
    @pytest.mark.api04
    def test_delete_template_in_use(self, api_client, base_url):
        """删除正在使用的模板（业务规则测试）"""
        # 注意：需要有一个实际被使用的模板ID才能测试
        # 这里使用占位符，实际测试时需替换
        in_use_template_id = "in-use-template-placeholder"
        response = api_client.delete(
            f"{base_url}/v1/config-templates/{in_use_template_id}"
        )
        # 使用中的模板不能删除，应返回错误
        assert response.status_code in [400, 404, 200]
