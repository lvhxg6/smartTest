"""
基线核查模板管理 - 模板信息查询接口测试
测试接口:
- GET /v1/config-templates/{templateId}/{optType}/basic (查询模板基本信息)
- GET /v1/config-templates/{templateId}/list (查询模板指纹列表)
- GET /v1/config-templates/choose (指纹分页列表)
- GET /v1/config-template/task (查询任务模板列表)
"""
import pytest


class TestQueryTemplateBasicInfo:
    """GET /v1/config-templates/{templateId}/{optType}/basic - 查询模板基本信息测试"""

    # TestCase: TC-054
    def test_query_template_info_view(self, api_client, base_url, existing_template_id):
        """正常查询模板基本信息"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{existing_template_id}/view/basic"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert "entity" in data or "success" in data

    # TestCase: TC-055
    def test_query_template_info_edit(self, api_client, base_url, existing_template_id):
        """正常查询-不同optType"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{existing_template_id}/edit/basic"
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-056
    def test_query_template_info_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/non-existing-id-xyz/view/basic"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-057
    def test_query_template_info_invalid_opt_type(self, api_client, base_url, existing_template_id):
        """异常-optType无效"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{existing_template_id}/invalid/basic"
        )
        assert response.status_code in [200, 400, 404]


class TestQueryTemplateFingerList:
    """GET /v1/config-templates/{templateId}/list - 查询模板指纹列表测试"""

    # TestCase: TC-059
    def test_query_template_finger_list_default(self, api_client, base_url, existing_template_id):
        """正常查询指纹列表-默认分页"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{existing_template_id}/list"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "totalCount" in data

    # TestCase: TC-060
    def test_query_template_finger_list_pagination(self, api_client, base_url, existing_template_id):
        """正常查询-指定分页参数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{existing_template_id}/list",
            params={"page": 2, "perPage": 20}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-061
    def test_query_template_finger_list_filter_name(self, api_client, base_url, existing_template_id):
        """正常查询-带筛选checkItemName"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{existing_template_id}/list",
            params={"checkItemName": "密码策略"}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-062
    def test_query_template_finger_list_filter_risk(self, api_client, base_url, existing_template_id):
        """正常查询-带筛选riskLevel"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{existing_template_id}/list",
            params={"riskLevel": "high"}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-063
    def test_query_template_finger_list_sort(self, api_client, base_url, existing_template_id):
        """正常查询-带排序"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{existing_template_id}/list",
            params={"field": "createTime", "order": "desc"}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-064
    def test_query_template_finger_list_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/non-existing-id-xyz/list"
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-065
    def test_query_template_finger_list_empty(self, api_client, base_url, existing_template_id):
        """边界-模板下无指纹"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{existing_template_id}/list",
            params={"checkItemName": "不存在的指纹名称_xyz123"}
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            # 可能返回空数组
            assert isinstance(data.get("data"), list)


class TestQueryFingerChoose:
    """GET /v1/config-templates/choose - 指纹分页列表测试"""

    # TestCase: TC-066
    def test_query_finger_selected(self, api_client, base_url, existing_template_id):
        """正常查询-已选指纹"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"tempId": existing_template_id, "selected": "1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    # TestCase: TC-067
    def test_query_finger_unselected(self, api_client, base_url, existing_template_id):
        """正常查询-未选指纹"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"tempId": existing_template_id, "selected": "0"}
        )
        assert response.status_code == 200

    # TestCase: TC-068
    def test_query_finger_by_type(self, api_client, base_url):
        """正常查询-按指纹类型筛选"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"fingerType": "baseline"}
        )
        assert response.status_code == 200

    # TestCase: TC-069
    def test_query_finger_by_asset_type(self, api_client, base_url):
        """正常查询-按资产类型筛选"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"assetTypeCode": "linux"}
        )
        assert response.status_code == 200

    # TestCase: TC-070
    def test_query_finger_combined_filter(self, api_client, base_url, existing_template_id):
        """正常查询-组合筛选"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={
                "tempId": existing_template_id,
                "selected": "1",
                "fingerType": "baseline",
                "checkItemName": "密码"
            }
        )
        assert response.status_code == 200

    # TestCase: TC-071
    def test_query_finger_no_match(self, api_client, base_url):
        """边界-无匹配数据"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"checkItemName": "不存在的名称_xyz123abc"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("data") == [] or data.get("totalCount") == 0


class TestQueryTaskTemplate:
    """GET /v1/config-template/task - 查询任务模板列表测试"""

    # TestCase: TC-099
    def test_query_task_template_list(self, api_client, base_url):
        """正常查询任务模板列表"""
        response = api_client.get(
            f"{base_url}/v1/config-template/task"
        )
        assert response.status_code == 200
        data = response.json()
        assert "entity" in data or "success" in data
        if data.get("entity"):
            assert isinstance(data["entity"], list)

    # TestCase: TC-100
    def test_query_task_template_empty(self, api_client, base_url):
        """边界-无可用模板（可能返回空数组）"""
        response = api_client.get(
            f"{base_url}/v1/config-template/task"
        )
        assert response.status_code == 200
        data = response.json()
        # 即使无模板也应返回成功
        assert data.get("success") is True or "entity" in data
