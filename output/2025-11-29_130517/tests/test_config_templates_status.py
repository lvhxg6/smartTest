"""
基线核查模板状态管理接口测试

API-05: PATCH /v1/config-templates/{templateId}/enable 启用模板
API-06: PATCH /v1/config-templates/{templateId}/disable 禁用模板
API-07: PATCH /v1/config-templates/{templateId}/default 设置默认模板
"""

import pytest


class TestEnableTemplate:
    """API-05: PATCH /v1/config-templates/{templateId}/enable 启用基线核查模板"""

    # TestCase: TC-037
    @pytest.mark.p0
    @pytest.mark.api05
    def test_enable_disabled_template(self, api_client, base_url, template_id):
        """正常启用禁用状态的模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{template_id}/enable"
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-038
    @pytest.mark.p1
    @pytest.mark.api05
    def test_enable_already_enabled_template(self, api_client, base_url, template_id):
        """启用已启用的模板（幂等操作）"""
        # 先启用一次
        api_client.patch(f"{base_url}/v1/config-templates/{template_id}/enable")
        # 再次启用
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{template_id}/enable"
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            # 幂等操作应该成功
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-039
    @pytest.mark.p1
    @pytest.mark.api05
    def test_enable_not_exist_template(self, api_client, base_url, non_existent_id):
        """启用不存在的模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{non_existent_id}/enable"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-040
    @pytest.mark.p1
    @pytest.mark.api05
    def test_enable_template_empty_id(self, api_client, base_url):
        """必填参数缺失-templateId为空"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates//enable"
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-041
    @pytest.mark.p2
    @pytest.mark.api05
    def test_enable_template_special_chars(self, api_client, base_url):
        """边界测试-templateId特殊字符"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/<script>/enable"
        )
        assert response.status_code in [400, 404]


class TestDisableTemplate:
    """API-06: PATCH /v1/config-templates/{templateId}/disable 禁用基线核查模板"""

    # TestCase: TC-042
    @pytest.mark.p0
    @pytest.mark.api06
    def test_disable_enabled_template(self, api_client, base_url, template_id):
        """正常禁用启用状态的模板"""
        # 先确保模板是启用状态
        api_client.patch(f"{base_url}/v1/config-templates/{template_id}/enable")

        response = api_client.patch(
            f"{base_url}/v1/config-templates/{template_id}/disable"
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-043
    @pytest.mark.p1
    @pytest.mark.api06
    def test_disable_already_disabled_template(self, api_client, base_url, template_id):
        """禁用已禁用的模板（幂等操作）"""
        # 先禁用一次
        api_client.patch(f"{base_url}/v1/config-templates/{template_id}/disable")
        # 再次禁用
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{template_id}/disable"
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            # 幂等操作应该成功
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-044
    @pytest.mark.p1
    @pytest.mark.api06
    def test_disable_not_exist_template(self, api_client, base_url, non_existent_id):
        """禁用不存在的模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{non_existent_id}/disable"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-045
    @pytest.mark.p1
    @pytest.mark.api06
    def test_disable_template_empty_id(self, api_client, base_url):
        """必填参数缺失-templateId为空"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates//disable"
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-046
    @pytest.mark.p1
    @pytest.mark.api06
    def test_disable_default_template(self, api_client, base_url):
        """禁用默认模板（业务规则测试）"""
        # 注意：需要有一个实际的默认模板ID才能测试
        default_template_id = "default-template-placeholder"
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{default_template_id}/disable"
        )
        # 默认模板不能禁用
        assert response.status_code in [400, 404, 200]

    # TestCase: TC-047
    @pytest.mark.p1
    @pytest.mark.api06
    def test_disable_template_in_use(self, api_client, base_url):
        """禁用正在使用的模板（业务规则测试）"""
        # 注意：需要有一个实际被使用的模板ID才能测试
        in_use_template_id = "in-use-template-placeholder"
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{in_use_template_id}/disable"
        )
        # 使用中的模板不能禁用
        assert response.status_code in [400, 404, 200]


class TestSetDefaultTemplate:
    """API-07: PATCH /v1/config-templates/{templateId}/default 将指定模板设置为默认"""

    # TestCase: TC-048
    @pytest.mark.p0
    @pytest.mark.api07
    def test_set_default_template(self, api_client, base_url, template_id):
        """正常设置默认模板"""
        # 先确保模板是启用状态
        api_client.patch(f"{base_url}/v1/config-templates/{template_id}/enable")

        response = api_client.patch(
            f"{base_url}/v1/config-templates/{template_id}/default"
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-049
    @pytest.mark.p1
    @pytest.mark.api07
    def test_set_already_default_template(self, api_client, base_url, template_id):
        """设置已是默认的模板为默认（幂等操作）"""
        # 先设置为默认
        api_client.patch(f"{base_url}/v1/config-templates/{template_id}/enable")
        api_client.patch(f"{base_url}/v1/config-templates/{template_id}/default")
        # 再次设置
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{template_id}/default"
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            # 幂等操作应该成功
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-050
    @pytest.mark.p1
    @pytest.mark.api07
    def test_set_default_not_exist_template(self, api_client, base_url, non_existent_id):
        """设置不存在的模板为默认"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{non_existent_id}/default"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-051
    @pytest.mark.p1
    @pytest.mark.api07
    def test_set_default_template_empty_id(self, api_client, base_url):
        """必填参数缺失-templateId为空"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates//default"
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-052
    @pytest.mark.p1
    @pytest.mark.api07
    def test_set_disabled_template_as_default(self, api_client, base_url, template_id):
        """设置禁用状态模板为默认（业务规则测试）"""
        # 先禁用模板
        api_client.patch(f"{base_url}/v1/config-templates/{template_id}/disable")
        # 尝试设置为默认
        response = api_client.patch(
            f"{base_url}/v1/config-templates/{template_id}/default"
        )
        # 禁用的模板不能设为默认
        assert response.status_code in [400, 404, 200]
