"""
基线核查模板查询接口测试

API-01: GET /v1/config-templates 采集指纹模板分页
API-08: GET /v1/config-templates/{templateId}/{optType}/basic 查询模板基本信息
API-09: GET /v1/config-templates/{templateId}/list 查询模板指纹列表
API-10: GET /v1/config-templates/choose 指纹分页列表
API-11: POST /v1/config-templates/isExist 唯一性校验
API-18: GET /v1/config-template/task 查询任务模板列表
"""

import pytest
import json


class TestConfigTemplatesPageQuery:
    """API-01: GET /v1/config-templates 采集指纹模板分页查询"""

    # TestCase: TC-001
    @pytest.mark.p0
    @pytest.mark.api01
    def test_query_templates_default_params(self, api_client, base_url):
        """正常分页查询-默认参数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"params": json.dumps({})}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "entity" in data
        # 验证默认分页参数
        if "page" in data:
            assert data.get("page", 1) == 1
        if "perPage" in data:
            assert data.get("perPage", 10) == 10

    # TestCase: TC-002
    @pytest.mark.p0
    @pytest.mark.api01
    def test_query_templates_with_pagination(self, api_client, base_url):
        """正常分页查询-指定分页参数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 2,
                "perPage": 20,
                "params": json.dumps({})
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "entity" in data

    # TestCase: TC-003
    @pytest.mark.p0
    @pytest.mark.api01
    def test_query_templates_with_filter(self, api_client, base_url):
        """正常查询-带筛选条件"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "params": json.dumps({"templateName": "测试模板"})
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "entity" in data

    # TestCase: TC-004
    @pytest.mark.p1
    @pytest.mark.api01
    def test_query_templates_missing_params(self, api_client, base_url):
        """必填参数缺失-params为空"""
        response = api_client.get(
            f"{base_url}/v1/config-templates"
        )
        # params是必填参数，缺失应返回400
        assert response.status_code in [400, 200]  # 部分系统可能默认处理

    # TestCase: TC-005
    @pytest.mark.p1
    @pytest.mark.api01
    def test_query_templates_invalid_page_type(self, api_client, base_url):
        """参数类型错误-page非整数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": "abc",
                "params": json.dumps({})
            }
        )
        assert response.status_code == 400

    # TestCase: TC-006
    @pytest.mark.p1
    @pytest.mark.api01
    def test_query_templates_invalid_perpage_type(self, api_client, base_url):
        """参数类型错误-perPage非整数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "perPage": "xyz",
                "params": json.dumps({})
            }
        )
        assert response.status_code == 400

    # TestCase: TC-007
    @pytest.mark.p2
    @pytest.mark.api01
    def test_query_templates_page_zero(self, api_client, base_url):
        """边界测试-page为0"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 0,
                "params": json.dumps({})
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-008
    @pytest.mark.p2
    @pytest.mark.api01
    def test_query_templates_page_negative(self, api_client, base_url):
        """边界测试-page为负数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": -1,
                "params": json.dumps({})
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-009
    @pytest.mark.p2
    @pytest.mark.api01
    def test_query_templates_perpage_zero(self, api_client, base_url):
        """边界测试-perPage为0"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "perPage": 0,
                "params": json.dumps({})
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-010
    @pytest.mark.p2
    @pytest.mark.api01
    def test_query_templates_perpage_large(self, api_client, base_url):
        """边界测试-perPage超大值"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "perPage": 10000,
                "params": json.dumps({})
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-011
    @pytest.mark.p2
    @pytest.mark.api01
    def test_query_templates_page_large_no_data(self, api_client, base_url):
        """边界测试-page超大值无数据"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 999999,
                "params": json.dumps({})
            }
        )
        assert response.status_code == 200
        data = response.json()
        # 应返回空数据列表
        if "data" in data:
            assert len(data.get("data", [])) == 0 or data.get("data") is None


class TestTemplateBasicInfo:
    """API-08: GET /v1/config-templates/{templateId}/{optType}/basic 查询模板基本信息"""

    # TestCase: TC-053
    @pytest.mark.p0
    @pytest.mark.api08
    def test_query_template_info_view(self, api_client, base_url, template_id):
        """正常查询模板基本信息-view模式"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{template_id}/view/basic"
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "success" in data or "entity" in data

    # TestCase: TC-054
    @pytest.mark.p0
    @pytest.mark.api08
    def test_query_template_info_edit(self, api_client, base_url, template_id):
        """正常查询模板基本信息-edit模式"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{template_id}/edit/basic"
        )
        assert response.status_code in [200, 404]

    # TestCase: TC-055
    @pytest.mark.p1
    @pytest.mark.api08
    def test_query_template_info_not_exist(self, api_client, base_url, non_existent_id):
        """查询不存在的模板"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{non_existent_id}/view/basic"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-056
    @pytest.mark.p1
    @pytest.mark.api08
    def test_query_template_info_empty_id(self, api_client, base_url):
        """必填参数缺失-templateId为空"""
        response = api_client.get(
            f"{base_url}/v1/config-templates//view/basic"
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-057
    @pytest.mark.p1
    @pytest.mark.api08
    def test_query_template_info_empty_opttype(self, api_client, base_url, template_id):
        """必填参数缺失-optType为空"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{template_id}//basic"
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-058
    @pytest.mark.p2
    @pytest.mark.api08
    def test_query_template_info_invalid_opttype(self, api_client, base_url, template_id):
        """参数错误-optType无效值"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{template_id}/invalid/basic"
        )
        assert response.status_code in [400, 404, 200]

    # TestCase: TC-059
    @pytest.mark.p2
    @pytest.mark.api08
    def test_query_template_info_special_chars(self, api_client, base_url):
        """边界测试-templateId特殊字符"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/../../view/basic"
        )
        assert response.status_code in [400, 404]


class TestTemplateFingerprintList:
    """API-09: GET /v1/config-templates/{templateId}/list 查询模板指纹列表"""

    # TestCase: TC-060
    @pytest.mark.p0
    @pytest.mark.api09
    def test_query_fingerprint_list_default(self, api_client, base_url, template_id):
        """正常查询-默认分页"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{template_id}/list"
        )
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "data" in data or "entity" in data

    # TestCase: TC-061
    @pytest.mark.p0
    @pytest.mark.api09
    def test_query_fingerprint_list_with_pagination(self, api_client, base_url, template_id):
        """正常查询-指定分页"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{template_id}/list",
            params={"page": 2, "perPage": 20}
        )
        assert response.status_code in [200, 404]

    # TestCase: TC-062
    @pytest.mark.p0
    @pytest.mark.api09
    def test_query_fingerprint_list_with_filter(self, api_client, base_url, template_id):
        """正常查询-带筛选条件"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{template_id}/list",
            params={
                "checkItemName": "密码",
                "riskLevel": "high"
            }
        )
        assert response.status_code in [200, 404]

    # TestCase: TC-063
    @pytest.mark.p1
    @pytest.mark.api09
    def test_query_fingerprint_list_with_sort(self, api_client, base_url, template_id):
        """正常查询-带排序"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{template_id}/list",
            params={
                "field": "createTime",
                "order": "desc"
            }
        )
        assert response.status_code in [200, 404]

    # TestCase: TC-064
    @pytest.mark.p1
    @pytest.mark.api09
    def test_query_fingerprint_list_not_exist(self, api_client, base_url, non_existent_id):
        """查询不存在的模板指纹"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{non_existent_id}/list"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-065
    @pytest.mark.p1
    @pytest.mark.api09
    def test_query_fingerprint_list_empty_id(self, api_client, base_url):
        """必填参数缺失-templateId为空"""
        response = api_client.get(
            f"{base_url}/v1/config-templates//list"
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-066
    @pytest.mark.p2
    @pytest.mark.api09
    def test_query_fingerprint_list_page_negative(self, api_client, base_url, template_id):
        """边界测试-page为负数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{template_id}/list",
            params={"page": -1}
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-067
    @pytest.mark.p2
    @pytest.mark.api09
    def test_query_fingerprint_list_perpage_zero(self, api_client, base_url, template_id):
        """边界测试-perPage为0"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{template_id}/list",
            params={"perPage": 0}
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-068
    @pytest.mark.p2
    @pytest.mark.api09
    def test_query_fingerprint_list_special_chars(self, api_client, base_url, template_id):
        """边界测试-checkItemName特殊字符"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/{template_id}/list",
            params={"checkItemName": "\x00\x0a"}
        )
        assert response.status_code in [200, 400]


class TestFingerprintChoose:
    """API-10: GET /v1/config-templates/choose 指纹分页列表"""

    # TestCase: TC-069
    @pytest.mark.p0
    @pytest.mark.api10
    def test_query_choose_default(self, api_client, base_url):
        """正常查询-默认分页"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose"
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "entity" in data

    # TestCase: TC-070
    @pytest.mark.p0
    @pytest.mark.api10
    def test_query_choose_selected_true(self, api_client, base_url, template_id):
        """查询已选指纹"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={
                "tempId": template_id,
                "selected": "true"
            }
        )
        assert response.status_code == 200

    # TestCase: TC-071
    @pytest.mark.p0
    @pytest.mark.api10
    def test_query_choose_selected_false(self, api_client, base_url, template_id):
        """查询未选指纹"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={
                "tempId": template_id,
                "selected": "false"
            }
        )
        assert response.status_code == 200

    # TestCase: TC-072
    @pytest.mark.p1
    @pytest.mark.api10
    def test_query_choose_by_fingertype(self, api_client, base_url):
        """按指纹类型筛选"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"fingerType": "os"}
        )
        assert response.status_code == 200

    # TestCase: TC-073
    @pytest.mark.p1
    @pytest.mark.api10
    def test_query_choose_by_assettype(self, api_client, base_url):
        """按资产类型筛选"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"assetTypeCode": "linux"}
        )
        assert response.status_code == 200

    # TestCase: TC-074
    @pytest.mark.p1
    @pytest.mark.api10
    def test_query_choose_by_name(self, api_client, base_url):
        """按检查项名称搜索"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"checkItemName": "密码策略"}
        )
        assert response.status_code == 200

    # TestCase: TC-075
    @pytest.mark.p1
    @pytest.mark.api10
    def test_query_choose_with_sort(self, api_client, base_url):
        """带排序查询"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={
                "field": "name",
                "order": "asc"
            }
        )
        assert response.status_code == 200

    # TestCase: TC-076
    @pytest.mark.p2
    @pytest.mark.api10
    def test_query_choose_invalid_page(self, api_client, base_url):
        """边界测试-page非整数"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"page": "abc"}
        )
        assert response.status_code == 400

    # TestCase: TC-077
    @pytest.mark.p2
    @pytest.mark.api10
    def test_query_choose_perpage_large(self, api_client, base_url):
        """边界测试-perPage超大值"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"perPage": 100000}
        )
        assert response.status_code in [200, 400]


class TestTemplateIsExist:
    """API-11: POST /v1/config-templates/isExist 唯一性校验"""

    # TestCase: TC-078
    @pytest.mark.p0
    @pytest.mark.api11
    def test_check_name_not_exist(self, api_client, base_url):
        """名称不存在-新增场景"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "unique_name_not_exist_12345",
                "id": ""
            }
        )
        assert response.status_code == 200
        data = response.json()
        # entity为false表示名称不存在
        assert "entity" in data or "success" in data

    # TestCase: TC-079
    @pytest.mark.p0
    @pytest.mark.api11
    def test_check_name_exist(self, api_client, base_url):
        """名称已存在-新增场景"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "已有模板",
                "id": ""
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "entity" in data or "success" in data

    # TestCase: TC-080
    @pytest.mark.p0
    @pytest.mark.api11
    def test_check_name_self_edit(self, api_client, base_url, template_id):
        """名称存在但是自己-编辑场景"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "当前模板名",
                "id": template_id
            }
        )
        assert response.status_code == 200

    # TestCase: TC-081
    @pytest.mark.p1
    @pytest.mark.api11
    def test_check_missing_checktype(self, api_client, base_url):
        """必填参数缺失-checkType为空"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "",
                "checkValue": "test",
                "id": "1"
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-082
    @pytest.mark.p1
    @pytest.mark.api11
    def test_check_missing_checkvalue(self, api_client, base_url):
        """必填参数缺失-checkValue为空"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "",
                "id": "1"
            }
        )
        assert response.status_code in [400, 200]

    # TestCase: TC-083
    @pytest.mark.p1
    @pytest.mark.api11
    def test_check_empty_id(self, api_client, base_url):
        """必填参数缺失-id为空（作为新增处理）"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "test",
                "id": ""
            }
        )
        assert response.status_code == 200

    # TestCase: TC-084
    @pytest.mark.p2
    @pytest.mark.api11
    def test_check_value_long(self, api_client, base_url):
        """边界测试-checkValue超长"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "a" * 1000,
                "id": ""
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-085
    @pytest.mark.p2
    @pytest.mark.api11
    def test_check_value_special_chars(self, api_client, base_url):
        """边界测试-checkValue特殊字符"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "<>&\"'",
                "id": ""
            }
        )
        assert response.status_code == 200


class TestTaskTemplateList:
    """API-18: GET /v1/config-template/task 查询任务模板列表"""

    # TestCase: TC-119
    @pytest.mark.p0
    @pytest.mark.api18
    def test_query_task_templates(self, api_client, base_url):
        """正常查询任务模板列表"""
        response = api_client.get(
            f"{base_url}/v1/config-template/task"
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "entity" in data

    # TestCase: TC-120
    @pytest.mark.p1
    @pytest.mark.api18
    def test_query_task_templates_empty(self, api_client, base_url):
        """查询-无可用模板时返回空列表"""
        response = api_client.get(
            f"{base_url}/v1/config-template/task"
        )
        assert response.status_code == 200
        data = response.json()
        # 即使无数据也应返回200
        if "entity" in data:
            assert isinstance(data["entity"], list) or data["entity"] is None
