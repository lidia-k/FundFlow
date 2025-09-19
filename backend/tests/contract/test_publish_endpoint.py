"""
Contract tests for POST /api/salt-rules/{ruleSetId}/publish endpoint
Task: T018 - Contract test POST /api/salt-rules/{ruleSetId}/publish
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4
from app.main import app


class TestPublishEndpointContract:
    """Test publish endpoint API contract compliance"""

    def setup_method(self):
        """Setup test client"""
        # This should fail initially as the endpoint doesn't exist yet
        self.client = TestClient(app)

    def test_publish_endpoint_exists(self):
        """Test that publish endpoint exists and accepts POST"""
        rule_set_id = str(uuid4())
        data = {"confirmArchive": True}

        response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=data)

        # Should not return 404 (endpoint exists) or 405 (method not allowed)
        assert response.status_code not in [404, 405]

    def test_publish_success_response_schema(self):
        """Test successful publish response matches OpenAPI schema"""
        rule_set_id = str(uuid4())
        archived_rule_set_id = str(uuid4())

        request_data = {
            "effectiveDate": "2025-01-01",
            "confirmArchive": True
        }

        # Mock publish service response
        mock_publish_result = {
            "ruleSetId": rule_set_id,
            "status": "active",
            "effectiveDate": "2025-01-01",
            "archivedRuleSet": archived_rule_set_id,
            "resolvedRulesGenerated": 102
        }

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set', return_value=mock_publish_result):
            response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=request_data)

        assert response.status_code == 200
        response_data = response.json()

        # Validate response schema according to OpenAPI spec
        assert "ruleSetId" in response_data
        assert "status" in response_data
        assert "effectiveDate" in response_data

        # Validate ruleSetId is UUID format
        import uuid
        uuid.UUID(response_data["ruleSetId"])

        # Validate status is valid enum value
        assert response_data["status"] in ["draft", "active", "archived"]

        # Validate effectiveDate is date format
        from datetime import datetime
        datetime.strptime(response_data["effectiveDate"], "%Y-%m-%d")

        # Validate optional fields
        if "archivedRuleSet" in response_data:
            uuid.UUID(response_data["archivedRuleSet"])

        if "resolvedRulesGenerated" in response_data:
            assert isinstance(response_data["resolvedRulesGenerated"], int)
            assert response_data["resolvedRulesGenerated"] >= 0

    def test_publish_request_body_validation(self):
        """Test request body validation"""
        rule_set_id = str(uuid4())

        # Valid request with all optional fields
        valid_data = {
            "effectiveDate": "2025-01-01",
            "confirmArchive": True
        }

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set'):
            response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=valid_data)
        assert response.status_code in [200, 400, 404]  # 400/404 for business logic, not schema

        # Empty request body (all fields optional)
        empty_data = {}
        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set'):
            response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=empty_data)
        assert response.status_code in [200, 400, 404]

        # Invalid date format
        invalid_date_data = {
            "effectiveDate": "invalid-date",
            "confirmArchive": True
        }
        response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=invalid_date_data)
        assert response.status_code == 400

        # Invalid confirmArchive type
        invalid_confirm_data = {
            "effectiveDate": "2025-01-01",
            "confirmArchive": "not-a-boolean"
        }
        response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=invalid_confirm_data)
        assert response.status_code == 400

    def test_publish_effective_date_validation(self):
        """Test effective date field validation"""
        rule_set_id = str(uuid4())

        # Valid date formats
        valid_dates = ["2025-01-01", "2025-12-31", "2024-02-29"]  # Leap year

        for date_str in valid_dates:
            data = {"effectiveDate": date_str, "confirmArchive": True}
            with patch('src.services.rule_set_service.RuleSetService.publish_rule_set'):
                response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=data)
            assert response.status_code in [200, 400, 404]  # Not schema validation error

        # Invalid date formats
        invalid_dates = ["2025-13-01", "2025-01-32", "not-a-date", "2025/01/01"]

        for date_str in invalid_dates:
            data = {"effectiveDate": date_str, "confirmArchive": True}
            response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=data)
            assert response.status_code == 400

    def test_publish_confirm_archive_default_value(self):
        """Test confirmArchive default value behavior"""
        rule_set_id = str(uuid4())

        # Request without confirmArchive (should default to false)
        data = {"effectiveDate": "2025-01-01"}

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set') as mock_publish:
            response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=data)

        # Should not fail due to missing confirmArchive
        assert response.status_code in [200, 400, 404]

    def test_publish_validation_errors_prevent_publish(self):
        """Test 400 response when validation errors prevent publication"""
        rule_set_id = str(uuid4())
        data = {"confirmArchive": True}

        # Mock service to return validation error
        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set',
                  side_effect=ValueError("Cannot publish with validation errors")):
            response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=data)

        assert response.status_code == 400
        response_data = response.json()

        # Validate error response schema
        assert "error" in response_data
        assert "message" in response_data
        assert isinstance(response_data["error"], str)
        assert isinstance(response_data["message"], str)

    def test_publish_conflict_response_active_exists(self):
        """Test 409 response when active rule set exists without confirmation"""
        rule_set_id = str(uuid4())
        existing_active_id = str(uuid4())

        data = {"confirmArchive": False}  # Not confirming archive

        # Mock conflict response
        mock_conflict_data = {
            "error": "ACTIVE_RULE_SET_EXISTS",
            "message": "Active rule set exists for 2025 Q1, confirmation required",
            "existingActiveRuleSetId": existing_active_id,
            "requiresConfirmation": True
        }

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set',
                  side_effect=Exception("Conflict")) as mock_publish:
            # Mock the conflict detection in the endpoint
            with patch('src.api.salt_rules.check_active_rule_set_conflict', return_value=mock_conflict_data):
                response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=data)

        assert response.status_code == 409
        response_data = response.json()

        # Validate conflict response schema
        assert "error" in response_data
        assert "message" in response_data
        # Optional fields in conflict response would be validated by actual implementation

    def test_publish_rule_set_not_found(self):
        """Test 404 response when rule set doesn't exist"""
        non_existent_id = str(uuid4())
        data = {"confirmArchive": True}

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set',
                  side_effect=ValueError("Rule set not found")):
            response = self.client.post(f"/api/salt-rules/{non_existent_id}/publish", json=data)

        assert response.status_code == 404
        response_data = response.json()

        # Validate error response schema
        assert "error" in response_data
        assert "message" in response_data

    def test_publish_invalid_rule_set_id_format(self):
        """Test 400 response for invalid UUID format"""
        invalid_id = "not-a-uuid"
        data = {"confirmArchive": True}

        response = self.client.post(f"/api/salt-rules/{invalid_id}/publish", json=data)

        assert response.status_code == 400
        response_data = response.json()

        # Validate error response schema
        assert "error" in response_data
        assert "message" in response_data

    def test_publish_content_type_validation(self):
        """Test that endpoint requires application/json content type"""
        rule_set_id = str(uuid4())

        # Send as form data instead of JSON
        response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish",
                                  data={"confirmArchive": "true"})

        # Should require JSON content type
        assert response.status_code in [400, 415]  # 415 Unsupported Media Type

    def test_publish_status_enum_values(self):
        """Test status enum values in response"""
        rule_set_id = str(uuid4())
        data = {"confirmArchive": True}

        for status in ["draft", "active", "archived"]:
            mock_result = {
                "ruleSetId": rule_set_id,
                "status": status,
                "effectiveDate": "2025-01-01"
            }

            with patch('src.services.rule_set_service.RuleSetService.publish_rule_set', return_value=mock_result):
                response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=data)

            if response.status_code == 200:
                response_data = response.json()
                assert response_data["status"] == status

    def test_publish_resolved_rules_generated_count(self):
        """Test resolvedRulesGenerated field validation"""
        rule_set_id = str(uuid4())
        data = {"confirmArchive": True}

        mock_result = {
            "ruleSetId": rule_set_id,
            "status": "active",
            "effectiveDate": "2025-01-01",
            "resolvedRulesGenerated": 102  # 51 states * 2 rule types
        }

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set', return_value=mock_result):
            response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=data)

        assert response.status_code == 200
        response_data = response.json()

        if "resolvedRulesGenerated" in response_data:
            assert isinstance(response_data["resolvedRulesGenerated"], int)
            assert response_data["resolvedRulesGenerated"] >= 0
            # Reasonable upper bound (all US states/territories * entity types)
            assert response_data["resolvedRulesGenerated"] <= 1000