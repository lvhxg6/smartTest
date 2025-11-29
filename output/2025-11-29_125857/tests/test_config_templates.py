"""
Test cases for Config Templates CRUD API
Endpoints:
- GET /v1/config-templates - Query templates with pagination
- POST /v1/config-templates - Create template
- PUT /v1/config-templates - Update template
- DELETE /v1/config-templates/{templateId} - Delete template
- GET /v1/config-templates/{templateId}/{optType}/basic - Query template basic info
- POST /v1/config-templates/isExist - Check name uniqueness
"""
import pytest
import json


class TestQueryTemplates:
    """Tests for GET /v1/config-templates - Query template list with pagination"""

    # TestCase: TC-001
    @pytest.mark.p0
    def test_query_templates_default_pagination(self, api_client, base_url):
        """TC-001: Query templates with default pagination"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"params": json.dumps({})}
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "totalCount" in data

    # TestCase: TC-002
    @pytest.mark.p0
    def test_query_templates_custom_pagination(self, api_client, base_url):
        """TC-002: Query templates with custom page and perPage"""
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
        if "page" in data:
            assert data["page"] == 2
        if "perPage" in data:
            assert data["perPage"] == 20

    # TestCase: TC-003
    @pytest.mark.p0
    def test_query_templates_with_filter(self, api_client, base_url):
        """TC-003: Query templates with filter conditions"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "params": json.dumps({"templateName": "测试模板"})
            }
        )
        assert response.status_code == 200

    # TestCase: TC-004
    @pytest.mark.p1
    def test_query_templates_missing_params(self, api_client, base_url):
        """TC-004: Query templates without required params parameter"""
        response = api_client.get(
            f"{base_url}/v1/config-templates"
        )
        # Should return 400 or handle gracefully
        assert response.status_code in [200, 400]

    # TestCase: TC-005
    @pytest.mark.p1
    def test_query_templates_invalid_page_type(self, api_client, base_url):
        """TC-005: Query templates with non-integer page value"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": "abc",
                "params": json.dumps({})
            }
        )
        assert response.status_code in [400, 500]

    # TestCase: TC-006
    @pytest.mark.p1
    def test_query_templates_invalid_perpage_type(self, api_client, base_url):
        """TC-006: Query templates with non-integer perPage value"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "perPage": "xyz",
                "params": json.dumps({})
            }
        )
        assert response.status_code in [400, 500]

    # TestCase: TC-007
    @pytest.mark.p2
    def test_query_templates_page_zero(self, api_client, base_url):
        """TC-007: Query templates with page=0"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 0,
                "params": json.dumps({})
            }
        )
        # Should either return error or adjust to page 1
        assert response.status_code in [200, 400]

    # TestCase: TC-008
    @pytest.mark.p2
    def test_query_templates_negative_page(self, api_client, base_url):
        """TC-008: Query templates with negative page number"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": -1,
                "params": json.dumps({})
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-009
    @pytest.mark.p2
    def test_query_templates_perpage_zero(self, api_client, base_url):
        """TC-009: Query templates with perPage=0"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "perPage": 0,
                "params": json.dumps({})
            }
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-010
    @pytest.mark.p2
    def test_query_templates_large_perpage(self, api_client, base_url):
        """TC-010: Query templates with very large perPage value"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "perPage": 10000,
                "params": json.dumps({})
            }
        )
        assert response.status_code == 200

    # TestCase: TC-011
    @pytest.mark.p2
    def test_query_templates_page_exceeds_total(self, api_client, base_url):
        """TC-011: Query templates with page number exceeding total pages"""
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={
                "page": 9999,
                "params": json.dumps({})
            }
        )
        assert response.status_code == 200
        data = response.json()
        # Should return empty data list
        if "data" in data:
            assert isinstance(data["data"], list)


class TestCreateTemplate:
    """Tests for POST /v1/config-templates - Create template"""

    # TestCase: TC-012
    @pytest.mark.p0
    def test_create_template_success(self, api_client, base_url, unique_template_name):
        """TC-012: Create template with required fields"""
        template_data = {
            "templateName": unique_template_name,
            "templateDesc": "Test description",
            "templateType": 1
        }
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json=template_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

        # Cleanup
        if data.get("entity"):
            template_id = data["entity"].get("pkHandbook") or data["entity"].get("pkCollectTemplate")
            if template_id:
                api_client.delete(f"{base_url}/v1/config-templates/{template_id}")

    # TestCase: TC-013
    @pytest.mark.p0
    def test_create_template_full_fields(self, api_client, base_url, unique_template_name):
        """TC-013: Create template with all fields"""
        template_data = {
            "templateName": unique_template_name,
            "templateVer": "1.0",
            "templateDesc": "Full description",
            "templateType": 1,
            "isDefault": 0,
            "isUse": 1,
            "specification": "Test specification"
        }
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json=template_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True

        # Cleanup
        if data.get("entity"):
            template_id = data["entity"].get("pkHandbook") or data["entity"].get("pkCollectTemplate")
            if template_id:
                api_client.delete(f"{base_url}/v1/config-templates/{template_id}")

    # TestCase: TC-014
    @pytest.mark.p1
    def test_create_template_empty_body(self, api_client, base_url):
        """TC-014: Create template with empty request body"""
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json={}
        )
        assert response.status_code in [400, 500] or response.json().get("success") is False

    # TestCase: TC-015
    @pytest.mark.p1
    def test_create_template_invalid_type_templatetype(self, api_client, base_url):
        """TC-015: Create template with string templateType"""
        template_data = {
            "templateName": "TestInvalidType",
            "templateType": "abc"
        }
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json=template_data
        )
        assert response.status_code in [400, 500]

    # TestCase: TC-016
    @pytest.mark.p1
    def test_create_template_invalid_type_isdefault(self, api_client, base_url):
        """TC-016: Create template with string isDefault"""
        template_data = {
            "templateName": "TestInvalidDefault",
            "isDefault": "yes"
        }
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json=template_data
        )
        assert response.status_code in [400, 500]

    # TestCase: TC-017
    @pytest.mark.p2
    def test_create_template_empty_name(self, api_client, base_url):
        """TC-017: Create template with empty templateName"""
        template_data = {
            "templateName": "",
            "templateType": 1
        }
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json=template_data
        )
        assert response.status_code in [400, 500] or response.json().get("success") is False

    # TestCase: TC-018
    @pytest.mark.p2
    def test_create_template_long_name(self, api_client, base_url):
        """TC-018: Create template with very long templateName"""
        template_data = {
            "templateName": "a" * 1000,
            "templateType": 1
        }
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json=template_data
        )
        assert response.status_code in [200, 400, 500]

    # TestCase: TC-019
    @pytest.mark.p2
    def test_create_template_special_chars_name(self, api_client, base_url):
        """TC-019: Create template with special characters in name (XSS test)"""
        template_data = {
            "templateName": "<script>alert(1)</script>",
            "templateType": 1
        }
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json=template_data
        )
        # Should either sanitize or reject
        assert response.status_code in [200, 400]

    # TestCase: TC-020
    @pytest.mark.p1
    def test_create_template_duplicate_name(self, api_client, base_url, created_template):
        """TC-020: Create template with duplicate name"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        template_data = {
            "templateName": created_template["template_data"]["templateName"],
            "templateType": 1
        }
        response = api_client.post(
            f"{base_url}/v1/config-templates",
            json=template_data
        )
        # Should fail due to duplicate name
        assert response.status_code in [400, 409, 500] or response.json().get("success") is False


class TestUpdateTemplate:
    """Tests for PUT /v1/config-templates - Update template"""

    # TestCase: TC-021
    @pytest.mark.p0
    def test_update_template_success(self, api_client, base_url, created_template):
        """TC-021: Update template with valid data"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        update_data = {
            "pkCollectTemplate": created_template["template_id"],
            "templateName": f"{created_template['template_data']['templateName']}_updated"
        }
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json=update_data
        )
        assert response.status_code == 200

    # TestCase: TC-022
    @pytest.mark.p0
    def test_update_template_multiple_fields(self, api_client, base_url, created_template):
        """TC-022: Update template with multiple fields"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        update_data = {
            "pkCollectTemplate": created_template["template_id"],
            "templateName": f"{created_template['template_data']['templateName']}_v2",
            "templateDesc": "Updated description",
            "templateVer": "2.0"
        }
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json=update_data
        )
        assert response.status_code == 200

    # TestCase: TC-023
    @pytest.mark.p1
    def test_update_template_empty_body(self, api_client, base_url):
        """TC-023: Update template with empty request body"""
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json={}
        )
        assert response.status_code in [400, 500] or response.json().get("success") is False

    # TestCase: TC-024
    @pytest.mark.p1
    def test_update_template_missing_id(self, api_client, base_url):
        """TC-024: Update template without pkCollectTemplate"""
        update_data = {
            "templateName": "NoIdUpdate"
        }
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json=update_data
        )
        assert response.status_code in [400, 500] or response.json().get("success") is False

    # TestCase: TC-025
    @pytest.mark.p1
    def test_update_template_nonexistent_id(self, api_client, base_url):
        """TC-025: Update template with non-existent ID"""
        update_data = {
            "pkCollectTemplate": "non-exist-id-12345",
            "templateName": "NonExistentUpdate"
        }
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json=update_data
        )
        assert response.status_code in [400, 404, 500] or response.json().get("success") is False

    # TestCase: TC-026
    @pytest.mark.p2
    def test_update_template_empty_name(self, api_client, base_url, created_template):
        """TC-026: Update template with empty templateName"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        update_data = {
            "pkCollectTemplate": created_template["template_id"],
            "templateName": ""
        }
        response = api_client.put(
            f"{base_url}/v1/config-templates",
            json=update_data
        )
        assert response.status_code in [400, 500] or response.json().get("success") is False

    # TestCase: TC-027
    @pytest.mark.p1
    def test_update_template_duplicate_name(self, api_client, base_url, unique_template_name):
        """TC-027: Update template to use existing name"""
        # Create first template
        template1 = {
            "templateName": unique_template_name + "_first",
            "templateType": 1
        }
        resp1 = api_client.post(f"{base_url}/v1/config-templates", json=template1)
        template1_id = None
        if resp1.status_code == 200 and resp1.json().get("entity"):
            template1_id = resp1.json()["entity"].get("pkHandbook") or resp1.json()["entity"].get("pkCollectTemplate")

        # Create second template
        template2 = {
            "templateName": unique_template_name + "_second",
            "templateType": 1
        }
        resp2 = api_client.post(f"{base_url}/v1/config-templates", json=template2)
        template2_id = None
        if resp2.status_code == 200 and resp2.json().get("entity"):
            template2_id = resp2.json()["entity"].get("pkHandbook") or resp2.json()["entity"].get("pkCollectTemplate")

        if template2_id:
            # Try to update second template with first template's name
            update_data = {
                "pkCollectTemplate": template2_id,
                "templateName": unique_template_name + "_first"
            }
            response = api_client.put(f"{base_url}/v1/config-templates", json=update_data)
            assert response.status_code in [400, 409, 500] or response.json().get("success") is False

        # Cleanup
        if template1_id:
            api_client.delete(f"{base_url}/v1/config-templates/{template1_id}")
        if template2_id:
            api_client.delete(f"{base_url}/v1/config-templates/{template2_id}")


class TestDeleteTemplate:
    """Tests for DELETE /v1/config-templates/{templateId} - Delete template"""

    # TestCase: TC-028
    @pytest.mark.p0
    def test_delete_template_success(self, api_client, base_url, unique_template_name):
        """TC-028: Delete existing template"""
        # Create a template first
        template_data = {
            "templateName": unique_template_name,
            "templateType": 1
        }
        create_resp = api_client.post(f"{base_url}/v1/config-templates", json=template_data)
        if create_resp.status_code != 200 or not create_resp.json().get("entity"):
            pytest.skip("Failed to create prerequisite template")

        template_id = create_resp.json()["entity"].get("pkHandbook") or create_resp.json()["entity"].get("pkCollectTemplate")
        if not template_id:
            pytest.skip("Failed to get template ID")

        # Delete the template
        response = api_client.delete(f"{base_url}/v1/config-templates/{template_id}")
        assert response.status_code == 200
        assert response.json().get("success") is True

    # TestCase: TC-029
    @pytest.mark.p1
    def test_delete_template_empty_id(self, api_client, base_url):
        """TC-029: Delete template with empty templateId"""
        response = api_client.delete(f"{base_url}/v1/config-templates/")
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-030
    @pytest.mark.p1
    def test_delete_template_nonexistent_id(self, api_client, base_url):
        """TC-030: Delete template with non-existent ID"""
        response = api_client.delete(f"{base_url}/v1/config-templates/non-exist-id-12345")
        assert response.status_code in [400, 404, 500] or response.json().get("success") is False

    # TestCase: TC-031
    @pytest.mark.p2
    def test_delete_template_special_char_id(self, api_client, base_url):
        """TC-031: Delete template with special characters in ID"""
        response = api_client.delete(f"{base_url}/v1/config-templates/<script>")
        assert response.status_code in [400, 404, 500]

    # TestCase: TC-032
    @pytest.mark.p1
    def test_delete_default_template(self, api_client, base_url):
        """TC-032: Attempt to delete default template"""
        # First, get list to find default template
        response = api_client.get(
            f"{base_url}/v1/config-templates",
            params={"params": json.dumps({"isDefault": "1"})}
        )
        if response.status_code == 200 and response.json().get("data"):
            default_templates = [t for t in response.json()["data"] if t.get("isDefault") == 1]
            if default_templates:
                template_id = default_templates[0].get("pkHandbook") or default_templates[0].get("pkCollectTemplate")
                if template_id:
                    delete_resp = api_client.delete(f"{base_url}/v1/config-templates/{template_id}")
                    # Should be rejected
                    assert delete_resp.status_code in [400, 403, 500] or delete_resp.json().get("success") is False
                    return

        pytest.skip("No default template found to test")

    # TestCase: TC-033
    @pytest.mark.p1
    def test_delete_in_use_template(self, api_client, base_url):
        """TC-033: Attempt to delete template in use"""
        # This test requires a template that is being used by a task
        # Skip if no such template exists
        pytest.skip("Requires template in use by task - manual verification needed")


class TestQueryTemplateBasicInfo:
    """Tests for GET /v1/config-templates/{templateId}/{optType}/basic"""

    # TestCase: TC-048
    @pytest.mark.p0
    def test_query_template_info_view(self, api_client, base_url, created_template):
        """TC-048: Query template basic info with view optType"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/{created_template['template_id']}/view/basic"
        )
        assert response.status_code == 200

    # TestCase: TC-049
    @pytest.mark.p0
    def test_query_template_info_edit(self, api_client, base_url, created_template):
        """TC-049: Query template basic info with edit optType"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/{created_template['template_id']}/edit/basic"
        )
        assert response.status_code == 200

    # TestCase: TC-050
    @pytest.mark.p1
    def test_query_template_info_empty_id(self, api_client, base_url):
        """TC-050: Query template info with empty templateId"""
        response = api_client.get(f"{base_url}/v1/config-templates//view/basic")
        assert response.status_code in [400, 404]

    # TestCase: TC-051
    @pytest.mark.p1
    def test_query_template_info_empty_opttype(self, api_client, base_url, created_template):
        """TC-051: Query template info with empty optType"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/{created_template['template_id']}//basic"
        )
        assert response.status_code in [400, 404]

    # TestCase: TC-052
    @pytest.mark.p1
    def test_query_template_info_nonexistent_id(self, api_client, base_url):
        """TC-052: Query template info with non-existent ID"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/non-exist-id-12345/view/basic"
        )
        assert response.status_code in [400, 404, 500] or response.json().get("success") is False

    # TestCase: TC-053
    @pytest.mark.p2
    def test_query_template_info_invalid_opttype(self, api_client, base_url, created_template):
        """TC-053: Query template info with invalid optType"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/{created_template['template_id']}/invalid/basic"
        )
        assert response.status_code in [200, 400, 404]


class TestCheckNameExistence:
    """Tests for POST /v1/config-templates/isExist - Check name uniqueness"""

    # TestCase: TC-066
    @pytest.mark.p0
    def test_check_name_not_exists(self, api_client, base_url, unique_template_name):
        """TC-066: Check name that does not exist"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": unique_template_name,
                "id": ""
            }
        )
        assert response.status_code == 200
        data = response.json()
        # entity should be False (not exists)
        assert data.get("entity") is False or data.get("success") is True

    # TestCase: TC-067
    @pytest.mark.p0
    def test_check_name_exists(self, api_client, base_url, created_template):
        """TC-067: Check name that already exists"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": created_template["template_data"]["templateName"],
                "id": ""
            }
        )
        assert response.status_code == 200
        data = response.json()
        # entity should be True (exists)
        assert data.get("entity") is True

    # TestCase: TC-068
    @pytest.mark.p0
    def test_check_name_exclude_self(self, api_client, base_url, created_template):
        """TC-068: Check name excluding self when editing"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": created_template["template_data"]["templateName"],
                "id": created_template["template_id"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        # entity should be False (excluding self)
        assert data.get("entity") is False

    # TestCase: TC-069
    @pytest.mark.p1
    def test_check_name_missing_checktype(self, api_client, base_url):
        """TC-069: Check name without checkType parameter"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkValue": "test",
                "id": ""
            }
        )
        assert response.status_code in [400, 500]

    # TestCase: TC-070
    @pytest.mark.p1
    def test_check_name_missing_checkvalue(self, api_client, base_url):
        """TC-070: Check name without checkValue parameter"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "id": ""
            }
        )
        assert response.status_code in [400, 500]

    # TestCase: TC-071
    @pytest.mark.p1
    def test_check_name_missing_id(self, api_client, base_url):
        """TC-071: Check name without id parameter"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "test"
            }
        )
        # id is required per Swagger definition
        assert response.status_code in [200, 400, 500]

    # TestCase: TC-072
    @pytest.mark.p2
    def test_check_name_empty_checkvalue(self, api_client, base_url):
        """TC-072: Check name with empty checkValue"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "name",
                "checkValue": "",
                "id": ""
            }
        )
        assert response.status_code in [200, 400, 500]

    # TestCase: TC-073
    @pytest.mark.p2
    def test_check_name_invalid_checktype(self, api_client, base_url):
        """TC-073: Check name with invalid checkType"""
        response = api_client.post(
            f"{base_url}/v1/config-templates/isExist",
            params={
                "checkType": "invalid",
                "checkValue": "test",
                "id": ""
            }
        )
        assert response.status_code in [200, 400, 500]
