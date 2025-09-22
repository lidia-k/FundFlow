"""Tests for FileService storage behaviour."""

from pathlib import Path

from src.services.file_service import FileService


def create_temp_file(tmp_path: Path, name: str, size: int = 128) -> Path:
    file_path = tmp_path / name
    file_path.write_bytes(b"a" * size)
    return file_path


def test_store_uploaded_file_success(db_session, tmp_path):
    service = FileService(db_session, storage_root=tmp_path)
    upload = create_temp_file(tmp_path, "rules.xlsx")

    result = service.store_uploaded_file(
        file_path=upload,
        original_filename="rules.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        uploaded_by="admin@fundflow.com",
        year=2025,
        quarter="Q1",
    )

    assert result.error_message is None
    assert result.source_file is not None
    stored_path = Path(result.source_file.filepath)
    assert stored_path.exists()
    assert stored_path.read_bytes() == upload.read_bytes()


def test_store_uploaded_file_rejects_large_files(db_session, tmp_path):
    service = FileService(db_session, storage_root=tmp_path)
    service.max_file_size = 10  # bytes
    upload = create_temp_file(tmp_path, "large.xlsx", size=32)

    result = service.store_uploaded_file(
        file_path=upload,
        original_filename="large.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        uploaded_by="admin@fundflow.com",
        year=2025,
        quarter="Q1",
    )

    assert result.source_file is None
    assert "exceeds" in result.error_message


def test_store_uploaded_file_rejects_invalid_content_type(db_session, tmp_path):
    service = FileService(db_session, storage_root=tmp_path)
    upload = create_temp_file(tmp_path, "rules.csv")

    result = service.store_uploaded_file(
        file_path=upload,
        original_filename="rules.csv",
        content_type="text/csv",
        uploaded_by="admin@fundflow.com",
        year=2025,
        quarter="Q1",
    )

    assert result.source_file is None
    assert "not allowed" in result.error_message


def test_store_uploaded_file_overwrites_existing_record(db_session, tmp_path):
    service = FileService(db_session, storage_root=tmp_path)
    original = create_temp_file(tmp_path, "rules.xlsx", size=16)
    updated = create_temp_file(tmp_path, "rules_new.xlsx", size=32)

    first = service.store_uploaded_file(
        file_path=original,
        original_filename="rules.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        uploaded_by="admin@fundflow.com",
        year=2025,
        quarter="Q1",
    )

    second = service.store_uploaded_file(
        file_path=updated,
        original_filename="rules.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        uploaded_by="admin@fundflow.com",
        year=2025,
        quarter="Q1",
    )

    assert first.source_file is not None
    assert second.source_file is not None
    assert first.source_file.id != second.source_file.id
    stored_path = Path(second.source_file.filepath)
    assert stored_path.exists()
    assert stored_path.read_bytes() == updated.read_bytes()
