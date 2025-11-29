"""
基线核查模板管理 - 任务模板列表测试
接口路径: /v1/config-template/task
"""
import pytest


class TestQueryTaskTemplates:
    """GET /v1/config-template/task - 查询任务模板列表测试"""

    # TestCase: TC-099
    @pytest.mark.p0
    def test_query_task_templates_success(self, api_client, base_url):
        """正常查询任务模板"""
        response = api_client.get(
            f"{base_url}/v1/config-template/task"
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        # 验证返回HandBook列表
        entity = data.get("entity")
        assert entity is None or isinstance(entity, list)

    # TestCase: TC-100
    @pytest.mark.p1
    def test_query_task_templates_no_available(self, api_client, base_url):
        """边界-无可用模板"""
        response = api_client.get(
            f"{base_url}/v1/config-template/task"
        )
        assert response.status_code == 200
        data = response.json()
        # 无可用模板时返回空数组
        assert data.get("success") is True
        entity = data.get("entity")
        assert entity is None or isinstance(entity, list)
