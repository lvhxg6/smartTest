"""
Test cases for Template Fingerprints API
Endpoints:
- GET /v1/config-templates/{templateId}/list - Query template fingerprint list
- GET /v1/config-templates/choose - Query fingerprint pagination list (selected/unselected)
- PUT /v1/config-templates/selectTemplate/{templateId} - Add all fingerprints
- PATCH /v1/config-templates/selectTemplate/{templateId} - Add selected fingerprints
- PUT /v1/config-templates/temps/{templateId} - Delete all fingerprints
- PATCH /v1/config-templates/temps/{templateId} - Batch delete fingerprints
"""
import pytest


class TestQueryTemplateFingerprints:
    """Tests for GET /v1/config-templates/{templateId}/list"""

    # TestCase: TC-054
    @pytest.mark.p0
    def test_query_fingerprints_default_pagination(self, api_client, base_url, created_template):
        """TC-054: Query fingerprints with default pagination"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/{created_template['template_id']}/list"
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or "totalCount" in data

    # TestCase: TC-055
    @pytest.mark.p0
    def test_query_fingerprints_with_filter(self, api_client, base_url, created_template):
        """TC-055: Query fingerprints with filter conditions"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/{created_template['template_id']}/list",
            params={
                "checkItemName": "检查项",
                "riskLevel": "HIGH"
            }
        )
        assert response.status_code == 200

    # TestCase: TC-056
    @pytest.mark.p0
    def test_query_fingerprints_with_sorting(self, api_client, base_url, created_template):
        """TC-056: Query fingerprints with sorting"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/{created_template['template_id']}/list",
            params={
                "field": "createTime",
                "order": "desc"
            }
        )
        assert response.status_code == 200

    # TestCase: TC-057
    @pytest.mark.p1
    def test_query_fingerprints_empty_template_id(self, api_client, base_url):
        """TC-057: Query fingerprints with empty templateId"""
        response = api_client.get(f"{base_url}/v1/config-templates//list")
        assert response.status_code in [400, 404]

    # TestCase: TC-058
    @pytest.mark.p1
    def test_query_fingerprints_nonexistent_template(self, api_client, base_url):
        """TC-058: Query fingerprints for non-existent template"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/non-exist-id-12345/list"
        )
        assert response.status_code in [400, 404, 500] or response.json().get("success") is False

    # TestCase: TC-059
    @pytest.mark.p2
    def test_query_fingerprints_negative_page(self, api_client, base_url, created_template):
        """TC-059: Query fingerprints with negative page number"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/{created_template['template_id']}/list",
            params={"page": -1}
        )
        assert response.status_code in [200, 400]

    # TestCase: TC-060
    @pytest.mark.p2
    def test_query_fingerprints_sql_injection(self, api_client, base_url, created_template):
        """TC-060: Query fingerprints with SQL injection attempt in checkItemName"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/{created_template['template_id']}/list",
            params={"checkItemName": "'OR 1=1"}
        )
        # Should return 200 with proper sanitization
        assert response.status_code == 200


class TestQueryFingerprintChoose:
    """Tests for GET /v1/config-templates/choose"""

    # TestCase: TC-061
    @pytest.mark.p0
    def test_query_selected_fingerprints(self, api_client, base_url, created_template):
        """TC-061: Query selected fingerprints"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={
                "tempId": created_template["template_id"],
                "selected": "true"
            }
        )
        assert response.status_code == 200

    # TestCase: TC-062
    @pytest.mark.p0
    def test_query_unselected_fingerprints(self, api_client, base_url, created_template):
        """TC-062: Query unselected fingerprints"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={
                "tempId": created_template["template_id"],
                "selected": "false"
            }
        )
        assert response.status_code == 200

    # TestCase: TC-063
    @pytest.mark.p0
    def test_query_fingerprints_with_filters(self, api_client, base_url, created_template):
        """TC-063: Query fingerprints with multiple filters"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={
                "tempId": created_template["template_id"],
                "fingerType": "type1",
                "assetTypeCode": "OS"
            }
        )
        assert response.status_code == 200

    # TestCase: TC-064
    @pytest.mark.p1
    def test_query_fingerprints_invalid_page(self, api_client, base_url):
        """TC-064: Query fingerprints with invalid page type"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"page": "abc"}
        )
        assert response.status_code in [400, 500]

    # TestCase: TC-065
    @pytest.mark.p2
    def test_query_fingerprints_large_perpage(self, api_client, base_url):
        """TC-065: Query fingerprints with very large perPage"""
        response = api_client.get(
            f"{base_url}/v1/config-templates/choose",
            params={"perPage": 99999}
        )
        assert response.status_code == 200


class TestAddAllFingerprints:
    """Tests for PUT /v1/config-templates/selectTemplate/{templateId}"""

    # TestCase: TC-074
    @pytest.mark.p0
    def test_add_all_fingerprints_success(self, api_client, base_url, created_template):
        """TC-074: Add all fingerprints to template"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{created_template['template_id']}",
            json={}
        )
        assert response.status_code == 200

    # TestCase: TC-075
    @pytest.mark.p1
    def test_add_all_fingerprints_empty_template_id(self, api_client, base_url):
        """TC-075: Add all fingerprints with empty templateId"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/",
            json={}
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-076
    @pytest.mark.p1
    def test_add_all_fingerprints_nonexistent_template(self, api_client, base_url):
        """TC-076: Add all fingerprints to non-existent template"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/non-exist-id-12345",
            json={}
        )
        assert response.status_code in [400, 404, 500] or response.json().get("success") is False

    # TestCase: TC-077
    @pytest.mark.p2
    def test_add_all_fingerprints_already_full(self, api_client, base_url, created_template):
        """TC-077: Add all fingerprints when template already has all fingerprints"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        # First add all
        api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{created_template['template_id']}",
            json={}
        )

        # Try to add all again
        response = api_client.put(
            f"{base_url}/v1/config-templates/selectTemplate/{created_template['template_id']}",
            json={}
        )
        assert response.status_code == 200
        # entity should be 0 or operation should be idempotent


class TestAddSelectedFingerprints:
    """Tests for PATCH /v1/config-templates/selectTemplate/{templateId}"""

    # TestCase: TC-078
    @pytest.mark.p0
    def test_add_selected_fingerprints_success(self, api_client, base_url, created_template):
        """TC-078: Add selected fingerprints to template"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{created_template['template_id']}",
            json={"ids": ["fp1", "fp2"]}
        )
        assert response.status_code == 200

    # TestCase: TC-079
    @pytest.mark.p1
    def test_add_selected_fingerprints_empty_template_id(self, api_client, base_url):
        """TC-079: Add selected fingerprints with empty templateId"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/",
            json={"ids": ["fp1"]}
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-080
    @pytest.mark.p1
    def test_add_selected_fingerprints_empty_body(self, api_client, base_url, created_template):
        """TC-080: Add selected fingerprints with empty request body"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{created_template['template_id']}",
            json={}
        )
        assert response.status_code in [200, 400, 500]

    # TestCase: TC-081
    @pytest.mark.p1
    def test_add_selected_fingerprints_nonexistent_template(self, api_client, base_url):
        """TC-081: Add selected fingerprints to non-existent template"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/non-exist-id-12345",
            json={"ids": ["fp1"]}
        )
        assert response.status_code in [400, 404, 500] or response.json().get("success") is False

    # TestCase: TC-082
    @pytest.mark.p2
    def test_add_selected_fingerprints_nonexistent_fp(self, api_client, base_url, created_template):
        """TC-082: Add non-existent fingerprint IDs"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.patch(
            f"{base_url}/v1/config-templates/selectTemplate/{created_template['template_id']}",
            json={"ids": ["non-exist-fp-12345"]}
        )
        # Should either skip non-existent or return error
        assert response.status_code in [200, 400]


class TestDeleteAllFingerprints:
    """Tests for PUT /v1/config-templates/temps/{templateId}"""

    # TestCase: TC-083
    @pytest.mark.p0
    def test_delete_all_fingerprints_success(self, api_client, base_url, created_template):
        """TC-083: Delete all fingerprints from template"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/{created_template['template_id']}",
            json={}
        )
        assert response.status_code == 200

    # TestCase: TC-084
    @pytest.mark.p1
    def test_delete_all_fingerprints_empty_template_id(self, api_client, base_url):
        """TC-084: Delete all fingerprints with empty templateId"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/",
            json={}
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-085
    @pytest.mark.p1
    def test_delete_all_fingerprints_nonexistent_template(self, api_client, base_url):
        """TC-085: Delete all fingerprints from non-existent template"""
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/non-exist-id-12345",
            json={}
        )
        assert response.status_code in [400, 404, 500] or response.json().get("success") is False

    # TestCase: TC-086
    @pytest.mark.p2
    def test_delete_all_fingerprints_empty_template(self, api_client, base_url, created_template):
        """TC-086: Delete all fingerprints from template with no fingerprints"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        # First delete all to ensure empty
        api_client.put(
            f"{base_url}/v1/config-templates/temps/{created_template['template_id']}",
            json={}
        )

        # Try to delete all again
        response = api_client.put(
            f"{base_url}/v1/config-templates/temps/{created_template['template_id']}",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        # entity should be 0
        assert data.get("entity") == 0 or data.get("success") is True


class TestBatchDeleteFingerprints:
    """Tests for PATCH /v1/config-templates/temps/{templateId}"""

    # TestCase: TC-087
    @pytest.mark.p0
    def test_batch_delete_fingerprints_success(self, api_client, base_url, created_template):
        """TC-087: Batch delete fingerprints from template"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/{created_template['template_id']}",
            json={"ids": ["fp1", "fp2"]}
        )
        assert response.status_code == 200

    # TestCase: TC-088
    @pytest.mark.p1
    def test_batch_delete_fingerprints_empty_template_id(self, api_client, base_url):
        """TC-088: Batch delete fingerprints with empty templateId"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/",
            json={"ids": ["fp1"]}
        )
        assert response.status_code in [400, 404, 405]

    # TestCase: TC-089
    @pytest.mark.p1
    def test_batch_delete_fingerprints_empty_body(self, api_client, base_url, created_template):
        """TC-089: Batch delete fingerprints with empty request body"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/{created_template['template_id']}",
            json={}
        )
        assert response.status_code in [200, 400, 500]

    # TestCase: TC-090
    @pytest.mark.p1
    def test_batch_delete_fingerprints_nonexistent_template(self, api_client, base_url):
        """TC-090: Batch delete fingerprints from non-existent template"""
        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/non-exist-id-12345",
            json={"ids": ["fp1"]}
        )
        assert response.status_code in [400, 404, 500] or response.json().get("success") is False

    # TestCase: TC-091
    @pytest.mark.p2
    def test_batch_delete_fingerprints_nonexistent_fp(self, api_client, base_url, created_template):
        """TC-091: Batch delete non-existent fingerprint IDs"""
        if created_template["template_id"] is None:
            pytest.skip("Failed to create prerequisite template")

        response = api_client.patch(
            f"{base_url}/v1/config-templates/temps/{created_template['template_id']}",
            json={"ids": ["non-exist-fp-12345"]}
        )
        # Should either skip non-existent or return error
        assert response.status_code in [200, 400]
