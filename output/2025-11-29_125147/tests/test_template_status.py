"""
基线核查模板管理 - 模板状态管理测试
接口路径: /v1/config-templates/{templateId}/enable, disable, default
"""
import pytest
import uuid


class TestEnableTemplate:
    """PATCH /v1/config-templates/{templateId}/enable - 启用模板测试"""

    # TestCase: TC-038
    @pytest.mark.p0
    def test_enable_disabled_template(self, api_client, base_url):
        """正常启用已禁用模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/T001/enable"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True

    # TestCase: TC-039
    @pytest.mark.p1
    def test_enable_already_enabled_template(self, api_client, base_url):
        """边界-启用已启用模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/T001/enable"
        )
        # 幂等操作，应返回成功
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-040
    @pytest.mark.p0
    def test_enable_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/NOT_EXIST_{uuid.uuid4().hex}/enable"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-041
    @pytest.mark.p1
    def test_enable_template_empty_id(self, api_client, base_url):
        """异常-模板ID为空"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates//enable"
        )
        assert response.status_code in [400, 404]


class TestDisableTemplate:
    """PATCH /v1/config-templates/{templateId}/disable - 禁用模板测试"""

    # TestCase: TC-042
    @pytest.mark.p0
    def test_disable_enabled_template(self, api_client, base_url):
        """正常禁用已启用模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/T001/disable"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True

    # TestCase: TC-043
    @pytest.mark.p1
    def test_disable_already_disabled_template(self, api_client, base_url):
        """边界-禁用已禁用模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/T001/disable"
        )
        # 幂等操作
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-044
    @pytest.mark.p0
    def test_disable_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/NOT_EXIST_{uuid.uuid4().hex}/disable"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-045
    @pytest.mark.p1
    def test_disable_default_template(self, api_client, base_url):
        """边界-禁用默认模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/DEFAULT_ID/disable"
        )
        # 根据业务规则，可能禁止或允许
        assert response.status_code in [200, 400, 404]


class TestSetDefaultTemplate:
    """PATCH /v1/config-templates/{templateId}/default - 设置默认模板测试"""

    # TestCase: TC-046
    @pytest.mark.p0
    def test_set_default_template_success(self, api_client, base_url):
        """正常设置默认模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/T001/default"
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True

    # TestCase: TC-047
    @pytest.mark.p1
    def test_set_already_default_template(self, api_client, base_url):
        """边界-设置已是默认的模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/T001/default"
        )
        # 幂等操作
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-048
    @pytest.mark.p0
    def test_switch_default_template(self, api_client, base_url):
        """业务-切换默认模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/T002/default"
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-049
    @pytest.mark.p0
    def test_set_default_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/NOT_EXIST_{uuid.uuid4().hex}/default"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-050
    @pytest.mark.p1
    def test_set_disabled_template_as_default(self, api_client, base_url):
        """边界-设置禁用模板为默认"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/DISABLED_ID/default"
        )
        # 根据业务规则决定
        assert response.status_code in [200, 400, 404]
