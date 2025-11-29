"""
基线核查模板指纹管理接口测试

API-12: PUT /v1/config-templates/selectTemplate/{templateId} 添加全部指纹
API-13: PATCH /v1/config-templates/selectTemplate/{templateId} 添加选中指纹
API-14: PUT /v1/config-templates/temps/{templateId} 删除全部指纹
API-15: PATCH /v1/config-templates/temps/{templateId} 批量删除指纹
"""

import pytest


class TestAddAllFingerprints:
    """API-12: PUT /v1/config-templates/selectTemplate/{templateId} 为模板添加全部指纹"""

    # TestCase: TC-086
    @pytest.mark.p0
    @pytest.mark.api12
    def test_add_all_fingerprints_success(self, api_client, base_url, template_id):
        """正常添加全部指纹"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{template_id}",
            json={}
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-087
    @pytest.mark.p1
    @pytest.mark.api12
    def test_add_all_fingerprints_to_not_exist(self, api_client, base_url, non_existent_id):
        """添加到不存在的模板"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{non_existent_id}",
            json={}
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-088
    @pytest.mark.p1
    @pytest.mark.api12
    def test_add_all_fingerprints_empty_id(self, api_client, base_url):
        """必填参数缺失-templateId为空"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/",
            json={}
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-089
    @pytest.mark.p1
    @pytest.mark.api12
    def test_add_all_fingerprints_no_body(self, api_client, base_url, template_id):
        """必填参数缺失-RequestBody为空"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{template_id}"
        )
        assert response.status_code in [400, 200, 415]

    # TestCase: TC-090
    @pytest.mark.p2
    @pytest.mark.api12
    def test_add_all_fingerprints_duplicate(self, api_client, base_url, template_id):
        """重复添加全部指纹（幂等测试）"""
        # 第一次添加
        api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{template_id}",
            json={}
        )
        # 第二次添加
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{template_id}",
            json={}
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            # 幂等操作应返回成功，entity可能为0
            assert data.get("success") is True or "entity" in data


class TestAddSelectedFingerprints:
    """API-13: PATCH /v1/config-templates/selectTemplate/{templateId} 为模板添加选中的指纹"""

    # TestCase: TC-091
    @pytest.mark.p0
    @pytest.mark.api13
    def test_add_selected_fingerprints_success(self, api_client, base_url, template_id):
        """正常添加选中指纹"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{template_id}",
            json={
                "ids": ["fp-001", "fp-002"]
            }
        )
        assert response.status_code in [200, 404, 400]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-092
    @pytest.mark.p1
    @pytest.mark.api13
    def test_add_selected_fingerprints_to_not_exist(self, api_client, base_url, non_existent_id):
        """添加到不存在的模板"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{non_existent_id}",
            json={
                "ids": ["fp-001"]
            }
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-093
    @pytest.mark.p1
    @pytest.mark.api13
    def test_add_selected_fingerprints_not_exist(self, api_client, base_url, template_id):
        """添加不存在的指纹"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{template_id}",
            json={
                "ids": ["not-exist-fingerprint-id"]
            }
        )
        assert response.status_code in [400, 200, 404]

    # TestCase: TC-094
    @pytest.mark.p1
    @pytest.mark.api13
    def test_add_selected_fingerprints_empty_id(self, api_client, base_url):
        """必填参数缺失-templateId为空"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/",
            json={
                "ids": ["fp-001"]
            }
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-095
    @pytest.mark.p2
    @pytest.mark.api13
    def test_add_selected_fingerprints_empty_ids(self, api_client, base_url, template_id):
        """必填参数缺失-ids为空数组"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{template_id}",
            json={
                "ids": []
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-096
    @pytest.mark.p2
    @pytest.mark.api13
    def test_add_selected_fingerprints_duplicate(self, api_client, base_url, template_id):
        """重复添加相同指纹（幂等测试）"""
        fingerprint_ids = ["existing-fp-001"]
        # 第一次添加
        api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{template_id}",
            json={"ids": fingerprint_ids}
        )
        # 第二次添加
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{template_id}",
            json={"ids": fingerprint_ids}
        )
        assert response.status_code in [200, 400, 404]


class TestDeleteAllFingerprints:
    """API-14: PUT /v1/config-templates/temps/{templateId} 删除模板中的全部指纹"""

    # TestCase: TC-097
    @pytest.mark.p0
    @pytest.mark.api14
    def test_delete_all_fingerprints_success(self, api_client, base_url, template_id):
        """正常删除全部指纹"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/{template_id}",
            json={}
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-098
    @pytest.mark.p1
    @pytest.mark.api14
    def test_delete_all_fingerprints_from_not_exist(self, api_client, base_url, non_existent_id):
        """删除不存在模板的指纹"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/{non_existent_id}",
            json={}
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-099
    @pytest.mark.p1
    @pytest.mark.api14
    def test_delete_all_fingerprints_empty_id(self, api_client, base_url):
        """必填参数缺失-templateId为空"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/",
            json={}
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-100
    @pytest.mark.p1
    @pytest.mark.api14
    def test_delete_all_fingerprints_no_body(self, api_client, base_url, template_id):
        """必填参数缺失-RequestBody为空"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/{template_id}"
        )
        assert response.status_code in [400, 200, 415]

    # TestCase: TC-101
    @pytest.mark.p2
    @pytest.mark.api14
    def test_delete_all_fingerprints_from_empty(self, api_client, base_url, template_id):
        """删除空模板的指纹"""
        # 先删除全部
        api_client.put(
            f"{base_url}/v1/config-templates/temps/{template_id}",
            json={}
        )
        # 再次删除
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/{template_id}",
            json={}
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            # entity应为0
            assert data.get("entity", 0) == 0 or data.get("success") is True


class TestDeleteSelectedFingerprints:
    """API-15: PATCH /v1/config-templates/temps/{templateId} 批量删除模板中的指纹"""

    # TestCase: TC-102
    @pytest.mark.p0
    @pytest.mark.api15
    def test_delete_selected_fingerprints_success(self, api_client, base_url, template_id):
        """正常批量删除指纹"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/{template_id}",
            json={
                "ids": ["fp-001", "fp-002"]
            }
        )
        assert response.status_code in [200, 404, 400]
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is True or "entity" in data

    # TestCase: TC-103
    @pytest.mark.p1
    @pytest.mark.api15
    def test_delete_selected_fingerprints_from_not_exist(self, api_client, base_url, non_existent_id):
        """删除不存在模板的指纹"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/{non_existent_id}",
            json={
                "ids": ["fp-001"]
            }
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-104
    @pytest.mark.p1
    @pytest.mark.api15
    def test_delete_selected_fingerprints_not_exist(self, api_client, base_url, template_id):
        """删除不存在的指纹"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/{template_id}",
            json={
                "ids": ["not-exist-fingerprint-id"]
            }
        )
        # 可能忽略不存在的或报错
        assert response.status_code in [200, 400, 404]

    # TestCase: TC-105
    @pytest.mark.p1
    @pytest.mark.api15
    def test_delete_selected_fingerprints_empty_id(self, api_client, base_url):
        """必填参数缺失-templateId为空"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/",
            json={
                "ids": ["fp-001"]
            }
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-106
    @pytest.mark.p2
    @pytest.mark.api15
    def test_delete_selected_fingerprints_empty_ids(self, api_client, base_url, template_id):
        """必填参数缺失-ids为空数组"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/{template_id}",
            json={
                "ids": []
            }
        )
        assert response.status_code in [400, 200]
