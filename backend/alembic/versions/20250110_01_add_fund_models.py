"""Add fund models and refactor distributions schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Tuple

import sqlalchemy as sa
from alembic import op
from backend.src.models.enums import USJurisdiction

# revision identifiers, used by Alembic.
revision = "20250110_01_add_fund_models"
down_revision = None
branch_labels = None
depends_on = None


FUNDS_TABLE = "funds"
FUND_SOURCE_TABLE = "fund_source_data"
INVESTOR_FUND_TABLE = "investor_fund_commitments"
DISTRIBUTIONS_TABLE = "distributions"


def _insert_existing_funds(connection: sa.engine.Connection) -> None:
    metadata = sa.MetaData()
    distributions = sa.Table(
        DISTRIBUTIONS_TABLE,
        metadata,
        sa.Column("fund_code", sa.String(length=50)),
        sa.Column("period_quarter", sa.String(length=2)),
        sa.Column("period_year", sa.Integer()),
    )
    funds = sa.Table(
        FUNDS_TABLE,
        metadata,
        sa.Column("fund_code", sa.String(length=50)),
        sa.Column("period_quarter", sa.String(length=2)),
        sa.Column("period_year", sa.Integer()),
        sa.Column("created_at", sa.DateTime()),
    )

    rows: Iterable[Tuple[Any, ...]] = connection.execute(
        sa.select(
            sa.distinct(
                distributions.c.fund_code,
                distributions.c.period_quarter,
                distributions.c.period_year,
            )
        )
    )

    seen = set()
    for fund_code, quarter, year in rows:
        if not fund_code or not quarter or year is None:
            continue
        key = (fund_code, quarter, year)
        if key in seen:
            continue
        seen.add(key)
        connection.execute(
            funds.insert().values(
                fund_code=fund_code,
                period_quarter=quarter,
                period_year=year,
                created_at=datetime.utcnow(),
            )
        )


def upgrade() -> None:
    op.create_table(
        FUNDS_TABLE,
        sa.Column("fund_code", sa.String(length=50), primary_key=True),
        sa.Column("period_quarter", sa.String(length=2), nullable=False),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_fund_period_unique",
        FUNDS_TABLE,
        ["fund_code", "period_quarter", "period_year"],
        unique=True,
    )

    op.create_table(
        FUND_SOURCE_TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fund_code", sa.String(length=50), sa.ForeignKey("funds.fund_code"), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("state_jurisdiction", sa.Enum(USJurisdiction, name="usjurisdiction"), nullable=False),
        sa.Column("fund_share_percentage", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("total_distribution_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("user_sessions.session_id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_fund_source_unique",
        FUND_SOURCE_TABLE,
        ["fund_code", "company_name", "state_jurisdiction"],
        unique=True,
    )
    op.create_index(
        "idx_fund_source_lookup",
        FUND_SOURCE_TABLE,
        ["fund_code", "state_jurisdiction"],
    )

    op.create_table(
        INVESTOR_FUND_TABLE,
        sa.Column("investor_id", sa.Integer(), sa.ForeignKey("investors.id"), primary_key=True),
        sa.Column("fund_code", sa.String(length=50), sa.ForeignKey("funds.fund_code"), primary_key=True),
        sa.Column("commitment_percentage", sa.Numeric(precision=6, scale=4), nullable=False),
        sa.Column("effective_date", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_commitment_lookup", INVESTOR_FUND_TABLE, ["fund_code"])

    connection = op.get_bind()
    _insert_existing_funds(connection)

    with op.batch_alter_table(DISTRIBUTIONS_TABLE) as batch_op:
        batch_op.drop_index("idx_distribution_unique")
        batch_op.create_foreign_key(
            "fk_distributions_fund_code",
            FUNDS_TABLE,
            ["fund_code"],
            ["fund_code"],
            ondelete="CASCADE",
        )
        batch_op.drop_column("period_quarter")
        batch_op.drop_column("period_year")
        batch_op.create_index(
            "idx_distribution_unique",
            ["investor_id", "fund_code", "jurisdiction"],
            unique=True,
        )


def downgrade() -> None:
    with op.batch_alter_table(DISTRIBUTIONS_TABLE) as batch_op:
        batch_op.drop_index("idx_distribution_unique")
        batch_op.add_column(sa.Column("period_year", sa.Integer(), nullable=False, server_default="2000"))
        batch_op.add_column(sa.Column("period_quarter", sa.String(length=2), nullable=False, server_default="Q1"))
        batch_op.drop_constraint("fk_distributions_fund_code", type_="foreignkey")
        batch_op.create_index(
            "idx_distribution_unique",
            [
                "investor_id",
                "fund_code",
                "period_quarter",
                "period_year",
                "jurisdiction",
            ],
            unique=True,
        )

    connection = op.get_bind()
    metadata = sa.MetaData()
    funds = sa.Table(
        FUNDS_TABLE,
        metadata,
        sa.Column("fund_code", sa.String(length=50)),
        sa.Column("period_quarter", sa.String(length=2)),
        sa.Column("period_year", sa.Integer()),
    )
    distributions = sa.Table(
        DISTRIBUTIONS_TABLE,
        metadata,
        sa.Column("fund_code", sa.String(length=50)),
        sa.Column("period_quarter", sa.String(length=2)),
        sa.Column("period_year", sa.Integer()),
    )

    # Repopulate period columns from funds table
    select_stmt = sa.select(
        distributions.c.fund_code,
        funds.c.period_quarter,
        funds.c.period_year,
    ).select_from(
        distributions.join(funds, distributions.c.fund_code == funds.c.fund_code)
    )

    results = connection.execute(select_stmt).fetchall()
    for fund_code, quarter, year in results:
        connection.execute(
            sa.update(distributions)
            .where(distributions.c.fund_code == fund_code)
            .values(period_quarter=quarter, period_year=year)
        )

    op.drop_table(INVESTOR_FUND_TABLE)
    op.drop_index("idx_fund_source_lookup", table_name=FUND_SOURCE_TABLE)
    op.drop_index("idx_fund_source_unique", table_name=FUND_SOURCE_TABLE)
    op.drop_table(FUND_SOURCE_TABLE)
    op.drop_index("idx_fund_period_unique", table_name=FUNDS_TABLE)
    op.drop_table(FUNDS_TABLE)
