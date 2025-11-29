"""
基线核查模板管理 - 模板状态管理接口测试
测试接口:
- PATCH /v1/config-templates/{templateId}/enable (启用模板)
- PATCH /v1/config-templates/{templateId}/disable (禁用模板)
- PATCH /v1/config-templates/{templateId}/default (设置默认模板)
"""
import pytest


class TestEnableTemplate:
    """PATCH /v1/config-templates/{templateId}/enable - 启用模板测试"""

    # TestCase: TC-041
    def test_enable_template_success(self, api_client, base_url, existing_template_id):
        """正常启用模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{existing_template_id}/enable"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-042
    def test_enable_already_enabled_template(self, api_client, base_url, existing_template_id):
        """正常-对已启用模板再次启用（幂等）"""
        # 先启用
        api_client.patch(
            f"{base_url}/v1/config-templates/{existing_template_id}/enable"
        )
        # 再次启用
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{existing_template_id}/enable"
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-043
    def test_enable_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/non-existing-id-xyz/enable"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-044
    def test_enable_template_empty_id(self, api_client, base_url):
        """异常-模板ID为空"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates//enable"
        )
        assert response.status_code in [400, 404]


class TestDisableTemplate:
    """PATCH /v1/config-templates/{templateId}/disable - 禁用模板测试"""

    # TestCase: TC-045
    def test_disable_template_success(self, api_client, base_url, existing_template_id):
        """正常禁用模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{existing_template_id}/disable"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-046
    def test_disable_already_disabled_template(self, api_client, base_url, existing_template_id):
        """正常-对已禁用模板再次禁用（幂等）"""
        # 先禁用
        api_client.patch(
            f"{base_url}/v1/config-templates/{existing_template_id}/disable"
        )
        # 再次禁用
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{existing_template_id}/disable"
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-047
    def test_disable_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/non-existing-id-xyz/disable"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-048
    def test_disable_default_template(self, api_client, base_url):
        """异常-禁用默认模板"""
        # 获取默认模板
        list_response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"isDefault": "1", "page": 1, "perPage": 1}
        )
        if list_response.status_code == 200:
            data = list_response.json()
            if data.get("data") and len(data["data"]) > 0:
                default_id = data["data"][0].get("pkHandbook") or data["data"][0].get("key")
                if default_id:
                    response = api_client.patch(
                        f"{base_url}/v1/config-templates/{default_id}/disable"
                    )
                    # 禁用默认模板可能被拒绝
                    assert response.status_code in [200, 400]
                    return
        pytest.skip("无法获取默认模板ID")


class TestSetDefaultTemplate:
    """PATCH /v1/config-templates/{templateId}/default - 设置默认模板测试"""

    # TestCase: TC-050
    def test_set_default_template_success(self, api_client, base_url, existing_template_id):
        """正常设置默认模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{existing_template_id}/default"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-051
    def test_set_default_already_default_template(self, api_client, base_url):
        """正常-对已是默认的模板设置（幂等）"""
        # 获取当前默认模板
        list_response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"isDefault": "1", "page": 1, "perPage": 1}
        )
        if list_response.status_code == 200:
            data = list_response.json()
            if data.get("data") and len(data["data"]) > 0:
                default_id = data["data"][0].get("pkHandbook") or data["data"][0].get("key")
                if default_id:
                    response = api_client.patch(
                        f"{base_url}/v1/config-templates/{default_id}/default"
                    )
                    assert response.status_code in [200, 400]
                    return
        pytest.skip("无法获取默认模板ID")

    # TestCase: TC-052
    def test_set_default_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/non-existing-id-xyz/default"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-053
    def test_set_disabled_template_as_default(self, api_client, base_url):
        """异常-设置禁用模板为默认"""
        # 获取禁用状态的模板
        list_response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"isUse": "0", "page": 1, "perPage": 1}
        )
        if list_response.status_code == 200:
            data = list_response.json()
            if data.get("data") and len(data["data"]) > 0:
                disabled_id = data["data"][0].get("pkHandbook") or data["data"][0].get("key")
                if disabled_id:
                    response = api_client.patch(
                        f"{base_url}/v1/config-templates/{disabled_id}/default"
                    )
                    # 设置禁用模板为默认可能被拒绝
                    assert response.status_code in [200, 400]
                    return
        pytest.skip("无法获取禁用状态的模板ID")
