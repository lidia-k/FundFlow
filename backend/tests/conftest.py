"""Pytest configuration for backend tests."""

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
SRC_DIR = BACKEND_DIR / "src"
APP_DIR = BACKEND_DIR / "app"

for path in (str(PROJECT_ROOT), str(BACKEND_DIR), str(SRC_DIR), str(APP_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

from src.database.connection import Base


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()
