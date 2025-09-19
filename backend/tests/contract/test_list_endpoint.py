"""
Contract tests for GET /api/salt-rules endpoint
Task: T019 - Contract test GET /api/salt-rules
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from uuid import uuid4
from app.main import app


class TestListEndpointContract:
    """Test list endpoint API contract compliance"""

    def setup_method(self):
        """Setup test client"""
        # This should fail initially as the endpoint doesn't exist yet
        self.client = TestClient(app)

    def test_list_endpoint_exists(self):
        """Test that list endpoint exists and accepts GET"""
        response = self.client.get("/api/salt-rules")

        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_list_success_response_schema(self):
        """Test successful list response matches OpenAPI schema"""
        # Mock rule set service response
        mock_rule_sets = [
            {
                "id": str(uuid4()),
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
                    "withholding": 51,
                    "composite": 51
                }
            },
            {
                "id": str(uuid4()),
                "year": 2024,
                "quarter": "Q4",
                "version": "2.1.0",
                "status": "archived",
                "effectiveDate": "2024-10-01",
                "createdAt": "2024-09-15T10:00:00Z",
                "publishedAt": "2024-10-01T08:00:00Z",
                "createdBy": "admin@fundflow.com",
                "ruleCount": {
                    "withholding": 51,
                    "composite": 51
                }
            }
        ]

        mock_pagination = {
            "page": 1,
            "limit": 20,
            "total": 2,
            "totalPages": 1,
            "hasNext": False,
            "hasPrevious": False
        }

        mock_response = {
            "items": mock_rule_sets,
            "pagination": mock_pagination
        }

        with patch('src.services.rule_set_service.RuleSetService.list_rule_sets', return_value=mock_response):
            response = self.client.get("/api/salt-rules")

        assert response.status_code == 200
        response_data = response.json()

        # Validate response schema according to OpenAPI spec
        assert "items" in response_data
        assert "pagination" in response_data
        assert isinstance(response_data["items"], list)

        # Validate pagination schema
        pagination = response_data["pagination"]
        assert "page" in pagination
        assert "limit" in pagination
        assert "total" in pagination
        assert "totalPages" in pagination
        assert "hasNext" in pagination
        assert "hasPrevious" in pagination
        assert isinstance(pagination["page"], int)
        assert isinstance(pagination["limit"], int)
        assert isinstance(pagination["total"], int)
        assert isinstance(pagination["totalPages"], int)
        assert isinstance(pagination["hasNext"], bool)
        assert isinstance(pagination["hasPrevious"], bool)

        # Validate rule set summary schema
        if len(response_data["items"]) > 0:
            rule_set = response_data["items"][0]
            assert "id" in rule_set
            assert "year" in rule_set
            assert "quarter" in rule_set
            assert "status" in rule_set
            assert "createdAt" in rule_set

            # Validate required fields
            import uuid
            uuid.UUID(rule_set["id"])
            assert isinstance(rule_set["year"], int)
            assert rule_set["quarter"] in ["Q1", "Q2", "Q3", "Q4"]
            assert rule_set["status"] in ["draft", "active", "archived"]

            # Validate optional fields
            if "version" in rule_set:
                assert isinstance(rule_set["version"], str)
            if "effectiveDate" in rule_set:
                from datetime import datetime
                datetime.strptime(rule_set["effectiveDate"], "%Y-%m-%d")
            if "publishedAt" in rule_set:
                datetime.fromisoformat(rule_set["publishedAt"].replace("Z", "+00:00"))
            if "ruleCount" in rule_set:
                rule_count = rule_set["ruleCount"]
                assert "withholding" in rule_count
                assert "composite" in rule_count
                assert isinstance(rule_count["withholding"], int)
                assert isinstance(rule_count["composite"], int)

    def test_list_status_filter_validation(self):
        """Test status query parameter validation"""
        # Valid status values
        valid_statuses = ["draft", "active", "archived"]

        for status in valid_statuses:
            with patch('src.services.rule_set_service.RuleSetService.list_rule_sets'):
                response = self.client.get(f"/api/salt-rules?status={status}")
            assert response.status_code in [200, 404]  # Not schema validation error

        # Invalid status value
        response = self.client.get("/api/salt-rules?status=invalid")
        assert response.status_code == 400

        response_data = response.json()
        assert "error" in response_data
        assert "message" in response_data

    def test_list_year_filter_validation(self):
        """Test year query parameter validation"""
        # Valid year values
        valid_years = [2020, 2025, 2030]

        for year in valid_years:
            with patch('src.services.rule_set_service.RuleSetService.list_rule_sets'):
                response = self.client.get(f"/api/salt-rules?year={year}")
            assert response.status_code in [200, 404]

        # Invalid year (string)
        response = self.client.get("/api/salt-rules?year=invalid")
        assert response.status_code == 400

        # Invalid year (out of range) - depends on implementation
        # response = self.client.get("/api/salt-rules?year=1999")
        # assert response.status_code == 400

    def test_list_quarter_filter_validation(self):
        """Test quarter query parameter validation"""
        # Valid quarter values
        valid_quarters = ["Q1", "Q2", "Q3", "Q4"]

        for quarter in valid_quarters:
            with patch('src.services.rule_set_service.RuleSetService.list_rule_sets'):
                response = self.client.get(f"/api/salt-rules?quarter={quarter}")
            assert response.status_code in [200, 404]

        # Invalid quarter value
        response = self.client.get("/api/salt-rules?quarter=Q5")
        assert response.status_code == 400

    def test_list_pagination_parameters(self):
        """Test pagination query parameters validation"""
        # Valid pagination parameters
        valid_params = [
            {"page": 1, "limit": 20},
            {"page": 2, "limit": 10},
            {"page": 5, "limit": 50},
            {"page": 1, "limit": 100}  # Max limit
        ]

        for params in valid_params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            with patch('src.services.rule_set_service.RuleSetService.list_rule_sets'):
                response = self.client.get(f"/api/salt-rules?{query_string}")
            assert response.status_code in [200, 404]

        # Invalid pagination parameters
        invalid_params = [
            {"page": 0},  # Page must be >= 1
            {"page": -1},
            {"limit": 0},  # Limit must be >= 1
            {"limit": -1},
            {"limit": 101},  # Limit must be <= 100
            {"page": "invalid"},
            {"limit": "invalid"}
        ]

        for params in invalid_params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            response = self.client.get(f"/api/salt-rules?{query_string}")
            assert response.status_code == 400

    def test_list_default_pagination_values(self):
        """Test default pagination values according to OpenAPI spec"""
        mock_response = {
            "items": [],
            "pagination": {
                "page": 1,  # Default page
                "limit": 20,  # Default limit
                "total": 0,
                "totalPages": 0,
                "hasNext": False,
                "hasPrevious": False
            }
        }

        with patch('src.services.rule_set_service.RuleSetService.list_rule_sets', return_value=mock_response) as mock_list:
            response = self.client.get("/api/salt-rules")

        assert response.status_code == 200
        response_data = response.json()

        pagination = response_data["pagination"]
        assert pagination["page"] == 1
        assert pagination["limit"] == 20

    def test_list_combined_filters(self):
        """Test combining multiple filter parameters"""
        params = {
            "status": "active",
            "year": 2025,
            "quarter": "Q1",
            "page": 1,
            "limit": 10
        }

        query_string = "&".join([f"{k}={v}" for k, v in params.items()])

        with patch('src.services.rule_set_service.RuleSetService.list_rule_sets') as mock_list:
            response = self.client.get(f"/api/salt-rules?{query_string}")

        assert response.status_code in [200, 404]

        # Verify filters were passed to service
        if response.status_code == 200:
            mock_list.assert_called_once()

    def test_list_empty_result_set(self):
        """Test response when no rule sets match filters"""
        mock_response = {
            "items": [],
            "pagination": {
                "page": 1,
                "limit": 20,
                "total": 0,
                "totalPages": 0,
                "hasNext": False,
                "hasPrevious": False
            }
        }

        with patch('src.services.rule_set_service.RuleSetService.list_rule_sets', return_value=mock_response):
            response = self.client.get("/api/salt-rules")

        assert response.status_code == 200
        response_data = response.json()

        assert len(response_data["items"]) == 0
        assert response_data["pagination"]["total"] == 0
        assert response_data["pagination"]["totalPages"] == 0

    def test_list_pagination_navigation(self):
        """Test pagination navigation flags"""
        # Test different pagination scenarios
        pagination_scenarios = [
            # First page with more pages
            {
                "page": 1, "limit": 10, "total": 25, "totalPages": 3,
                "hasNext": True, "hasPrevious": False
            },
            # Middle page
            {
                "page": 2, "limit": 10, "total": 25, "totalPages": 3,
                "hasNext": True, "hasPrevious": True
            },
            # Last page
            {
                "page": 3, "limit": 10, "total": 25, "totalPages": 3,
                "hasNext": False, "hasPrevious": True
            },
            # Single page
            {
                "page": 1, "limit": 20, "total": 5, "totalPages": 1,
                "hasNext": False, "hasPrevious": False
            }
        ]

        for pagination in pagination_scenarios:
            mock_response = {
                "items": [],
                "pagination": pagination
            }

            with patch('src.services.rule_set_service.RuleSetService.list_rule_sets', return_value=mock_response):
                response = self.client.get(f"/api/salt-rules?page={pagination['page']}&limit={pagination['limit']}")

            assert response.status_code == 200
            response_data = response.json()

            resp_pagination = response_data["pagination"]
            assert resp_pagination["hasNext"] == pagination["hasNext"]
            assert resp_pagination["hasPrevious"] == pagination["hasPrevious"]

    def test_list_rule_count_schema(self):
        """Test rule count object schema validation"""
        mock_rule_set = {
            "id": str(uuid4()),
            "year": 2025,
            "quarter": "Q1",
            "status": "active",
            "createdAt": "2025-01-01T10:00:00Z",
            "ruleCount": {
                "withholding": 51,
                "composite": 51
            }
        }

        mock_response = {
            "items": [mock_rule_set],
            "pagination": {
                "page": 1, "limit": 20, "total": 1, "totalPages": 1,
                "hasNext": False, "hasPrevious": False
            }
        }

        with patch('src.services.rule_set_service.RuleSetService.list_rule_sets', return_value=mock_response):
            response = self.client.get("/api/salt-rules")

        assert response.status_code == 200
        response_data = response.json()

        rule_set = response_data["items"][0]
        rule_count = rule_set["ruleCount"]

        assert isinstance(rule_count["withholding"], int)
        assert isinstance(rule_count["composite"], int)
        assert rule_count["withholding"] >= 0
        assert rule_count["composite"] >= 0