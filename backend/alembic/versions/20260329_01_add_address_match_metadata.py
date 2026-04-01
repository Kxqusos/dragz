"""add address match metadata to pharmacy coordinates

Revision ID: 20260329_01
Revises: 20260328_01
Create Date: 2026-03-29 12:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260329_01"
down_revision = "20260328_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pharmacy_coordinates", sa.Column("matching_key", sa.String(length=512), nullable=True))
    op.add_column("pharmacy_coordinates", sa.Column("match_strategy", sa.String(length=64), nullable=True))
    op.add_column("pharmacy_coordinates", sa.Column("confidence_tier", sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column("pharmacy_coordinates", "confidence_tier")
    op.drop_column("pharmacy_coordinates", "match_strategy")
    op.drop_column("pharmacy_coordinates", "matching_key")
