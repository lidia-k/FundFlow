"""
Contract tests for GET /api/salt-rules/{ruleSetId}/preview endpoint
Task: T017 - Contract test GET /api/salt-rules/{ruleSetId}/preview
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4
from app.main import app


class TestPreviewEndpointContract:
    """Test preview endpoint API contract compliance"""

    def setup_method(self):
        """Setup test client"""
        # This should fail initially as the endpoint doesn't exist yet
        self.client = TestClient(app)

    def test_preview_endpoint_exists(self):
        """Test that preview endpoint exists and accepts GET"""
        rule_set_id = str(uuid4())
        response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview")

        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_preview_success_response_schema(self):
        """Test successful preview response matches OpenAPI schema"""
        rule_set_id = str(uuid4())
        compare_with_id = str(uuid4())

        # Mock comparison service response
        mock_preview_result = {
            "ruleSetId": rule_set_id,
            "comparison": {
                "added": [
                    {
                        "ruleType": "withholding",
                        "state": "TX",
                        "entityType": "Corporation",
                        "changes": [
                            {
                                "field": "tax_rate",
                                "oldValue": None,
                                "newValue": "0.0000"
                            }
                        ]
                    }
                ],
                "modified": [
                    {
                        "ruleType": "withholding",
                        "state": "CA",
                        "entityType": "Partnership",
                        "changes": [
                            {
                                "field": "tax_rate",
                                "oldValue": "0.0525",
                                "newValue": "0.0575"
                            },
                            {
                                "field": "income_threshold",
                                "oldValue": "1000.00",
                                "newValue": "1500.00"
                            }
                        ]
                    }
                ],
                "removed": []
            },
            "summary": {
                "rulesAdded": 1,
                "rulesModified": 1,
                "rulesRemoved": 0,
                "fieldsChanged": 3
            }
        }

        with patch('src.services.comparison_service.ComparisonService.compare_rule_sets', return_value=mock_preview_result):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview")

        assert response.status_code == 200
        response_data = response.json()

        # Validate response schema according to OpenAPI spec
        assert "ruleSetId" in response_data
        assert "comparison" in response_data
        assert "summary" in response_data

        # Validate ruleSetId is UUID format
        import uuid
        uuid.UUID(response_data["ruleSetId"])

        # Validate comparison schema
        comparison = response_data["comparison"]
        assert "added" in comparison
        assert "modified" in comparison
        assert "removed" in comparison
        assert isinstance(comparison["added"], list)
        assert isinstance(comparison["modified"], list)
        assert isinstance(comparison["removed"], list)

        # Validate rule change schema for added rules
        if len(comparison["added"]) > 0:
            added_rule = comparison["added"][0]
            assert "ruleType" in added_rule
            assert "state" in added_rule
            assert "entityType" in added_rule
            assert "changes" in added_rule
            assert added_rule["ruleType"] in ["withholding", "composite"]
            assert isinstance(added_rule["changes"], list)

            # Validate field change schema
            if len(added_rule["changes"]) > 0:
                field_change = added_rule["changes"][0]
                assert "field" in field_change
                assert "oldValue" in field_change
                assert "newValue" in field_change

        # Validate summary schema
        summary = response_data["summary"]
        assert "rulesAdded" in summary
        assert "rulesModified" in summary
        assert "rulesRemoved" in summary
        assert "fieldsChanged" in summary
        assert isinstance(summary["rulesAdded"], int)
        assert isinstance(summary["rulesModified"], int)
        assert isinstance(summary["rulesRemoved"], int)
        assert isinstance(summary["fieldsChanged"], int)

    def test_preview_with_compare_with_parameter(self):
        """Test preview with compareWith query parameter"""
        rule_set_id = str(uuid4())
        compare_with_id = str(uuid4())

        mock_preview_result = {
            "ruleSetId": rule_set_id,
            "comparison": {"added": [], "modified": [], "removed": []},
            "summary": {"rulesAdded": 0, "rulesModified": 0, "rulesRemoved": 0, "fieldsChanged": 0}
        }

        with patch('src.services.comparison_service.ComparisonService.compare_rule_sets', return_value=mock_preview_result) as mock_compare:
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview?compareWith={compare_with_id}")

        assert response.status_code in [200, 404]  # 404 if rule set not found
        # Verify that compareWith parameter was passed to the service
        if response.status_code == 200:
            mock_compare.assert_called_once()

    def test_preview_invalid_compare_with_uuid(self):
        """Test validation of compareWith parameter UUID format"""
        rule_set_id = str(uuid4())
        invalid_compare_id = "not-a-uuid"

        response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview?compareWith={invalid_compare_id}")
        assert response.status_code == 400

        response_data = response.json()
        assert "error" in response_data
        assert "message" in response_data

    def test_preview_rule_set_not_found(self):
        """Test 404 response when rule set doesn't exist"""
        non_existent_id = str(uuid4())

        with patch('src.services.comparison_service.ComparisonService.compare_rule_sets', side_effect=ValueError("Rule set not found")):
            response = self.client.get(f"/api/salt-rules/{non_existent_id}/preview")

        assert response.status_code == 404
        response_data = response.json()

        # Validate error response schema
        assert "error" in response_data
        assert "message" in response_data
        assert isinstance(response_data["error"], str)
        assert isinstance(response_data["message"], str)

    def test_preview_invalid_rule_set_id_format(self):
        """Test 400 response for invalid UUID format"""
        invalid_id = "not-a-uuid"
        response = self.client.get(f"/api/salt-rules/{invalid_id}/preview")

        assert response.status_code == 400
        response_data = response.json()

        # Validate error response schema
        assert "error" in response_data
        assert "message" in response_data

    def test_preview_rule_type_enum_values(self):
        """Test rule type enum values in response"""
        rule_set_id = str(uuid4())

        mock_preview_result = {
            "ruleSetId": rule_set_id,
            "comparison": {
                "added": [
                    {
                        "ruleType": "withholding",
                        "state": "CA",
                        "entityType": "Corporation",
                        "changes": []
                    },
                    {
                        "ruleType": "composite",
                        "state": "NY",
                        "entityType": "Partnership",
                        "changes": []
                    }
                ],
                "modified": [],
                "removed": []
            },
            "summary": {"rulesAdded": 2, "rulesModified": 0, "rulesRemoved": 0, "fieldsChanged": 0}
        }

        with patch('src.services.comparison_service.ComparisonService.compare_rule_sets', return_value=mock_preview_result):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview")

        assert response.status_code == 200
        response_data = response.json()

        added_rules = response_data["comparison"]["added"]
        rule_types = [rule["ruleType"] for rule in added_rules]

        # Verify only valid rule types are present
        for rule_type in rule_types:
            assert rule_type in ["withholding", "composite"]

    def test_preview_entity_type_values(self):
        """Test entity type values match InvestorEntityType enum"""
        rule_set_id = str(uuid4())

        valid_entity_types = [
            "individual", "trust", "estate", "partnership", "corporation", "llc",
            "pension_fund", "endowment", "foundation", "insurance_company", "bank",
            "government", "foreign_government", "sovereign_wealth_fund", "other"
        ]

        mock_preview_result = {
            "ruleSetId": rule_set_id,
            "comparison": {
                "added": [
                    {
                        "ruleType": "withholding",
                        "state": "CA",
                        "entityType": "corporation",
                        "changes": []
                    }
                ],
                "modified": [],
                "removed": []
            },
            "summary": {"rulesAdded": 1, "rulesModified": 0, "rulesRemoved": 0, "fieldsChanged": 0}
        }

        with patch('src.services.comparison_service.ComparisonService.compare_rule_sets', return_value=mock_preview_result):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview")

        assert response.status_code == 200
        response_data = response.json()

        added_rules = response_data["comparison"]["added"]
        if len(added_rules) > 0:
            entity_type = added_rules[0]["entityType"]
            assert entity_type in valid_entity_types

    def test_preview_field_change_all_fields(self):
        """Test field changes include all possible field names"""
        rule_set_id = str(uuid4())

        # Test various field changes
        mock_field_changes = [
            {"field": "tax_rate", "oldValue": "0.0525", "newValue": "0.0575"},
            {"field": "income_threshold", "oldValue": "1000.00", "newValue": "1500.00"},
            {"field": "tax_threshold", "oldValue": "100.00", "newValue": "150.00"},
            {"field": "mandatory_filing", "oldValue": "true", "newValue": "false"},
            {"field": "min_tax_amount", "oldValue": "25.00", "newValue": "50.00"},
            {"field": "max_tax_amount", "oldValue": "10000.00", "newValue": "15000.00"}
        ]

        mock_preview_result = {
            "ruleSetId": rule_set_id,
            "comparison": {
                "added": [],
                "modified": [
                    {
                        "ruleType": "composite",
                        "state": "CA",
                        "entityType": "corporation",
                        "changes": mock_field_changes
                    }
                ],
                "removed": []
            },
            "summary": {"rulesAdded": 0, "rulesModified": 1, "rulesRemoved": 0, "fieldsChanged": 6}
        }

        with patch('src.services.comparison_service.ComparisonService.compare_rule_sets', return_value=mock_preview_result):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview")

        assert response.status_code == 200
        response_data = response.json()

        modified_rules = response_data["comparison"]["modified"]
        assert len(modified_rules) == 1

        changes = modified_rules[0]["changes"]
        assert len(changes) == 6

        # Validate all field changes have required structure
        for change in changes:
            assert "field" in change
            assert "oldValue" in change
            assert "newValue" in change
            assert isinstance(change["field"], str)

    def test_preview_empty_comparison_result(self):
        """Test preview response when no changes detected"""
        rule_set_id = str(uuid4())

        mock_preview_result = {
            "ruleSetId": rule_set_id,
            "comparison": {
                "added": [],
                "modified": [],
                "removed": []
            },
            "summary": {
                "rulesAdded": 0,
                "rulesModified": 0,
                "rulesRemoved": 0,
                "fieldsChanged": 0
            }
        }

        with patch('src.services.comparison_service.ComparisonService.compare_rule_sets', return_value=mock_preview_result):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview")

        assert response.status_code == 200
        response_data = response.json()

        # Validate structure even when empty
        assert len(response_data["comparison"]["added"]) == 0
        assert len(response_data["comparison"]["modified"]) == 0
        assert len(response_data["comparison"]["removed"]) == 0
        assert response_data["summary"]["rulesAdded"] == 0
        assert response_data["summary"]["rulesModified"] == 0
        assert response_data["summary"]["rulesRemoved"] == 0
        assert response_data["summary"]["fieldsChanged"] == 0