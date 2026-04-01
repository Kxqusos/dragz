"""add user terms acceptance timestamp

Revision ID: 20260331_02
Revises: 20260331_01
Create Date: 2026-03-31 12:15:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260331_02"
down_revision = "20260331_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("accepted_terms_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "accepted_terms_at")
