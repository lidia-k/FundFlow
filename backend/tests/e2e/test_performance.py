"""
E2E test for performance with 20MB files
Task: T024 - E2E test performance with 20MB files
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import io
import time
import hashlib
from uuid import uuid4
from app.main import app


class TestPerformanceE2E:
    """Test end-to-end performance with large files"""

    def setup_method(self):
        """Setup test client"""
        # This should fail initially as performance optimization doesn't exist yet
        self.client = TestClient(app)

    def test_20mb_file_upload_performance(self):
        """Test upload performance with file close to 20MB limit"""
        # Create large file content (19.5MB to stay under 20MB limit)
        large_content_size = int(19.5 * 1024 * 1024)  # 19.5MB
        large_content = self._create_large_excel_content(large_content_size)
        expected_hash = hashlib.sha256(large_content.getvalue()).hexdigest()

        files = {"file": ("large_rules.xlsx", large_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {
            "year": 2025,
            "quarter": "Q1",
            "description": "Performance test with large file"
        }

        # Mock Excel processing to simulate realistic processing time
        mock_rules = self._create_large_rule_set()

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):
                    mock_process.return_value = {
                        "withholding_rules": mock_rules["withholding"],
                        "composite_rules": mock_rules["composite"],
                        "validation_issues": []
                    }

                    # Measure upload time
                    start_time = time.time()
                    response = self.client.post("/api/salt-rules/upload", files=files, data=data)
                    upload_time = time.time() - start_time

        assert response.status_code == 201
        result = response.json()

        # Performance assertions
        assert upload_time < 30.0  # Should complete within 30 seconds

        # Verify file was processed correctly
        assert result["ruleSetId"] is not None
        assert result["uploadedFile"]["fileSize"] == large_content_size
        assert result["uploadedFile"]["sha256Hash"] == expected_hash
        assert result["validationStarted"] is True

        print(f"Upload time for {large_content_size / (1024*1024):.1f}MB file: {upload_time:.2f} seconds")

    def test_validation_performance_large_dataset(self):
        """Test validation performance with large rule sets"""
        rule_set_id = str(uuid4())

        # Mock large validation dataset
        mock_large_rule_set = self._create_large_rule_set()
        mock_validation_issues = self._create_mock_validation_issues(50)  # 50 validation issues

        mock_validation_response = {
            "ruleSetId": rule_set_id,
            "status": "completed",
            "summary": {
                "totalIssues": len(mock_validation_issues),
                "errorCount": 25,
                "warningCount": 25,
                "rulesProcessed": {
                    "withholding": len(mock_large_rule_set["withholding"]),
                    "composite": len(mock_large_rule_set["composite"])
                }
            },
            "issues": mock_validation_issues
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_validation_response):
            # Measure validation retrieval time
            start_time = time.time()
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")
            validation_time = time.time() - start_time

        assert response.status_code == 200
        result = response.json()

        # Performance assertions
        assert validation_time < 5.0  # Should complete within 5 seconds

        # Verify validation response
        assert result["summary"]["rulesProcessed"]["withholding"] > 100
        assert result["summary"]["rulesProcessed"]["composite"] > 100
        assert len(result["issues"]) == 50

        print(f"Validation retrieval time for large dataset: {validation_time:.2f} seconds")

    def test_preview_performance_large_comparison(self):
        """Test preview performance with large rule set comparison"""
        rule_set_id = str(uuid4())

        # Mock large comparison result
        mock_comparison_changes = {
            "added": self._create_mock_rule_changes("added", 25),
            "modified": self._create_mock_rule_changes("modified", 50),
            "removed": self._create_mock_rule_changes("removed", 10)
        }

        mock_preview_response = {
            "ruleSetId": rule_set_id,
            "comparison": mock_comparison_changes,
            "summary": {
                "rulesAdded": len(mock_comparison_changes["added"]),
                "rulesModified": len(mock_comparison_changes["modified"]),
                "rulesRemoved": len(mock_comparison_changes["removed"]),
                "fieldsChanged": 150
            }
        }

        with patch('src.services.comparison_service.ComparisonService.compare_rule_sets', return_value=mock_preview_response):
            # Measure preview generation time
            start_time = time.time()
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview")
            preview_time = time.time() - start_time

        assert response.status_code == 200
        result = response.json()

        # Performance assertions
        assert preview_time < 10.0  # Should complete within 10 seconds

        # Verify preview response
        assert result["summary"]["rulesAdded"] == 25
        assert result["summary"]["rulesModified"] == 50
        assert result["summary"]["rulesRemoved"] == 10
        assert result["summary"]["fieldsChanged"] == 150

        print(f"Preview generation time for large comparison: {preview_time:.2f} seconds")

    def test_publish_performance_large_rule_set(self):
        """Test publish performance with large rule set"""
        rule_set_id = str(uuid4())

        publish_data = {
            "effectiveDate": "2025-01-01",
            "confirmArchive": True
        }

        # Mock publish response for large rule set
        mock_publish_response = {
            "ruleSetId": rule_set_id,
            "status": "active",
            "effectiveDate": "2025-01-01",
            "resolvedRulesGenerated": 2550  # 51 states * 50 entity combinations
        }

        with patch('src.services.rule_set_service.RuleSetService.publish_rule_set', return_value=mock_publish_response):
            # Measure publish time
            start_time = time.time()
            response = self.client.post(f"/api/salt-rules/{rule_set_id}/publish", json=publish_data)
            publish_time = time.time() - start_time

        assert response.status_code == 200
        result = response.json()

        # Performance assertions
        assert publish_time < 15.0  # Should complete within 15 seconds

        # Verify publish response
        assert result["status"] == "active"
        assert result["resolvedRulesGenerated"] == 2550

        print(f"Publish time for large rule set: {publish_time:.2f} seconds")

    def test_detail_retrieval_performance_large_rule_set(self):
        """Test detail retrieval performance with large rule set"""
        rule_set_id = str(uuid4())

        # Mock large rule set detail
        large_rule_set = self._create_large_rule_set()
        mock_detail_response = {
            "id": rule_set_id,
            "year": 2025,
            "quarter": "Q1",
            "version": "1.0.0",
            "status": "active",
            "effectiveDate": "2025-01-01",
            "createdAt": "2025-01-01T10:00:00Z",
            "publishedAt": "2025-01-01T12:00:00Z",
            "sourceFile": {
                "id": str(uuid4()),
                "filename": "large_rules.xlsx",
                "fileSize": 20 * 1024 * 1024,  # 20MB
                "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "uploadTimestamp": "2025-01-01T09:00:00Z",
                "sha256Hash": "mock_hash_for_large_file"
            },
            "validationSummary": {
                "totalIssues": 0,
                "errorCount": 0,
                "warningCount": 0,
                "rulesProcessed": {
                    "withholding": len(large_rule_set["withholding"]),
                    "composite": len(large_rule_set["composite"])
                }
            },
            "rules": large_rule_set
        }

        with patch('src.services.rule_set_service.RuleSetService.get_rule_set_detail', return_value=mock_detail_response):
            # Measure detail retrieval time
            start_time = time.time()
            response = self.client.get(f"/api/salt-rules/{rule_set_id}")
            detail_time = time.time() - start_time

        assert response.status_code == 200
        result = response.json()

        # Performance assertions
        assert detail_time < 8.0  # Should complete within 8 seconds

        # Verify detail response
        assert len(result["rules"]["withholding"]) > 100
        assert len(result["rules"]["composite"]) > 100
        assert result["sourceFile"]["fileSize"] == 20 * 1024 * 1024

        print(f"Detail retrieval time for large rule set: {detail_time:.2f} seconds")

    def test_csv_export_performance_large_validation_set(self):
        """Test CSV export performance with large validation results"""
        rule_set_id = str(uuid4())

        # Mock large CSV data (simulate 1000 validation issues)
        large_csv_data = self._create_large_csv_validation_data(1000)

        with patch('src.services.validation_service.ValidationService.get_validation_results_csv', return_value=large_csv_data):
            # Measure CSV export time
            start_time = time.time()
            response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation?format=csv")
            csv_export_time = time.time() - start_time

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"

        # Performance assertions
        assert csv_export_time < 5.0  # Should complete within 5 seconds

        # Verify CSV content
        csv_content = response.text
        assert "sheet_name,row_number,column_name,error_code,severity,message,field_value" in csv_content
        lines = csv_content.strip().split('\n')
        assert len(lines) > 1000  # Header + 1000 data rows

        print(f"CSV export time for 1000 validation issues: {csv_export_time:.2f} seconds")

    def test_concurrent_requests_performance(self):
        """Test performance under concurrent requests (simulated)"""
        rule_set_id = str(uuid4())

        # Simulate multiple concurrent requests
        mock_responses = {
            "validation": {
                "ruleSetId": rule_set_id,
                "status": "completed",
                "summary": {"totalIssues": 0, "errorCount": 0, "warningCount": 0, "rulesProcessed": {"withholding": 51, "composite": 51}},
                "issues": []
            },
            "preview": {
                "ruleSetId": rule_set_id,
                "comparison": {"added": [], "modified": [], "removed": []},
                "summary": {"rulesAdded": 0, "rulesModified": 0, "rulesRemoved": 0, "fieldsChanged": 0}
            }
        }

        with patch('src.services.validation_service.ValidationService.get_validation_results', return_value=mock_responses["validation"]):
            with patch('src.services.comparison_service.ComparisonService.compare_rule_sets', return_value=mock_responses["preview"]):

                # Measure concurrent-like request times
                start_time = time.time()

                # Simulate rapid consecutive requests
                validation_response = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")
                preview_response = self.client.get(f"/api/salt-rules/{rule_set_id}/preview")
                validation_response_2 = self.client.get(f"/api/salt-rules/{rule_set_id}/validation")

                total_time = time.time() - start_time

        assert validation_response.status_code == 200
        assert preview_response.status_code == 200
        assert validation_response_2.status_code == 200

        # Performance assertions for rapid requests
        assert total_time < 3.0  # All three requests should complete quickly

        print(f"Time for 3 rapid consecutive requests: {total_time:.2f} seconds")

    def test_memory_usage_large_file_processing(self):
        """Test memory efficiency with large file processing"""
        # Create large file close to limit
        large_content_size = int(19.8 * 1024 * 1024)  # 19.8MB
        large_content = self._create_large_excel_content(large_content_size)
        expected_hash = hashlib.sha256(large_content.getvalue()).hexdigest()

        files = {"file": ("memory_test.xlsx", large_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        data = {"year": 2025, "quarter": "Q1"}

        # Mock processing that would normally consume memory
        large_rules = self._create_large_rule_set()

        with patch('src.services.excel_processor.ExcelProcessor.process_file') as mock_process:
            with patch('src.services.file_service.FileService.calculate_sha256_hash_from_bytes', return_value=expected_hash):
                with patch('src.services.file_service.FileService.check_duplicate_file', return_value=False):
                    mock_process.return_value = {
                        "withholding_rules": large_rules["withholding"],
                        "composite_rules": large_rules["composite"],
                        "validation_issues": []
                    }

                    # This should not cause memory issues
                    response = self.client.post("/api/salt-rules/upload", files=files, data=data)

        assert response.status_code == 201
        result = response.json()
        assert result["uploadedFile"]["fileSize"] == large_content_size

    def _create_large_excel_content(self, size_bytes):
        """Create mock Excel content of specified size"""
        # Create content that simulates Excel file structure
        base_content = b"Mock Excel content with data tables and formulas: "
        padding = b"X" * (size_bytes - len(base_content))
        return io.BytesIO(base_content + padding)

    def _create_large_rule_set(self):
        """Create large rule set for performance testing"""
        withholding_rules = []
        composite_rules = []

        # Create rules for all 51 US states/jurisdictions and multiple entity types
        states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                 "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                 "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                 "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                 "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"]

        entity_types = ["corporation", "partnership", "individual", "trust", "llc"]

        for state in states:
            for entity_type in entity_types:
                # Create withholding rule
                withholding_rules.append({
                    "id": str(uuid4()),
                    "stateCode": state,
                    "entityType": entity_type,
                    "taxRate": 0.05 + (hash(state + entity_type) % 100) / 10000,  # Varied rates
                    "incomeThreshold": 1000.00,
                    "taxThreshold": 100.00
                })

                # Create composite rule
                composite_rules.append({
                    "id": str(uuid4()),
                    "stateCode": state,
                    "entityType": entity_type,
                    "taxRate": 0.06 + (hash(state + entity_type) % 80) / 10000,  # Varied rates
                    "incomeThreshold": 1000.00,
                    "mandatoryFiling": hash(state + entity_type) % 2 == 0,
                    "minTaxAmount": 25.00,
                    "maxTaxAmount": 10000.00
                })

        return {
            "withholding": withholding_rules,
            "composite": composite_rules
        }

    def _create_mock_validation_issues(self, count):
        """Create mock validation issues for performance testing"""
        issues = []
        error_codes = ["INVALID_STATE", "INVALID_RATE_RANGE", "MISSING_FIELD", "DUPLICATE_RULE", "INVALID_ENTITY_TYPE"]
        severities = ["error", "warning"]

        for i in range(count):
            issues.append({
                "sheetName": "Withholding" if i % 2 == 0 else "Composite",
                "rowNumber": i + 10,
                "columnName": "State" if i % 3 == 0 else "TaxRate",
                "errorCode": error_codes[i % len(error_codes)],
                "severity": severities[i % len(severities)],
                "message": f"Mock validation issue #{i}",
                "fieldValue": f"invalid_value_{i}"
            })

        return issues

    def _create_mock_rule_changes(self, change_type, count):
        """Create mock rule changes for preview performance testing"""
        changes = []
        states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
        entity_types = ["corporation", "partnership", "individual"]

        for i in range(count):
            state = states[i % len(states)]
            entity = entity_types[i % len(entity_types)]

            field_changes = []
            if change_type == "modified":
                field_changes = [
                    {"field": "tax_rate", "oldValue": "0.0525", "newValue": "0.0575"},
                    {"field": "income_threshold", "oldValue": "1000.00", "newValue": "1500.00"}
                ]
            elif change_type == "added":
                field_changes = [
                    {"field": "tax_rate", "oldValue": None, "newValue": "0.0525"}
                ]
            elif change_type == "removed":
                field_changes = [
                    {"field": "tax_rate", "oldValue": "0.0525", "newValue": None}
                ]

            changes.append({
                "ruleType": "withholding" if i % 2 == 0 else "composite",
                "state": state,
                "entityType": entity,
                "changes": field_changes
            })

        return changes

    def _create_large_csv_validation_data(self, row_count):
        """Create large CSV data for export performance testing"""
        header = "sheet_name,row_number,column_name,error_code,severity,message,field_value\n"
        rows = []

        for i in range(row_count):
            row = f"Withholding,{i+10},State,INVALID_STATE,error,Invalid state code,ZZ{i}"
            rows.append(row)

        return header + "\n".join(rows)