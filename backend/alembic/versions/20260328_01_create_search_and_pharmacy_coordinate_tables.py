"""create search and pharmacy coordinate tables

Revision ID: 20260328_01
Revises: None
Create Date: 2026-03-28 20:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260328_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("query", sa.String(length=512), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pharmacy_coordinates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("normalized_address", sa.String(length=512), nullable=False),
        sa.Column("original_address", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lon", sa.Float(), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=True),
        sa.Column("query", sa.String(length=512), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "normalized_address",
            name="uq_pharmacy_coordinates_normalized_address",
        ),
    )
    op.create_index(
        "ix_pharmacy_coordinates_normalized_address",
        "pharmacy_coordinates",
        ["normalized_address"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pharmacy_coordinates_normalized_address",
        table_name="pharmacy_coordinates",
    )
    op.drop_table("pharmacy_coordinates")
    op.drop_table("search_sessions")
