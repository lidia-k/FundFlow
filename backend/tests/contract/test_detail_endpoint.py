"""
Contract tests for GET /api/salt-rules/{ruleSetId} endpoint
Task: T020 - Contract test GET /api/salt-rules/{ruleSetId}
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4
from app.main import app


class TestDetailEndpointContract:
    """Test detail endpoint API contract compliance"""

    def setup_method(self):
        """Setup test client"""
        # This should fail initially as the endpoint doesn't exist yet
        self.client = TestClient(app)

    def test_detail_endpoint_exists(self):
        """Test that detail endpoint exists and accepts GET"""
        rule_set_id = str(uuid4())
        response = self.client.get(f"/api/salt-rules/{rule_set_id}")

        # Should not return 404 (endpoint exists) unless rule set doesn't exist
        assert response.status_code != 405  # Method not allowed

    def test_detail_success_response_schema(self):
        """Test successful detail response matches OpenAPI schema"""
        rule_set_id = str(uuid4())
        source_file_id = str(uuid4())

        # Mock complete rule set detail response
        mock_detail_response = {
            # Base rule set summary fields
            "id": rule_set_id,
            "year": 2025,
            "quarter": "Q1",
            "version": "1.0.0",
            "status": "active",
            "effectiveDate": "2025-01-01",
            "createdAt": "2025-01-01T10:00:00Z",
            "publishedAt": "2025-01-01T12:00:00Z",
            "createdBy": "admin@fundflow.com",
            "description": "2025 Q1 SALT rules update",
            "ruleCount": {
                "withholding": 2,
                "composite": 2
            },
            # Extended detail fields
            "sourceFile": {
                "id": source_file_id,
                "filename": "EY_SALT_Rules_2025Q1.xlsx",
                "filepath": "/secure/uploads/2025q1/abc123/file.xlsx",
                "fileSize": 1048576,
                "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "sha256Hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
                "uploadTimestamp": "2025-01-01T09:00:00Z",
                "uploadedBy": "admin@fundflow.com"
            },
            "validationSummary": {
                "totalIssues": 0,
                "errorCount": 0,
                "warningCount": 0,
                "rulesProcessed": {
                    "withholding": 2,
                    "composite": 2
                }
            },
            "rules": {
                "withholding": [
                    {
                        "id": str(uuid4()),
                        "stateCode": "CA",
                        "entityType": "corporation",
                        "taxRate": 0.0525,
                        "incomeThreshold": 1000.00,
                        "taxThreshold": 100.00
                    },
                    {
                        "id": str(uuid4()),
                        "stateCode": "NY",
                        "entityType": "partnership",
                        "taxRate": 0.0625,
                        "incomeThreshold": 1000.00,
                        "taxThreshold": 100.00
                    }
                ],
                "composite": [
                    {
                        "id": str(uuid4()),
                        "stateCode": "CA",
                        "entityType": "corporation",
                        "taxRate": 0.0625,
                        "incomeThreshold": 1000.00,
                        "mandatoryFiling": True,
                        "minTaxAmount": 25.00,
                        "maxTaxAmount": 10000.00
                    },
                    {
                        "id": str(uuid4()),
                        "stateCode": "NY",
                        "entityType": "partnership",
                        "taxRate": 0.0700,
                        "incomeThreshold": 1000.00,
                        "mandatoryFiling": True,
                        "minTaxAmount": 50.00,
                        "maxTaxAmount": 15000.00
                    }
                ]
            }
        }

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail', return_value=mock_detail_response):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}")

        assert response.status_code == 200
        response_data = response.json()

        # Validate base rule set summary schema (inherited from RuleSetSummary)
        assert "id" in response_data
        assert "year" in response_data
        assert "quarter" in response_data
        assert "status" in response_data
        assert "createdAt" in response_data

        # Validate required fields
        import uuid
        uuid.UUID(response_data["id"])
        assert isinstance(response_data["year"], int)
        assert response_data["quarter"] in ["Q1", "Q2", "Q3", "Q4"]
        assert response_data["status"] in ["draft", "active", "archived"]

        # Validate extended detail fields
        assert "sourceFile" in response_data
        assert "validationSummary" in response_data
        assert "rules" in response_data

        # Validate source file schema
        source_file = response_data["sourceFile"]
        assert "id" in source_file
        assert "filename" in source_file
        assert "fileSize" in source_file
        assert "contentType" in source_file
        assert "uploadTimestamp" in source_file
        uuid.UUID(source_file["id"])
        assert isinstance(source_file["fileSize"], int)

        # Validate validation summary schema
        validation_summary = response_data["validationSummary"]
        assert "totalIssues" in validation_summary
        assert "errorCount" in validation_summary
        assert "warningCount" in validation_summary
        assert "rulesProcessed" in validation_summary
        assert isinstance(validation_summary["totalIssues"], int)
        assert isinstance(validation_summary["errorCount"], int)
        assert isinstance(validation_summary["warningCount"], int)

        rules_processed = validation_summary["rulesProcessed"]
        assert "withholding" in rules_processed
        assert "composite" in rules_processed
        assert isinstance(rules_processed["withholding"], int)
        assert isinstance(rules_processed["composite"], int)

        # Validate rules schema
        rules = response_data["rules"]
        assert "withholding" in rules
        assert "composite" in rules
        assert isinstance(rules["withholding"], list)
        assert isinstance(rules["composite"], list)

    def test_detail_withholding_rule_schema(self):
        """Test withholding rule schema validation"""
        rule_set_id = str(uuid4())

        mock_withholding_rule = {
            "id": str(uuid4()),
            "stateCode": "CA",
            "entityType": "corporation",
            "taxRate": 0.0525,
            "incomeThreshold": 1000.00,
            "taxThreshold": 100.00
        }

        mock_response = {
            "id": rule_set_id,
            "year": 2025,
            "quarter": "Q1",
            "status": "draft",
            "createdAt": "2025-01-01T10:00:00Z",
            "sourceFile": {
                "id": str(uuid4()),
                "filename": "test.xlsx",
                "fileSize": 1024,
                "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "uploadTimestamp": "2025-01-01T09:00:00Z"
            },
            "validationSummary": {
                "totalIssues": 0,
                "errorCount": 0,
                "warningCount": 0,
                "rulesProcessed": {"withholding": 1, "composite": 0}
            },
            "rules": {
                "withholding": [mock_withholding_rule],
                "composite": []
            }
        }

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail', return_value=mock_response):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}")

        assert response.status_code == 200
        response_data = response.json()

        withholding_rules = response_data["rules"]["withholding"]
        assert len(withholding_rules) == 1

        rule = withholding_rules[0]
        assert "id" in rule
        assert "stateCode" in rule
        assert "entityType" in rule
        assert "taxRate" in rule
        assert "incomeThreshold" in rule
        assert "taxThreshold" in rule

        # Validate field types and constraints
        import uuid
        uuid.UUID(rule["id"])
        assert isinstance(rule["stateCode"], str)
        assert len(rule["stateCode"]) == 2  # State code pattern ^[A-Z]{2}$
        assert rule["entityType"] in [
            "individual", "trust", "estate", "partnership", "corporation", "llc",
            "pension_fund", "endowment", "foundation", "insurance_company", "bank",
            "government", "foreign_government", "sovereign_wealth_fund", "other"
        ]
        assert isinstance(rule["taxRate"], (int, float))
        assert 0 <= rule["taxRate"] <= 1
        assert isinstance(rule["incomeThreshold"], (int, float))
        assert rule["incomeThreshold"] >= 0
        assert isinstance(rule["taxThreshold"], (int, float))
        assert rule["taxThreshold"] >= 0

    def test_detail_composite_rule_schema(self):
        """Test composite rule schema validation"""
        rule_set_id = str(uuid4())

        mock_composite_rule = {
            "id": str(uuid4()),
            "stateCode": "NY",
            "entityType": "partnership",
            "taxRate": 0.0625,
            "incomeThreshold": 1000.00,
            "mandatoryFiling": True,
            "minTaxAmount": 25.00,
            "maxTaxAmount": 10000.00
        }

        mock_response = {
            "id": rule_set_id,
            "year": 2025,
            "quarter": "Q1",
            "status": "draft",
            "createdAt": "2025-01-01T10:00:00Z",
            "sourceFile": {
                "id": str(uuid4()),
                "filename": "test.xlsx",
                "fileSize": 1024,
                "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "uploadTimestamp": "2025-01-01T09:00:00Z"
            },
            "validationSummary": {
                "totalIssues": 0,
                "errorCount": 0,
                "warningCount": 0,
                "rulesProcessed": {"withholding": 0, "composite": 1}
            },
            "rules": {
                "withholding": [],
                "composite": [mock_composite_rule]
            }
        }

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail', return_value=mock_response):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}")

        assert response.status_code == 200
        response_data = response.json()

        composite_rules = response_data["rules"]["composite"]
        assert len(composite_rules) == 1

        rule = composite_rules[0]
        assert "id" in rule
        assert "stateCode" in rule
        assert "entityType" in rule
        assert "taxRate" in rule
        assert "incomeThreshold" in rule
        assert "mandatoryFiling" in rule

        # Validate required fields
        import uuid
        uuid.UUID(rule["id"])
        assert isinstance(rule["mandatoryFiling"], bool)

        # Validate optional fields
        if "minTaxAmount" in rule:
            assert isinstance(rule["minTaxAmount"], (int, float))
            assert rule["minTaxAmount"] >= 0
        if "maxTaxAmount" in rule:
            assert isinstance(rule["maxTaxAmount"], (int, float))
            assert rule["maxTaxAmount"] >= 0
            if "minTaxAmount" in rule:
                assert rule["maxTaxAmount"] >= rule["minTaxAmount"]

    def test_detail_rule_set_not_found(self):
        """Test 404 response when rule set doesn't exist"""
        non_existent_id = str(uuid4())

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail',
                  side_effect=ValueError("Rule set not found")):
            response = self.client.get(f"/api/salt-rules/{non_existent_id}")

        assert response.status_code == 404
        response_data = response.json()

        # Validate error response schema
        assert "error" in response_data
        assert "message" in response_data
        assert isinstance(response_data["error"], str)
        assert isinstance(response_data["message"], str)

    def test_detail_invalid_rule_set_id_format(self):
        """Test 400 response for invalid UUID format"""
        invalid_id = "not-a-uuid"
        response = self.client.get(f"/api/salt-rules/{invalid_id}")

        assert response.status_code == 400
        response_data = response.json()

        # Validate error response schema
        assert "error" in response_data
        assert "message" in response_data

    def test_detail_optional_fields_handling(self):
        """Test handling of optional fields in response"""
        rule_set_id = str(uuid4())

        # Response with minimal required fields only
        minimal_response = {
            "id": rule_set_id,
            "year": 2025,
            "quarter": "Q1",
            "status": "draft",
            "createdAt": "2025-01-01T10:00:00Z",
            "sourceFile": {
                "id": str(uuid4()),
                "filename": "minimal.xlsx",
                "fileSize": 1024,
                "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "uploadTimestamp": "2025-01-01T09:00:00Z"
            },
            "validationSummary": {
                "totalIssues": 0,
                "errorCount": 0,
                "warningCount": 0,
                "rulesProcessed": {"withholding": 0, "composite": 0}
            },
            "rules": {
                "withholding": [],
                "composite": []
            }
        }

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail', return_value=minimal_response):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}")

        assert response.status_code == 200
        response_data = response.json()

        # Should not fail even without optional fields
        assert response_data["id"] == rule_set_id
        assert response_data["status"] == "draft"

        # Optional fields may or may not be present
        optional_fields = ["version", "effectiveDate", "publishedAt", "description", "ruleCount"]
        for field in optional_fields:
            if field in response_data:
                assert response_data[field] is not None

    def test_detail_source_file_optional_fields(self):
        """Test source file optional fields handling"""
        rule_set_id = str(uuid4())

        # Source file with all optional fields
        complete_source_file = {
            "id": str(uuid4()),
            "filename": "complete.xlsx",
            "filepath": "/secure/path/file.xlsx",  # Optional - admin only
            "fileSize": 1048576,
            "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "sha256Hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
            "uploadTimestamp": "2025-01-01T09:00:00Z",
            "uploadedBy": "admin@fundflow.com"
        }

        mock_response = {
            "id": rule_set_id,
            "year": 2025,
            "quarter": "Q1",
            "status": "draft",
            "createdAt": "2025-01-01T10:00:00Z",
            "sourceFile": complete_source_file,
            "validationSummary": {
                "totalIssues": 0,
                "errorCount": 0,
                "warningCount": 0,
                "rulesProcessed": {"withholding": 0, "composite": 0}
            },
            "rules": {"withholding": [], "composite": []}
        }

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail', return_value=mock_response):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}")

        assert response.status_code == 200
        response_data = response.json()

        source_file = response_data["sourceFile"]

        # Validate optional fields if present
        if "filepath" in source_file:
            assert isinstance(source_file["filepath"], str)
        if "sha256Hash" in source_file:
            assert isinstance(source_file["sha256Hash"], str)
            assert len(source_file["sha256Hash"]) == 64  # SHA256 hex length
        if "uploadedBy" in source_file:
            assert isinstance(source_file["uploadedBy"], str)

    def test_detail_empty_rules_arrays(self):
        """Test response with empty rules arrays"""
        rule_set_id = str(uuid4())

        mock_response = {
            "id": rule_set_id,
            "year": 2025,
            "quarter": "Q1",
            "status": "draft",
            "createdAt": "2025-01-01T10:00:00Z",
            "sourceFile": {
                "id": str(uuid4()),
                "filename": "empty.xlsx",
                "fileSize": 1024,
                "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "uploadTimestamp": "2025-01-01T09:00:00Z"
            },
            "validationSummary": {
                "totalIssues": 0,
                "errorCount": 0,
                "warningCount": 0,
                "rulesProcessed": {"withholding": 0, "composite": 0}
            },
            "rules": {
                "withholding": [],
                "composite": []
            }
        }

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail', return_value=mock_response):
            response = self.client.get(f"/api/salt-rules/{rule_set_id}")

        assert response.status_code == 200
        response_data = response.json()

        rules = response_data["rules"]
        assert isinstance(rules["withholding"], list)
        assert isinstance(rules["composite"], list)
        assert len(rules["withholding"]) == 0
        assert len(rules["composite"]) == 0