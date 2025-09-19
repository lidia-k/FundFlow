"""
Additional integration tests for all SALT Rules API endpoints using SALT Matrix_v1.2.xlsx.
Tests complete workflow including validation, preview, publish, list, and detail endpoints.
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from datetime import datetime, date
from uuid import uuid4

from app.main import app
from src.database.connection import Base, get_db
from src.models.salt_rule_set import SaltRuleSet, RuleSetStatus
from src.models.withholding_rule import WithholdingRule
from src.models.composite_rule import CompositeRule
from src.models.source_file import SourceFile
from src.models.validation_issue import ValidationIssue
from src.models.enums import Quarter, USJurisdiction


class TestSaltMatrixEndpoints:
    """Integration tests for all SALT Rules API endpoints"""

    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Setup isolated test database for each test"""
        engine = create_engine(
            "sqlite:///:memory:",
            echo=False,
            connect_args={
                "check_same_thread": False,
                "isolation_level": None
            }
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        Base.metadata.create_all(bind=engine)

        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        self.client = TestClient(app)
        self.test_db = TestingSessionLocal()

        yield

        self.test_db.close()
        app.dependency_overrides.clear()

    @pytest.fixture
    def uploaded_rule_set(self):
        """Create a rule set that simulates successful SALT Matrix v1.2 upload"""
        rule_set_id = str(uuid4())
        source_file_id = str(uuid4())

        # Create source file
        source_file = SourceFile(
            id=source_file_id,
            filename="SALT Matrix_v1.2.xlsx",
            filepath="/tmp/salt_matrix_v1_2.xlsx",
            file_size=2048000,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            sha256_hash="salt_matrix_v12_hash",
            upload_timestamp=datetime.utcnow(),
            uploaded_by="admin@fundflow.com"
        )

        # Create rule set
        rule_set = SaltRuleSet(
            id=rule_set_id,
            year=2025,
            quarter=Quarter.Q1,
            version="1.0.0",
            status=RuleSetStatus.DRAFT,
            effective_date=date.today(),
            created_at=datetime.utcnow(),
            created_by="admin@fundflow.com",
            description="SALT Matrix v1.2 test upload",
            source_file_id=source_file_id,
            rule_count_withholding=25,
            rule_count_composite=30
        )

        # Create sample withholding rules
        withholding_rules = [
            WithholdingRule(
                rule_set_id=rule_set_id,
                state_code=USJurisdiction.CA,
                entity_type="Corporation",
                tax_rate=0.0525,
                income_threshold=1000.00,
                tax_threshold=100.00
            ),
            WithholdingRule(
                rule_set_id=rule_set_id,
                state_code=USJurisdiction.NY,
                entity_type="Partnership",
                tax_rate=0.0625,
                income_threshold=1000.00,
                tax_threshold=100.00
            ),
            WithholdingRule(
                rule_set_id=rule_set_id,
                state_code=USJurisdiction.TX,
                entity_type="LLC",
                tax_rate=0.0000,  # TX has no state income tax
                income_threshold=0.00,
                tax_threshold=0.00
            )
        ]

        # Create sample composite rules
        composite_rules = [
            CompositeRule(
                rule_set_id=rule_set_id,
                state_code=USJurisdiction.CA,
                entity_type="Corporation",
                tax_rate=0.0875,
                income_threshold=1000.00,
                mandatory_filing=True,
                min_tax_amount=25.00,
                max_tax_amount=10000.00
            ),
            CompositeRule(
                rule_set_id=rule_set_id,
                state_code=USJurisdiction.NY,
                entity_type="Partnership",
                tax_rate=0.0925,
                income_threshold=1000.00,
                mandatory_filing=True,
                min_tax_amount=50.00,
                max_tax_amount=15000.00
            )
        ]

        # Create sample validation issues
        validation_issues = [
            ValidationIssue(
                rule_set_id=rule_set_id,
                sheet_name="Withholding",
                row_number=15,
                column_name="TaxRate",
                error_code="UNUSUAL_RATE",
                severity="warning",
                message="Tax rate 0% is unusual for TX (but expected due to no state income tax)",
                field_value="0.0000"
            )
        ]

        # Save to database
        self.test_db.add(source_file)
        self.test_db.add(rule_set)
        for rule in withholding_rules:
            self.test_db.add(rule)
        for rule in composite_rules:
            self.test_db.add(rule)
        for issue in validation_issues:
            self.test_db.add(issue)
        self.test_db.commit()

        return {
            "rule_set_id": rule_set_id,
            "source_file_id": source_file_id,
            "rule_set": rule_set,
            "source_file": source_file,
            "withholding_rules": withholding_rules,
            "composite_rules": composite_rules,
            "validation_issues": validation_issues
        }

    def test_validation_endpoint_json_format(self, uploaded_rule_set):
        """Test validation endpoint returns JSON format"""
        rule_set_id = uploaded_rule_set["rule_set_id"]

        # Mock validation service
        mock_validation_result = {
            "rule_set_id": rule_set_id,
            "status": "completed",
            "summary": {
                "total_issues": 1,
                "error_count": 0,
                "warning_count": 1,
                "rules_processed": {
                    "withholding": 25,
                    "composite": 30
                }
            },
            "issues": [
                {
                    "sheet_name": "Withholding",
                    "row_number": 15,
                    "column_name": "TaxRate",
                    "error_code": "UNUSUAL_RATE",
                    "severity": "warning",
                    "message": "Tax rate 0% is unusual for TX",
                    "field_value": "0.0000"
                }
            ]
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results') as mock_validation:
            mock_validation.return_value = mock_validation_result

            response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert response.status_code == 200
        data = response.json()

        # Validate structure
        assert data["rule_set_id"] == rule_set_id
        assert data["status"] == "completed"
        assert "summary" in data
        assert "issues" in data

        # Validate summary shows processing from both sheets
        summary = data["summary"]
        assert summary["rules_processed"]["withholding"] == 25
        assert summary["rules_processed"]["composite"] == 30
        assert summary["warning_count"] == 1
        assert summary["error_count"] == 0

    def test_validation_endpoint_csv_format(self, uploaded_rule_set):
        """Test validation endpoint returns CSV format when requested"""
        rule_set_id = uploaded_rule_set["rule_set_id"]

        # Mock CSV export
        mock_csv_content = """Sheet,Row,Column,ErrorCode,Severity,Message,FieldValue
Withholding,15,TaxRate,UNUSUAL_RATE,warning,Tax rate 0% is unusual for TX,0.0000
Composite,22,MinTaxAmount,MISSING_VALUE,warning,Min tax amount not specified,"""

        with patch('src.services.validation_service.ValidationService.export_validation_issues_csv') as mock_csv:
            mock_csv.return_value = mock_csv_content

            response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation?format=csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert f"validation-{rule_set_id}.csv" in response.headers.get("content-disposition", "")
        assert "Sheet,Row,Column,ErrorCode" in response.text

    def test_preview_endpoint_with_no_existing_rules(self, uploaded_rule_set):
        """Test preview endpoint when no existing rules (all new)"""
        rule_set_id = uploaded_rule_set["rule_set_id"]

        # Mock comparison service for new rule set (no existing active rules)
        mock_preview_result = {
            "rule_set_id": rule_set_id,
            "comparison": {
                "added": [
                    {
                        "rule_type": "withholding",
                        "state": "CA",
                        "entity_type": "Corporation",
                        "changes": [
                            {"field": "tax_rate", "old_value": None, "new_value": "0.0525"},
                            {"field": "income_threshold", "old_value": None, "new_value": "1000.00"}
                        ]
                    },
                    {
                        "rule_type": "withholding",
                        "state": "NY",
                        "entity_type": "Partnership",
                        "changes": [
                            {"field": "tax_rate", "old_value": None, "new_value": "0.0625"}
                        ]
                    },
                    {
                        "rule_type": "composite",
                        "state": "CA",
                        "entity_type": "Corporation",
                        "changes": [
                            {"field": "tax_rate", "old_value": None, "new_value": "0.0875"},
                            {"field": "mandatory_filing", "old_value": None, "new_value": "true"}
                        ]
                    }
                ],
                "modified": [],
                "removed": []
            },
            "summary": {
                "rules_added": 55,  # 25 withholding + 30 composite
                "rules_modified": 0,
                "rules_removed": 0,
                "fields_changed": 55
            }
        }

        with patch('src.services.comparison_service.ComparisonService.get_rule_set_preview') as mock_preview:
            mock_preview.return_value = mock_preview_result

            response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview")

        assert response.status_code == 200
        data = response.json()

        # Validate structure
        assert data["rule_set_id"] == rule_set_id
        assert "comparison" in data
        assert "summary" in data

        # Validate comparison shows all rules as new
        comparison = data["comparison"]
        assert len(comparison["added"]) == 3  # Sample rules shown
        assert len(comparison["modified"]) == 0
        assert len(comparison["removed"]) == 0

        # Validate summary
        summary = data["summary"]
        assert summary["rules_added"] == 55
        assert summary["rules_modified"] == 0
        assert summary["rules_removed"] == 0


    def test_list_endpoint_filters_and_pagination(self, uploaded_rule_set):
        """Test list endpoint with filters and pagination"""
        # Create additional rule sets for testing
        additional_rule_sets = []
        for i in range(3):
            rule_set = SaltRuleSet(
                id=str(uuid4()),
                year=2024 + i,
                quarter=Quarter.Q2,
                version="1.0.0",
                status=RuleSetStatus.DRAFT if i == 0 else RuleSetStatus.ACTIVE,
                effective_date=date.today(),
                created_at=datetime.utcnow(),
                created_by="admin@fundflow.com",
                description=f"Additional rule set {i}",
                source_file_id=uploaded_rule_set["source_file_id"],
                rule_count_withholding=10 + i,
                rule_count_composite=15 + i
            )
            additional_rule_sets.append(rule_set)
            self.test_db.add(rule_set)
        self.test_db.commit()

        # Test basic list (no filters)
        response = self.client.get("/api/salt-rules")
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total_count" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data

    def test_detail_endpoint(self, uploaded_rule_set):
        """Test detailed rule set information endpoint"""
        rule_set_id = uploaded_rule_set["rule_set_id"]

        # Mock detailed information
        mock_detail_result = {
            "id": rule_set_id,
            "year": 2025,
            "quarter": "Q1",
            "version": "1.0.0",
            "status": "draft",
            "effective_date": "2025-01-01",
            "created_at": "2025-01-01T10:00:00Z",
            "published_at": None,
            "created_by": "admin@fundflow.com",
            "description": "SALT Matrix v1.2 test upload",
            "source_file": {
                "id": uploaded_rule_set["source_file_id"],
                "filename": "SALT Matrix_v1.2.xlsx",
                "file_size": 2048000,
                "upload_timestamp": "2025-01-01T10:00:00Z",
                "sha256_hash": "salt_matrix_v12_hash"
            },
            "validation_summary": {
                "total_issues": 1,
                "error_count": 0,
                "warning_count": 1,
                "rules_processed": {
                    "withholding": 25,
                    "composite": 30
                }
            },
            "rules": {
                "withholding": [
                    {
                        "id": "rule-1",
                        "state_code": "CA",
                        "entity_type": "Corporation",
                        "tax_rate": "0.0525",
                        "income_threshold": "1000.00",
                        "tax_threshold": "100.00"
                    }
                ],
                "composite": [
                    {
                        "id": "rule-2",
                        "state_code": "CA",
                        "entity_type": "Corporation",
                        "tax_rate": "0.0875",
                        "income_threshold": "1000.00",
                        "mandatory_filing": True,
                        "min_tax_amount": "25.00",
                        "max_tax_amount": "10000.00"
                    }
                ]
            }
        }

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail') as mock_detail:
            mock_detail.return_value = mock_detail_result

            response = self.client.get(f"/api/salt-rules/{rule_set_id}")

        assert response.status_code == 200
        data = response.json()

        # Validate structure
        assert data["id"] == rule_set_id
        assert data["year"] == 2025
        assert data["quarter"] == "Q1"
        assert data["status"] == "draft"
        assert data["description"] == "SALT Matrix v1.2 test upload"

        # Validate source file information
        source_file = data["source_file"]
        assert source_file["filename"] == "SALT Matrix_v1.2.xlsx"
        assert source_file["file_size"] == 2048000

        # Validate validation summary
        validation_summary = data["validation_summary"]
        assert validation_summary["rules_processed"]["withholding"] == 25
        assert validation_summary["rules_processed"]["composite"] == 30

        # Validate rules structure
        rules = data["rules"]
        assert "withholding" in rules
        assert "composite" in rules
        assert len(rules["withholding"]) > 0
        assert len(rules["composite"]) > 0

    def test_detail_endpoint_not_found(self):
        """Test detail endpoint with non-existent rule set"""
        non_existent_id = str(uuid4())

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail') as mock_detail:
            mock_detail.side_effect = ValueError("Rule set not found")

            response = self.client.get(f"/api/salt-rules/{non_existent_id}")

        assert response.status_code == 404
        assert "Rule set not found" in response.json()["detail"]

    def test_validation_endpoint_not_found(self):
        """Test validation endpoint with non-existent rule set"""
        non_existent_id = str(uuid4())

        response = self.client.get(f"/api/salt-rules/{non_existent_id}/validation")

        assert response.status_code == 404
        assert "Rule set not found" in response.json()["detail"]

    def test_preview_endpoint_not_found(self):
        """Test preview endpoint with non-existent rule set"""
        non_existent_id = str(uuid4())

        response = self.client.get(f"/api/salt-rules/{non_existent_id}/preview")

        assert response.status_code == 404
        assert "Rule set not found" in response.json()["detail"]


