"""
Integration tests for SALT Matrix_v1.2.xlsx file upload and processing.
Tests the complete workflow using the actual sample file with Withholding and Composite sheets.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from app.main import app
from src.database.connection import Base, get_db
# Import all models to ensure tables are created
from src.models import (
    SaltRuleSet, RuleSetStatus, WithholdingRule, CompositeRule,
    SourceFile, ValidationIssue, StateEntityTaxRuleResolved,
    Quarter, USJurisdiction, User, UserSession, Investor, Distribution
)


class TestSaltMatrixV12Integration:
    """Integration tests for SALT Matrix v1.2 file processing"""

    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Setup isolated test database for each test"""
        # Create in-memory SQLite database for testing with thread safety
        engine = create_engine(
            "sqlite:///:memory:",
            echo=False,
            connect_args={
                "check_same_thread": False,
                "isolation_level": None
            }
        )
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        # Create all tables
        Base.metadata.create_all(bind=engine)

        # Override the dependency to use test database
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

        # Cleanup
        self.test_db.close()
        app.dependency_overrides.clear()

    @pytest.fixture
    def salt_matrix_file_path(self):
        """Get path to the actual SALT Matrix v1.2 file"""
        file_path = Path("./data/samples/input/SALT Matrix_v1.2.xlsx")
        assert file_path.exists(), f"SALT Matrix file not found at {file_path}"
        return file_path

    def test_upload_salt_matrix_v12_success(self, salt_matrix_file_path):
        """Test successful upload of SALT Matrix v1.2 file"""
        # Read the actual Excel file
        with open(salt_matrix_file_path, 'rb') as f:
            file_content = f.read()

        # Prepare upload request
        files = {
            "file": ("SALT Matrix_v1.2.xlsx", file_content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {
            "year": 2025,
            "quarter": "Q1",
            "description": "SALT Matrix v1.2 test upload with Withholding and Composite sheets"
        }

        # Mock file service to avoid file system operations
        with patch('src.services.file_service.FileService.store_uploaded_file') as mock_store:
            # Mock successful file storage
            mock_source_file = SourceFile(
                id="test-source-file-id",
                filename="SALT Matrix_v1.2.xlsx",
                filepath="/tmp/test_file.xlsx",
                file_size=len(file_content),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                sha256_hash="test_hash_value"
            )

            mock_store_result = type('StorageResult', (), {
                'source_file': mock_source_file,
                'is_duplicate': False,
                'error_message': None,
                'existing_source_file': None
            })()

            mock_store.return_value = mock_store_result

            # Mock Excel processor to simulate actual processing
            with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
                # Mock processing result with sample rules from both sheets
                mock_withholding_rules = [
                    WithholdingRule(
                        rule_set_id="test-rule-set-id",
                        state_code=USJurisdiction.CA,
                        entity_type="Corporation",
                        tax_rate=0.0525,
                        income_threshold=1000.00,
                        tax_threshold=100.00
                    ),
                    WithholdingRule(
                        rule_set_id="test-rule-set-id",
                        state_code=USJurisdiction.NY,
                        entity_type="Partnership",
                        tax_rate=0.0625,
                        income_threshold=1000.00,
                        tax_threshold=100.00
                    )
                ]

                mock_composite_rules = [
                    CompositeRule(
                        rule_set_id="test-rule-set-id",
                        state_code=USJurisdiction.CA,
                        entity_type="Corporation",
                        tax_rate=0.0875,
                        income_threshold=1000.00,
                        mandatory_filing=True,
                        min_tax_amount=25.00,
                        max_tax_amount=10000.00
                    ),
                    CompositeRule(
                        rule_set_id="test-rule-set-id",
                        state_code=USJurisdiction.NY,
                        entity_type="Partnership",
                        tax_rate=0.0925,
                        income_threshold=1000.00,
                        mandatory_filing=True,
                        min_tax_amount=50.00,
                        max_tax_amount=15000.00
                    )
                ]

                mock_processing_result = type('ProcessingResult', (), {
                    'withholding_rules': mock_withholding_rules,
                    'composite_rules': mock_composite_rules,
                    'validation_issues': []
                })()

                mock_process.return_value = mock_processing_result

                # Perform the upload
                response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        # Verify successful upload
        assert response.status_code == 201
        response_data = response.json()

        # Validate response structure
        assert "rule_set_id" in response_data
        assert "status" in response_data
        assert "uploaded_file" in response_data
        assert "validation_started" in response_data
        assert "message" in response_data

        # Validate response values
        assert response_data["status"] == "draft"
        assert response_data["validation_started"] is True
        assert "successfully" in response_data["message"].lower()

        # Validate uploaded file information
        uploaded_file = response_data["uploaded_file"]
        assert uploaded_file["filename"] == "SALT Matrix_v1.2.xlsx"
        assert uploaded_file["file_size"] == len(file_content)
        assert "sha256_hash" in uploaded_file
        assert "upload_timestamp" in uploaded_file

    def test_upload_salt_matrix_v12_database_persistence(self, salt_matrix_file_path):
        """Test that SALT Matrix v1.2 upload persists correctly to database"""
        # Read the actual Excel file
        with open(salt_matrix_file_path, 'rb') as f:
            file_content = f.read()

        files = {
            "file": ("SALT Matrix_v1.2.xlsx", file_content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {
            "year": 2025,
            "quarter": "Q1",
            "description": "Database persistence test for SALT Matrix v1.2"
        }

        # Mock services to focus on database persistence
        with patch('src.services.file_service.FileService.store_uploaded_file') as mock_store:
            with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
                # Setup mocks
                mock_source_file = SourceFile(
                    id="test-source-file-id",
                    filename="SALT Matrix_v1.2.xlsx",
                    filepath="/tmp/test_file.xlsx",
                    file_size=len(file_content),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    sha256_hash="test_hash_value"
                )

                mock_store_result = type('StorageResult', (), {
                    'source_file': mock_source_file,
                    'is_duplicate': False,
                    'error_message': None
                })()
                mock_store.return_value = mock_store_result

                mock_processing_result = type('ProcessingResult', (), {
                    'withholding_rules': [],
                    'composite_rules': [],
                    'validation_issues': []
                })()
                mock_process.return_value = mock_processing_result

                # Perform upload
                response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        # Verify database persistence
        assert response.status_code == 201
        rule_set_id = response.json()["rule_set_id"]

        # Query database to verify rule set was created
        rule_set = self.test_db.query(SaltRuleSet).filter(SaltRuleSet.id == rule_set_id).first()
        assert rule_set is not None
        assert rule_set.year == 2025
        assert rule_set.quarter == Quarter.Q1
        assert rule_set.status == RuleSetStatus.DRAFT
        assert rule_set.description == "Database persistence test for SALT Matrix v1.2"
        assert rule_set.version == "1.0.0"
        assert rule_set.created_by == "admin@fundflow.com"  # Based on API implementation

    def test_salt_matrix_v12_file_validation(self, salt_matrix_file_path):
        """Test file validation for SALT Matrix v1.2"""
        # Test with actual file
        with open(salt_matrix_file_path, 'rb') as f:
            file_content = f.read()

        files = {
            "file": ("SALT Matrix_v1.2.xlsx", file_content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {"year": 2025, "quarter": "Q1"}

        # Mock services for validation focus
        with patch('src.services.file_service.FileService.store_uploaded_file') as mock_store:
            with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
                # Setup successful mocks
                mock_source_file = SourceFile(
                    id="test-source-file-id",
                    filename="SALT Matrix_v1.2.xlsx",
                    filepath="/tmp/test_file.xlsx",
                    file_size=len(file_content),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    sha256_hash="test_hash_value"
                )

                mock_store_result = type('StorageResult', (), {
                    'source_file': mock_source_file,
                    'is_duplicate': False,
                    'error_message': None
                })()
                mock_store.return_value = mock_store_result

                # Mock validation issues (warnings but not errors)
                mock_validation_issues = [
                    ValidationIssue(
                        rule_set_id="test-rule-set-id",
                        sheet_name="Withholding",
                        row_number=5,
                        column_name="TaxRate",
                        error_code="UNUSUAL_RATE",
                        severity="warning",
                        message="Tax rate 0% is unusual for this state",
                        field_value="0.0000"
                    )
                ]

                mock_processing_result = type('ProcessingResult', (), {
                    'withholding_rules': [],
                    'composite_rules': [],
                    'validation_issues': mock_validation_issues
                })()
                mock_process.return_value = mock_processing_result

                # Perform upload
                response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        # Should succeed even with warnings
        assert response.status_code == 201
        assert response.json()["validation_started"] is True

    def test_salt_matrix_v12_duplicate_detection(self, salt_matrix_file_path):
        """Test duplicate detection for SALT Matrix v1.2"""
        with open(salt_matrix_file_path, 'rb') as f:
            file_content = f.read()

        files = {
            "file": ("SALT Matrix_v1.2.xlsx", file_content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {"year": 2025, "quarter": "Q1"}

        # Mock duplicate detection
        with patch('src.services.file_service.FileService.store_uploaded_file') as mock_store:
            # Mock existing source file for duplicate detection
            existing_source_file = SourceFile(
                id="existing-source-file-id",
                filename="SALT Matrix_v1.2.xlsx",
                filepath="/tmp/existing_file.xlsx",
                file_size=len(file_content),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                sha256_hash="duplicate_hash_value"
            )

            mock_store_result = type('StorageResult', (), {
                'source_file': None,
                'is_duplicate': True,
                'error_message': None,
                'existing_source_file': existing_source_file
            })()
            mock_store.return_value = mock_store_result

            # Mock finding existing rule set
            with patch('src.services.file_service.FileService.find_existing_rule_set_by_hash') as mock_find:
                mock_find.return_value = {
                    "id": "existing-rule-set-id",
                    "year": 2025,
                    "quarter": "Q1"
                }

                # Perform upload
                response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        # Should return 409 Conflict for duplicate
        assert response.status_code == 409
        response_data = response.json()

        # Validate conflict response structure
        assert "error" in response_data
        assert "message" in response_data
        assert "existing_rule_set_id" in response_data
        assert "duplicate_detection" in response_data

        # Validate values
        assert response_data["error"] == "DUPLICATE_FILE"
        assert "Duplicate file detected" in response_data["message"]
        assert response_data["existing_rule_set_id"] == "existing-rule-set-id"

        duplicate_detection = response_data["duplicate_detection"]
        assert "sha256_hash" in duplicate_detection
        assert "uploaded_at" in duplicate_detection

    def test_salt_matrix_v12_invalid_parameters(self, salt_matrix_file_path):
        """Test parameter validation with SALT Matrix v1.2 file"""
        with open(salt_matrix_file_path, 'rb') as f:
            file_content = f.read()

        files = {
            "file": ("SALT Matrix_v1.2.xlsx", file_content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }

        # Test invalid year
        data = {"year": 2019, "quarter": "Q1"}  # Below minimum year
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400
        assert "Year must be between 2020 and 2030" in response.json()["detail"]

        # Test invalid quarter
        files["file"] = ("SALT Matrix_v1.2.xlsx", file_content,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        data = {"year": 2025, "quarter": "Q5"}  # Invalid quarter
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400
        assert "Quarter must be one of: Q1, Q2, Q3, Q4" in response.json()["detail"]

        # Test description too long
        files["file"] = ("SALT Matrix_v1.2.xlsx", file_content,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        data = {
            "year": 2025,
            "quarter": "Q1",
            "description": "a" * 501  # Over 500 character limit
        }
        response = self.client.post("/api/salt-rules/upload", files=files, data=data)
        assert response.status_code == 400
        assert "Description must be 500 characters or less" in response.json()["detail"]

    def test_salt_matrix_v12_file_size_limit(self):
        """Test file size limit with oversized mock file"""
        # Create oversized file content (over 20MB)
        oversized_content = b"x" * (20 * 1024 * 1024 + 1)  # 20MB + 1 byte

        files = {
            "file": ("Large_SALT_Matrix.xlsx", oversized_content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {"year": 2025, "quarter": "Q1"}

        response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        # Should reject file that's too large
        assert response.status_code == 413
        assert "File size exceeds 20MB limit" in response.json()["detail"]

    def test_salt_matrix_v12_wrong_file_type(self):
        """Test rejection of non-Excel files"""
        # Try uploading a text file instead of Excel
        text_content = b"This is not an Excel file"

        files = {
            "file": ("not_excel.txt", text_content, "text/plain")
        }
        data = {"year": 2025, "quarter": "Q1"}

        response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        # Should reject non-Excel file
        assert response.status_code == 400
        assert "File must be Excel format (.xlsx or .xlsm)" in response.json()["detail"]

    def test_salt_matrix_v12_validation_endpoint(self, salt_matrix_file_path):
        """Test validation results endpoint after SALT Matrix v1.2 upload"""
        # First upload the file
        with open(salt_matrix_file_path, 'rb') as f:
            file_content = f.read()

        files = {
            "file": ("SALT Matrix_v1.2.xlsx", file_content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {"year": 2025, "quarter": "Q1"}

        # Mock successful upload
        with patch('src.services.file_service.FileService.store_uploaded_file') as mock_store:
            with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
                mock_source_file = SourceFile(
                    id="test-source-file-id",
                    filename="SALT Matrix_v1.2.xlsx",
                    filepath="/tmp/test_file.xlsx",
                    file_size=len(file_content),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    sha256_hash="test_hash_value"
                )

                mock_store_result = type('StorageResult', (), {
                    'source_file': mock_source_file,
                    'is_duplicate': False,
                    'error_message': None
                })()
                mock_store.return_value = mock_store_result

                mock_processing_result = type('ProcessingResult', (), {
                    'withholding_rules': [],
                    'composite_rules': [],
                    'validation_issues': []
                })()
                mock_process.return_value = mock_processing_result

                upload_response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert upload_response.status_code == 201
        rule_set_id = upload_response.json()["rule_set_id"]

        # Mock validation service for validation endpoint test
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
                    "row_number": 10,
                    "column_name": "TaxRate",
                    "error_code": "UNUSUAL_RATE",
                    "severity": "warning",
                    "message": "Tax rate 0% is unusual for CA",
                    "field_value": "0.0000"
                }
            ]
        }

        # Test validation endpoint
        with patch('src.services.validation_service.ValidationService.get_validation_results') as mock_validation:
            mock_validation.return_value = mock_validation_result

            validation_response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

        assert validation_response.status_code == 200
        validation_data = validation_response.json()

        # Validate response structure
        assert validation_data["rule_set_id"] == rule_set_id
        assert validation_data["status"] == "completed"
        assert "summary" in validation_data
        assert "issues" in validation_data

        # Validate summary
        summary = validation_data["summary"]
        assert summary["total_issues"] == 1
        assert summary["error_count"] == 0
        assert summary["warning_count"] == 1
        assert "rules_processed" in summary

        # Validate issues
        assert len(validation_data["issues"]) == 1
        issue = validation_data["issues"][0]
        assert issue["sheet_name"] == "Withholding"
        assert issue["severity"] == "warning"
        assert "unusual" in issue["message"].lower()

    def test_salt_matrix_v12_preview_endpoint(self, salt_matrix_file_path):
        """Test preview endpoint after SALT Matrix v1.2 upload"""
        # Upload file first (similar setup as validation test)
        with open(salt_matrix_file_path, 'rb') as f:
            file_content = f.read()

        files = {
            "file": ("SALT Matrix_v1.2.xlsx", file_content,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        }
        data = {"year": 2025, "quarter": "Q1"}

        # Mock upload
        with patch('src.services.file_service.FileService.store_uploaded_file') as mock_store:
            with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
                mock_source_file = SourceFile(
                    id="test-source-file-id",
                    filename="SALT Matrix_v1.2.xlsx",
                    filepath="/tmp/test_file.xlsx",
                    file_size=len(file_content),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    sha256_hash="test_hash_value"
                )

                mock_store_result = type('StorageResult', (), {
                    'source_file': mock_source_file,
                    'is_duplicate': False,
                    'error_message': None
                })()
                mock_store.return_value = mock_store_result

                mock_processing_result = type('ProcessingResult', (), {
                    'withholding_rules': [],
                    'composite_rules': [],
                    'validation_issues': []
                })()
                mock_process.return_value = mock_processing_result

                upload_response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        rule_set_id = upload_response.json()["rule_set_id"]

        # Mock preview service
        mock_preview_result = {
            "rule_set_id": rule_set_id,
            "comparison": {
                "added": [
                    {
                        "rule_type": "withholding",
                        "state": "CA",
                        "entity_type": "Corporation",
                        "changes": [
                            {"field": "tax_rate", "old_value": None, "new_value": "0.0525"}
                        ]
                    }
                ],
                "modified": [],
                "removed": []
            },
            "summary": {
                "rules_added": 25,
                "rules_modified": 0,
                "rules_removed": 0,
                "fields_changed": 25
            }
        }

        # Test preview endpoint
        with patch('src.services.comparison_service.ComparisonService.get_rule_set_preview') as mock_preview:
            mock_preview.return_value = mock_preview_result

            preview_response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview")

        assert preview_response.status_code == 200
        preview_data = preview_response.json()

        # Validate response structure
        assert preview_data["rule_set_id"] == rule_set_id
        assert "comparison" in preview_data
        assert "summary" in preview_data

        # Validate comparison
        comparison = preview_data["comparison"]
        assert "added" in comparison
        assert "modified" in comparison
        assert "removed" in comparison
        assert len(comparison["added"]) == 1

        # Validate summary
        summary = preview_data["summary"]
        assert summary["rules_added"] == 25
        assert summary["rules_modified"] == 0
        assert summary["rules_removed"] == 0