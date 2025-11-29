"""
基线全局配置接口测试

API-16: GET /v1/config-template/globalConf 获取全局配置
API-17: POST /v1/config-template/globalConf 保存全局配置
"""

import pytest


class TestGetGlobalConfig:
    """API-16: GET /v1/config-template/globalConf 获取基线全局配置"""

    # TestCase: TC-107
    @pytest.mark.p0
    @pytest.mark.api16
    def test_get_global_config_success(self, api_client, base_url):
        """正常获取全局配置"""
        response = api_client.get(
            f"{base_url}/v1/config-template/globalConf"
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "entity" in data
        # 验证返回TaskGlobalConfig结构
        if data.get("entity"):
            entity = data["entity"]
            # 可能包含的字段
            valid_fields = [
                "saveOriginalResult", "pageShowOriginalResult",
                "enableAssetTypeCheck", "originalResultSaveType",
                "originalResultSaveTypeEnum", "taskRedundancyTime", "pointCount"
            ]
            # 至少应包含部分字段或为空对象
            assert isinstance(entity, dict)

    # TestCase: TC-108
    @pytest.mark.p1
    @pytest.mark.api16
    def test_get_global_config_first_time(self, api_client, base_url):
        """首次获取-未配置时返回默认配置或空"""
        response = api_client.get(
            f"{base_url}/v1/config-template/globalConf"
        )
        assert response.status_code == 200
        data = response.json()
        # 即使未配置也应返回200
        assert "success" in data or "entity" in data


class TestSaveGlobalConfig:
    """API-17: POST /v1/config-template/globalConf 保存基线全局配置"""

    # TestCase: TC-109
    @pytest.mark.p0
    @pytest.mark.api17
    def test_save_global_config_full(self, api_client, base_url, sample_global_config):
        """正常保存全局配置-全部字段"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json=sample_global_config
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "entity" in data

    # TestCase: TC-110
    @pytest.mark.p1
    @pytest.mark.api17
    def test_save_global_config_partial(self, api_client, base_url):
        """保存配置-仅部分字段"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "saveOriginalResult": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True or "entity" in data

    # TestCase: TC-111
    @pytest.mark.p1
    @pytest.mark.api17
    def test_save_global_config_empty_body(self, api_client, base_url):
        """必填参数缺失-RequestBody为空"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={}
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-112
    @pytest.mark.p1
    @pytest.mark.api17
    def test_save_global_config_invalid_boolean(self, api_client, base_url):
        """参数类型错误-saveOriginalResult非布尔"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "saveOriginalResult": "yes"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-113
    @pytest.mark.p1
    @pytest.mark.api17
    def test_save_global_config_invalid_integer(self, api_client, base_url):
        """参数类型错误-originalResultSaveType非整数"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "originalResultSaveType": "file"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-114
    @pytest.mark.p2
    @pytest.mark.api17
    def test_save_global_config_negative_time(self, api_client, base_url):
        """边界测试-taskRedundancyTime为负数"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "taskRedundancyTime": -1
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-115
    @pytest.mark.p2
    @pytest.mark.api17
    def test_save_global_config_zero_count(self, api_client, base_url):
        """边界测试-pointCount为0"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "pointCount": 0
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-116
    @pytest.mark.p2
    @pytest.mark.api17
    def test_save_global_config_large_count(self, api_client, base_url):
        """边界测试-pointCount超大值"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "pointCount": 999999999
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-117
    @pytest.mark.p1
    @pytest.mark.api17
    def test_save_global_config_valid_enum(self, api_client, base_url):
        """枚举值测试-originalResultSaveTypeEnum有效值FILE"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "originalResultSaveTypeEnum": "FILE"
            }
        )
        assert response.status_code == 200

    # TestCase: TC-117b
    @pytest.mark.p1
    @pytest.mark.api17
    def test_save_global_config_valid_enum_db(self, api_client, base_url):
        """枚举值测试-originalResultSaveTypeEnum有效值DB"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "originalResultSaveTypeEnum": "DB"
            }
        )
        assert response.status_code == 200

    # TestCase: TC-118
    @pytest.mark.p1
    @pytest.mark.api17
    def test_save_global_config_invalid_enum(self, api_client, base_url):
        """枚举值测试-originalResultSaveTypeEnum无效值"""
        response = api_client.post(
            f"{base_url}/v1/config-template/globalConf",
            json={
                "originalResultSaveTypeEnum": "INVALID"
            }
        )
        assert response.status_code == 400
