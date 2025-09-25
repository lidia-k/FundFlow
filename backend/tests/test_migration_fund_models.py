"""Migration regression tests for fund model introduction."""

from datetime import datetime
from pathlib import Path

import pytest

try:
    from alembic.config import Config

    from alembic import command
except ImportError:  # pragma: no cover - environment dependent
    pytest.skip("Alembic is not available", allow_module_level=True)
from sqlalchemy import Engine, create_engine, text


def _bootstrap_legacy_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE investors (
                    id INTEGER PRIMARY KEY,
                    investor_name VARCHAR(255) NOT NULL,
                    investor_entity_type VARCHAR(255) NOT NULL,
                    investor_tax_state VARCHAR(255) NOT NULL,
                    created_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE user_sessions (
                    session_id VARCHAR(36) PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    upload_filename VARCHAR(255),
                    original_filename VARCHAR(255),
                    file_size INTEGER,
                    status VARCHAR(32),
                    progress_percentage INTEGER,
                    created_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE distributions (
                    id INTEGER PRIMARY KEY,
                    investor_id INTEGER NOT NULL,
                    session_id VARCHAR(36) NOT NULL,
                    fund_code VARCHAR(50) NOT NULL,
                    period_quarter VARCHAR(2) NOT NULL,
                    period_year INTEGER NOT NULL,
                    jurisdiction VARCHAR(10) NOT NULL,
                    amount NUMERIC(12,2) NOT NULL,
                    composite_exemption BOOLEAN,
                    withholding_exemption BOOLEAN,
                    composite_tax_amount NUMERIC(12,2),
                    withholding_tax_amount NUMERIC(12,2),
                    created_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO investors (id, investor_name, investor_entity_type, investor_tax_state, created_at)
                VALUES (1, 'Legacy LP', 'PARTNERSHIP', 'NY', :created_at)
                """
            ),
            {"created_at": datetime.utcnow()},
        )
        conn.execute(
            text(
                """
                INSERT INTO user_sessions (session_id, user_id, upload_filename, original_filename, file_size, status, progress_percentage, created_at)
                VALUES ('session-legacy', 1, 'legacy.xlsx', 'legacy.xlsx', 12345, 'completed', 100, :created_at)
                """
            ),
            {"created_at": datetime.utcnow()},
        )
        conn.execute(
            text(
                """
                INSERT INTO distributions (
                    id,
                    investor_id,
                    session_id,
                    fund_code,
                    period_quarter,
                    period_year,
                    jurisdiction,
                    amount,
                    composite_exemption,
                    withholding_exemption,
                    created_at
                )
                VALUES (
                    1,
                    1,
                    'session-legacy',
                    'FUNDLEG',
                    'Q2',
                    2023,
                    'NY',
                    5000.00,
                    0,
                    0,
                    :created_at
                )
                """
            ),
            {"created_at": datetime.utcnow()},
        )


def test_upgrade_migrates_period_metadata(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{db_path}")
    _bootstrap_legacy_schema(engine)

    backend_dir = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    command.upgrade(alembic_cfg, "head")

    with engine.connect() as conn:
        funds = conn.execute(
            text("SELECT fund_code, period_quarter, period_year FROM funds")
        )
        fund_row = funds.fetchone()
        assert fund_row == ("FUNDLEG", "Q2", 2023)

        distribution_columns = {
            row[1] for row in conn.execute(text("PRAGMA table_info('distributions')"))
        }
        assert "period_quarter" not in distribution_columns
        assert "period_year" not in distribution_columns

        dist_row = conn.execute(
            text(
                "SELECT fund_code, jurisdiction, amount FROM distributions WHERE id = 1"
            )
        ).fetchone()
        assert dist_row == ("FUNDLEG", "NY", 5000.0)

        commitments = conn.execute(
            text("SELECT COUNT(*) FROM investor_fund_commitments")
        )
        assert commitments.fetchone()[0] == 0

        sources = conn.execute(text("SELECT COUNT(*) FROM fund_source_data"))
        assert sources.fetchone()[0] == 0

    command.downgrade(alembic_cfg, "base")
