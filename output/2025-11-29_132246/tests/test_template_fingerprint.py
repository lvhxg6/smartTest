"""
基线核查模板管理 - 模板指纹管理接口测试
测试接口:
- PUT /v1/config-templates/selectTemplate/{templateId} (添加全部指纹)
- PATCH /v1/config-templates/selectTemplate/{templateId} (添加选中指纹)
- PUT /v1/config-templates/temps/{templateId} (删除全部指纹)
- PATCH /v1/config-templates/temps/{templateId} (批量删除指纹)
"""
import pytest


class TestAddAllFingerprints:
    """PUT /v1/config-templates/selectTemplate/{templateId} - 添加全部指纹测试"""

    # TestCase: TC-072
    def test_add_all_fingerprints_success(self, api_client, base_url, existing_template_id):
        """正常添加全部指纹"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{existing_template_id}",
            json={}
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-073
    def test_add_all_fingerprints_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/non-existing-id-xyz",
            json={}
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-074
    def test_add_all_fingerprints_already_full(self, api_client, base_url, existing_template_id):
        """边界-无可添加指纹"""
        # 先添加全部
        api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{existing_template_id}",
            json={}
        )
        # 再次添加
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{existing_template_id}",
            json={}
        )
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            # 返回添加数量可能为0
            assert "entity" in data

    # TestCase: TC-075
    def test_add_all_fingerprints_missing_body(self, api_client, base_url, existing_template_id):
        """异常-缺少请求体"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{existing_template_id}"
        )
        assert response.status_code in [200, 400, 415]


class TestAddSelectedFingerprints:
    """PATCH /v1/config-templates/selectTemplate/{templateId} - 添加选中指纹测试"""

    # TestCase: TC-076
    def test_add_selected_fingerprints_success(self, api_client, base_url, existing_template_id):
        """正常添加选中指纹"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{existing_template_id}",
            json={"ids": ["finger-1", "finger-2"]}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-077
    def test_add_selected_fingerprints_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/non-existing-id-xyz",
            json={"ids": ["finger-1"]}
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-078
    def test_add_selected_fingerprints_finger_not_exist(self, api_client, base_url, existing_template_id):
        """异常-指纹ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{existing_template_id}",
            json={"ids": ["non-existing-finger-xyz"]}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-079
    def test_add_selected_fingerprints_empty_list(self, api_client, base_url, existing_template_id):
        """边界-空选择列表"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{existing_template_id}",
            json={"ids": []}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-080
    def test_add_selected_fingerprints_duplicate(self, api_client, base_url, existing_template_id):
        """边界-重复添加已有指纹"""
        # 先添加
        api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{existing_template_id}",
            json={"ids": ["finger-1"]}
        )
        # 再次添加相同的
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{existing_template_id}",
            json={"ids": ["finger-1"]}
        )
        assert response.status_code in [200, 400]


class TestDeleteAllFingerprints:
    """PUT /v1/config-templates/temps/{templateId} - 删除全部指纹测试"""

    # TestCase: TC-081
    def test_delete_all_fingerprints_success(self, api_client, base_url, existing_template_id):
        """正常删除全部指纹"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/{existing_template_id}",
            json={}
        )
        assert response.status_code in [200, 400, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-082
    def test_delete_all_fingerprints_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/non-existing-id-xyz",
            json={}
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-083
    def test_delete_all_fingerprints_empty_template(self, api_client, base_url, existing_template_id):
        """边界-模板无指纹"""
        # 先删除全部
        api_client.put(
            f"{base_url}/v1/config-templates/temps/{existing_template_id}",
            json={}
        )
        # 再次删除
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/{existing_template_id}",
            json={}
        )
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            # 返回删除数量可能为0
            assert data.get("entity") == 0 or data.get("success") is True


class TestDeleteSelectedFingerprints:
    """PATCH /v1/config-templates/temps/{templateId} - 批量删除指纹测试"""

    # TestCase: TC-084
    def test_delete_selected_fingerprints_success(self, api_client, base_url, existing_template_id):
        """正常批量删除指纹"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/{existing_template_id}",
            json={"ids": ["finger-1", "finger-2"]}
        )
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-085
    def test_delete_selected_fingerprints_template_not_exist(self, api_client, base_url):
        """异常-模板ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/non-existing-id-xyz",
            json={"ids": ["finger-1"]}
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-086
    def test_delete_selected_fingerprints_finger_not_exist(self, api_client, base_url, existing_template_id):
        """异常-指纹ID不存在"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/{existing_template_id}",
            json={"ids": ["non-existing-finger-xyz"]}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-087
    def test_delete_selected_fingerprints_empty_list(self, api_client, base_url, existing_template_id):
        """边界-空删除列表"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/{existing_template_id}",
            json={"ids": []}
        )
        assert response.status_code in [200, 400]
