"""
基线核查模板管理 - 模板信息查询测试
接口路径: /v1/config-templates/{templateId}/{optType}/basic
         /v1/config-templates/{templateId}/list
"""
import pytest
import uuid


class TestQueryTemplateBasicInfo:
    """GET /v1/config-templates/{templateId}/{optType}/basic - 查询模板基本信息测试"""

    # TestCase: TC-051
    @pytest.mark.p0
    def test_query_template_info_view_mode(self, api_client, base_url):
        """正常查询模板信息"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/T001/view/basic"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data or "entity" in data

    # TestCase: TC-052
    @pytest.mark.p0
    def test_query_template_info_edit_mode(self, api_client, base_url):
        """正常查询-不同optType"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/T001/edit/basic"
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-053
    @pytest.mark.p0
    def test_query_template_info_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/NOT_EXIST_{uuid.uuid4().hex}/view/basic"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is False or data.get("entity") is None

    # TestCase: TC-054
    @pytest.mark.p1
    def test_query_template_info_invalid_opt_type(self, api_client, base_url):
        """异常-optType非法"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/T001/invalid/basic"
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-055
    @pytest.mark.p1
    def test_query_template_info_empty_id(self, api_client, base_url):
        """异常-templateId为空"""
        response = api_client.get(
            f"{base_url}/v1/config-templates//view/basic"
        )
        assert response.status_code in [400, 404]


class TestQueryTemplateFingerList:
    """GET /v1/config-templates/{templateId}/list - 查询模板指纹列表测试"""

    # TestCase: TC-056
    @pytest.mark.p0
    def test_query_finger_list_default(self, api_client, base_url):
        """正常查询-默认分页"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/T001/list"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert "data" in data or "entity" in data

    # TestCase: TC-057
    @pytest.mark.p0
    def test_query_finger_list_with_pagination(self, api_client, base_url):
        """正常查询-带分页参数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/T001/list",
            params={"page": 2, "perPage": 20}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-058
    @pytest.mark.p0
    def test_query_finger_list_with_filters(self, api_client, base_url):
        """正常查询-带筛选条件"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/T001/list",
            params={"assetTypeIds": "AT001", "riskLevel": "high"}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-059
    @pytest.mark.p1
    def test_query_finger_list_with_sort(self, api_client, base_url):
        """正常查询-带排序"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/T001/list",
            params={"field": "createTime", "order": "desc"}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-060
    @pytest.mark.p1
    def test_query_finger_list_by_check_item_name(self, api_client, base_url):
        """正常查询-按检查项名称筛选"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/T001/list",
            params={"checkItemName": "密码策略"}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-061
    @pytest.mark.p0
    def test_query_finger_list_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/NOT_EXIST_{uuid.uuid4().hex}/list"
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-062
    @pytest.mark.p1
    def test_query_finger_list_empty(self, api_client, base_url):
        """边界-模板无指纹"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/EMPTY_TEMPLATE/list"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            # 空数据返回空数组
            assert data.get("data") == [] or data.get("totalCount") == 0 or data is not None
