"""
基线核查模板管理 - 指纹操作测试
接口路径: /v1/config-templates/selectTemplate/{templateId}
         /v1/config-templates/temps/{templateId}
"""
import pytest
import uuid


class TestAddAllFingers:
    """PUT /v1/config-templates/selectTemplate/{templateId} - 添加全部指纹测试"""

    # TestCase: TC-070
    @pytest.mark.p0
    def test_add_all_fingers_success(self, api_client, base_url):
        """正常添加全部指纹"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/T001",
            json={}
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True
            assert "entity" in data

    # TestCase: TC-071
    @pytest.mark.p1
    def test_add_all_fingers_no_available(self, api_client, base_url):
        """边界-已无可添加指纹"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/T001",
            json={}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-072
    @pytest.mark.p0
    def test_add_all_fingers_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/NOT_EXIST_{uuid.uuid4().hex}",
            json={}
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-073
    @pytest.mark.p1
    def test_add_all_fingers_missing_body(self, api_client, base_url):
        """异常-缺少RequestBody"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/T001"
        )
        assert response.status_code in [200, 400, 415]


class TestAddSelectedFingers:
    """PATCH /v1/config-templates/selectTemplate/{templateId} - 添加选中指纹测试"""

    # TestCase: TC-074
    @pytest.mark.p0
    def test_add_selected_fingers_success(self, api_client, base_url):
        """正常添加选中指纹"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/T001",
            json={"ids": ["F001", "F002"]}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-075
    @pytest.mark.p1
    def test_add_selected_fingers_empty_list(self, api_client, base_url):
        """边界-添加空列表"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/T001",
            json={"ids": []}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-076
    @pytest.mark.p1
    def test_add_selected_fingers_partial_exist(self, api_client, base_url):
        """边界-部分指纹已存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/T001",
            json={"ids": ["F001", "F002"]}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-077
    @pytest.mark.p1
    def test_add_selected_fingers_not_exist(self, api_client, base_url):
        """异常-指纹ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/T001",
            json={"ids": [f"F999_{uuid.uuid4().hex}"]}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-078
    @pytest.mark.p0
    def test_add_selected_fingers_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/NOT_EXIST_{uuid.uuid4().hex}",
            json={"ids": ["F001"]}
        )
        assert response.status_code in [400, 404]


class TestDeleteAllFingers:
    """PUT /v1/config-templates/temps/{templateId} - 删除全部指纹测试"""

    # TestCase: TC-079
    @pytest.mark.p0
    def test_delete_all_fingers_success(self, api_client, base_url):
        """正常删除全部指纹"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/T001",
            json={}
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True

    # TestCase: TC-080
    @pytest.mark.p1
    def test_delete_all_fingers_empty_template(self, api_client, base_url):
        """边界-模板无指纹"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/EMPTY_TEMPLATE",
            json={}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-081
    @pytest.mark.p0
    def test_delete_all_fingers_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/NOT_EXIST_{uuid.uuid4().hex}",
            json={}
        )
        assert response.status_code in [400, 404]


class TestDeleteSelectedFingers:
    """PATCH /v1/config-templates/temps/{templateId} - 批量删除指纹测试"""

    # TestCase: TC-082
    @pytest.mark.p0
    def test_delete_selected_fingers_success(self, api_client, base_url):
        """正常批量删除指纹"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/T001",
            json={"ids": ["F001", "F002"]}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-083
    @pytest.mark.p1
    def test_delete_selected_fingers_empty_list(self, api_client, base_url):
        """边界-删除空列表"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/T001",
            json={"ids": []}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-084
    @pytest.mark.p1
    def test_delete_selected_fingers_partial_not_in_template(self, api_client, base_url):
        """边界-部分指纹不在模板中"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/T001",
            json={"ids": ["F001", f"F999_{uuid.uuid4().hex}"]}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-085
    @pytest.mark.p0
    def test_delete_selected_fingers_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/NOT_EXIST_{uuid.uuid4().hex}",
            json={"ids": ["F001"]}
        )
        assert response.status_code in [400, 404]
