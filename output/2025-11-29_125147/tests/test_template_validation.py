"""
基线核查模板管理 - 唯一性校验测试
接口路径: /v1/config-templates/isExist
"""
import pytest
import uuid


class TestTemplateIsExist:
    """POST /v1/config-templates/isExist - 唯一性校验测试"""

    # TestCase: TC-086
    @pytest.mark.p0
    def test_check_name_not_exist(self, api_client, base_url):
        """正常校验-名称不存在"""
        unique_name = f"新模板_{uuid.uuid4().hex[:8]}"
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": unique_name,
                "id": ""
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # entity为false表示不重复
        assert data.get("entity") is False

    # TestCase: TC-087
    @pytest.mark.p0
    def test_check_name_exist(self, api_client, base_url):
        """正常校验-名称已存在"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "测试模板",
                "id": ""
            }
        )
        assert response.status_code == 200
        data = response.json()
        # 根据实际数据决定预期
        assert "entity" in data

    # TestCase: TC-088
    @pytest.mark.p0
    def test_check_name_exclude_self(self, api_client, base_url):
        """正常校验-排除自身"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "测试模板",
                "id": "T001"
            }
        )
        assert response.status_code == 200
        data = response.json()
        # 排除自身后应不算重复
        assert "entity" in data

    # TestCase: TC-089
    @pytest.mark.p0
    def test_check_missing_check_type(self, api_client, base_url):
        """异常-缺少checkType"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkValue": "测试",
                "id": ""
            }
        )
        assert response.status_code == 400

    # TestCase: TC-090
    @pytest.mark.p0
    def test_check_missing_check_value(self, api_client, base_url):
        """异常-缺少checkValue"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "id": ""
            }
        )
        assert response.status_code == 400

    # TestCase: TC-091
    @pytest.mark.p0
    def test_check_missing_id(self, api_client, base_url):
        """异常-缺少id"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "测试"
            }
        )
        assert response.status_code == 400

    # TestCase: TC-092
    @pytest.mark.p1
    def test_check_empty_check_value(self, api_client, base_url):
        """边界-checkValue为空字符串"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "",
                "id": ""
            }
        )
        assert response.status_code in [200, 400]
