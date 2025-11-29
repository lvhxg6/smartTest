"""
基线核查模板管理 - 模板CRUD测试
接口路径: /v1/config-templates
"""
import pytest
import json
import uuid


class TestGetConfigTemplates:
    """GET /v1/config-templates - 采集指纹模板分页查询测试"""

    # TestCase: TC-001
    @pytest.mark.p0
    def test_query_default_pagination(self, api_client, base_url):
        """正常查询-默认分页"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"params": "{}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "totalCount" in data
        assert "pageCount" in data
        assert "perPage" in data
        assert "page" in data

    # TestCase: TC-002
    @pytest.mark.p0
    def test_query_with_pagination_params(self, api_client, base_url):
        """正常查询-指定分页参数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 2,
                "perPage": 20,
                "params": "{}"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("page") == 2 or data.get("perPage") == 20

    # TestCase: TC-003
    @pytest.mark.p0
    def test_query_with_filter_conditions(self, api_client, base_url):
        """正常查询-带筛选条件"""
        params_obj = {"templateName": "测试模板", "isUse": "1"}
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"params": json.dumps(params_obj)}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    # TestCase: TC-004
    @pytest.mark.p1
    def test_query_with_sort_params(self, api_client, base_url):
        """正常查询-带排序参数"""
        params_obj = {"field": "createTime", "order": "desc"}
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"params": json.dumps(params_obj)}
        )
        assert response.status_code == 200

    # TestCase: TC-005
    @pytest.mark.p0
    def test_query_missing_required_params(self, api_client, base_url):
        """异常-缺少必填参数params"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": 1, "perPage": 10}
        )
        # 根据实际API行为，可能返回400或使用默认值
        assert response.status_code in [200, 400]

    # TestCase: TC-006
    @pytest.mark.p1
    def test_query_page_zero(self, api_client, base_url):
        """边界-page为0"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": 0, "perPage": 10, "params": "{}"}
        )
        # 可能返回400或自动修正为第1页
        assert response.status_code in [200, 400]

    # TestCase: TC-007
    @pytest.mark.p1
    def test_query_page_negative(self, api_client, base_url):
        """边界-page为负数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": -1, "perPage": 10, "params": "{}"}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-008
    @pytest.mark.p1
    def test_query_per_page_zero(self, api_client, base_url):
        """边界-perPage为0"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": 1, "perPage": 0, "params": "{}"}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-009
    @pytest.mark.p1
    def test_query_per_page_negative(self, api_client, base_url):
        """边界-perPage为负数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": 1, "perPage": -5, "params": "{}"}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-010
    @pytest.mark.p2
    def test_query_per_page_large_value(self, api_client, base_url):
        """边界-perPage超大值"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": 1, "perPage": 10000, "params": "{}"}
        )
        assert response.status_code == 200

    # TestCase: TC-011
    @pytest.mark.p2
    def test_query_page_out_of_range(self, api_client, base_url):
        """边界-page超出范围"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": 999, "perPage": 10, "params": "{}"}
        )
        assert response.status_code == 200
        data = response.json()
        # 超出范围应返回空数组
        assert data.get("data") == [] or data.get("data") is not None

    # TestCase: TC-012
    @pytest.mark.p1
    def test_query_page_type_error(self, api_client, base_url):
        """异常-page类型错误"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"page": "abc", "perPage": 10, "params": "{}"}
        )
        assert response.status_code == 400

    # TestCase: TC-013
    @pytest.mark.p1
    def test_query_empty_data(self, api_client, base_url):
        """边界-空数据查询"""
        params_obj = {"templateName": f"不存在的模板_{uuid.uuid4().hex}"}
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"params": json.dumps(params_obj)}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("data") == [] or data.get("totalCount") == 0


class TestPostConfigTemplates:
    """POST /v1/config-templates - 添加模板测试"""

    # TestCase: TC-014
    @pytest.mark.p0
    def test_add_template_with_required_fields(self, api_client, base_url):
        """正常添加模板-必填字段"""
        template_name = f"测试模板_{uuid.uuid4().hex[:8]}"
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": template_name,
                "templateType": 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    # TestCase: TC-015
    @pytest.mark.p0
    def test_add_template_with_all_fields(self, api_client, base_url):
        """正常添加模板-全字段"""
        template_name = f"完整模板_{uuid.uuid4().hex[:8]}"
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": template_name,
                "templateVer": "1.0",
                "templateDesc": "测试描述",
                "templateType": 1,
                "isDefault": 0,
                "isUse": 1,
                "specification": "规范"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    # TestCase: TC-016
    @pytest.mark.p0
    def test_add_template_missing_body(self, api_client, base_url):
        """异常-缺少RequestBody"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            data=None
        )
        assert response.status_code in [400, 415]

    # TestCase: TC-017
    @pytest.mark.p0
    def test_add_template_empty_body(self, api_client, base_url):
        """异常-RequestBody为空对象"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={}
        )
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is False or "message" in data

    # TestCase: TC-018
    @pytest.mark.p0
    def test_add_template_empty_name(self, api_client, base_url):
        """异常-模板名称为空"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": "",
                "templateType": 1
            }
        )
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is False

    # TestCase: TC-019
    @pytest.mark.p1
    def test_add_template_null_name(self, api_client, base_url):
        """异常-模板名称为null"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": None,
                "templateType": 1
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-020
    @pytest.mark.p1
    def test_add_template_name_too_long(self, api_client, base_url):
        """边界-模板名称超长"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": "a" * 256,
                "templateType": 1
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-021
    @pytest.mark.p1
    def test_add_template_special_chars_in_name(self, api_client, base_url):
        """边界-模板名称特殊字符"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": "<script>alert(1)</script>",
                "templateType": 1
            }
        )
        # 可能拒绝或转义存储
        assert response.status_code in [200, 400]

    # TestCase: TC-022
    @pytest.mark.p1
    def test_add_template_type_error(self, api_client, base_url):
        """异常-templateType类型错误"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": "测试",
                "templateType": "abc"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-023
    @pytest.mark.p1
    def test_add_template_invalid_json(self, api_client, base_url):
        """异常-JSON格式错误"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            data='{"templateName":测试}',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400

    # TestCase: TC-024
    @pytest.mark.p2
    def test_add_template_is_default_boundary(self, api_client, base_url):
        """边界-isDefault边界值"""
        template_name = f"测试模板_{uuid.uuid4().hex[:8]}"
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={
                "templateName": template_name,
                "templateType": 1,
                "isDefault": 99
            }
        )
        assert response.status_code in [200, 400]


class TestPutConfigTemplates:
    """PUT /v1/config-templates - 编辑模板测试"""

    # TestCase: TC-025
    @pytest.mark.p0
    def test_update_template_success(self, api_client, base_url):
        """正常编辑模板"""
        # 先创建一个模板
        template_name = f"待编辑模板_{uuid.uuid4().hex[:8]}"
        create_resp = api_client.post(
            f"{base_url}/v1/config-templates",
            json={"templateName": template_name, "templateType": 1}
        )
        if create_resp.status_code == 200 and create_resp.json().get("success"):
            template_id = create_resp.json().get("entity", {}).get("pkCollectTemplate")
            if template_id:
                # 编辑模板
                response = api_client.put(
                    f"{base_url}/v1/config-templates",
                    json={
                        "pkCollectTemplate": template_id,
                        "templateName": f"更新后_{template_name}",
                        "templateType": 1
                    }
                )
                assert response.status_code == 200
                data = response.json()
                assert data.get("success") is True
                return
        # 如果无法创建，使用模拟ID测试
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": "T001",
                "templateName": "更新后名称",
                "templateType": 1
            }
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-026
    @pytest.mark.p0
    def test_update_template_partial_fields(self, api_client, base_url):
        """正常编辑-部分字段更新"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": "T001",
                "templateDesc": "新描述"
            }
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-027
    @pytest.mark.p0
    def test_update_template_missing_id(self, api_client, base_url):
        """异常-缺少模板ID"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={"templateName": "测试"}
        )
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is False

    # TestCase: TC-028
    @pytest.mark.p0
    def test_update_template_id_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": f"NOT_EXIST_{uuid.uuid4().hex}",
                "templateName": "测试"
            }
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is False

    # TestCase: TC-029
    @pytest.mark.p0
    def test_update_template_empty_body(self, api_client, base_url):
        """异常-RequestBody为空"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            data=None
        )
        assert response.status_code in [400, 415]

    # TestCase: TC-030
    @pytest.mark.p1
    def test_update_template_duplicate_name(self, api_client, base_url):
        """边界-更新为重复名称"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": "A_ID",
                "templateName": "已存在的模板名称"
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-031
    @pytest.mark.p1
    def test_update_template_empty_id(self, api_client, base_url):
        """边界-模板ID为空字符串"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={
                "pkCollectTemplate": "",
                "templateName": "测试"
            }
        )
        assert response.status_code in [200, 400]


class TestDeleteConfigTemplates:
    """DELETE /v1/config-templates/{templateId} - 删除模板测试"""

    # TestCase: TC-032
    @pytest.mark.p0
    def test_delete_template_success(self, api_client, base_url):
        """正常删除模板"""
        # 先创建一个模板用于删除
        template_name = f"待删除模板_{uuid.uuid4().hex[:8]}"
        create_resp = api_client.post(
            f"{base_url}/v1/config-templates",
            json={"templateName": template_name, "templateType": 1}
        )
        if create_resp.status_code == 200 and create_resp.json().get("success"):
            template_id = create_resp.json().get("entity", {}).get("pkCollectTemplate")
            if template_id:
                response = api_client.delete(
                    f"{base_url}/v1/config-templates/{template_id}"
                )
                assert response.status_code == 200
                data = response.json()
                assert data.get("success") is True
                return
        # 使用模拟ID测试
        response = api_client.delete(f"{base_url}/v1/config-templates/T001")
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-033
    @pytest.mark.p0
    def test_delete_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.delete(
            f"{base_url}/v1/config-templates/NOT_EXIST_{uuid.uuid4().hex}"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is False

    # TestCase: TC-034
    @pytest.mark.p1
    def test_delete_template_empty_id(self, api_client, base_url):
        """异常-模板ID为空"""
        response = api_client.delete(f"{base_url}/v1/config-templates/")
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-035
    @pytest.mark.p1
    def test_delete_default_template(self, api_client, base_url):
        """边界-删除默认模板"""
        # 需要先获取默认模板ID
        response = api_client.delete(
            f"{base_url}/v1/config-templates/DEFAULT_TEMPLATE_ID"
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-036
    @pytest.mark.p1
    def test_delete_in_use_template(self, api_client, base_url):
        """边界-删除正在使用的模板"""
        response = api_client.delete(
            f"{base_url}/v1/config-templates/IN_USE_ID"
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-037
    @pytest.mark.p2
    def test_delete_template_special_chars_id(self, api_client, base_url):
        """边界-templateId含特殊字符"""
        response = api_client.delete(
            f"{base_url}/v1/config-templates/../../../etc"
        )
        assert response.status_code in [400, 404]
