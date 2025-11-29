"""
基线核查模板管理 - 指纹选择查询测试
接口路径: /v1/config-templates/choose
"""
import pytest


class TestQueryFingerChoose:
    """GET /v1/config-templates/choose - 指纹分页列表（已选/未选）测试"""

    # TestCase: TC-063
    @pytest.mark.p0
    def test_query_selected_fingers(self, api_client, base_url):
        """正常查询-已选指纹"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"tempId": "T001", "selected": "1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)

    # TestCase: TC-064
    @pytest.mark.p0
    def test_query_unselected_fingers(self, api_client, base_url):
        """正常查询-未选指纹"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"tempId": "T001", "selected": "0"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)

    # TestCase: TC-065
    @pytest.mark.p0
    def test_query_fingers_with_pagination(self, api_client, base_url):
        """正常查询-带分页"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"tempId": "T001", "page": 1, "perPage": 20}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "totalCount" in data

    # TestCase: TC-066
    @pytest.mark.p1
    def test_query_fingers_by_finger_type(self, api_client, base_url):
        """正常查询-按指纹类型筛选"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"tempId": "T001", "fingerType": "baseline"}
        )
        assert response.status_code == 200

    # TestCase: TC-067
    @pytest.mark.p1
    def test_query_fingers_by_asset_type(self, api_client, base_url):
        """正常查询-按资产类型筛选"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"tempId": "T001", "assetTypeCode": "linux"}
        )
        assert response.status_code == 200

    # TestCase: TC-068
    @pytest.mark.p1
    def test_query_fingers_by_check_item_name(self, api_client, base_url):
        """正常查询-按检查项名称搜索"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"tempId": "T001", "checkItemName": "SSH"}
        )
        assert response.status_code == 200

    # TestCase: TC-069
    @pytest.mark.p2
    def test_query_fingers_without_temp_id(self, api_client, base_url):
        """边界-不传tempId"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"selected": "1"}
        )
        # 可能返回所有或报错
        assert response.status_code in [200, 400]
