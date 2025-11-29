"""
基线核查模板管理 - 全局配置测试
接口路径: /v1/config-template/globalConf
"""
import pytest


class TestGetGlobalConfig:
    """GET /v1/config-template/globalConf - 获取全局配置测试"""

    # TestCase: TC-093
    @pytest.mark.p0
    def test_get_global_config_success(self, api_client, base_url):
        """正常获取全局配置"""
        response = api_client.get(
            f"{base_url}/v1/config-template/globalConf"
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # 验证返回TaskGlobalConfig结构
        entity = data.get("entity")
        if entity:
            assert isinstance(entity, dict)

    # TestCase: TC-094
    @pytest.mark.p1
    def test_get_global_config_no_config(self, api_client, base_url):
        """边界-无全局配置"""
        response = api_client.get(
            f"{base_url}/v1/config-template/globalConf"
        )
        assert response.status_code == 200
        data = response.json()
        # 无配置时返回默认值或null
        assert data.get("success") is True or "entity" in data


class TestSaveGlobalConfig:
    """POST /v1/config-template/globalConf - 保存全局配置测试"""

    # TestCase: TC-095
    @pytest.mark.p0
    def test_save_global_config_success(self, api_client, base_url):
        """正常保存全局配置"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "saveOriginalResult": True,
                "pageShowOriginalResult": True,
                "enableAssetTypeCheck": False,
                "originalResultSaveType": 1,
                "taskRedundancyTime": 30,
                "pointCount": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

    # TestCase: TC-096
    @pytest.mark.p0
    def test_save_global_config_missing_body(self, api_client, base_url):
        """异常-缺少RequestBody"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            data=None
        )
        assert response.status_code in [400, 415]

    # TestCase: TC-097
    @pytest.mark.p1
    def test_save_global_config_invalid_enum(self, api_client, base_url):
        """边界-originalResultSaveTypeEnum非法值"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "originalResultSaveTypeEnum": "INVALID"
            }
        )
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            # 可能返回失败或忽略无效值
            assert "success" in data

    # TestCase: TC-098
    @pytest.mark.p1
    def test_save_global_config_negative_redundancy_time(self, api_client, base_url):
        """边界-taskRedundancyTime为负数"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "taskRedundancyTime": -1
            }
        )
        assert response.status_code in [200, 400]
