"""add_company_request_phone

Revision ID: 1f2e3d4c5b6a
Revises: 7dee48e42e24
Create Date: 2026-04-16 17:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1f2e3d4c5b6a"
down_revision: str | None = "7dee48e42e24"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.add_column("company_creation_requests", sa.Column("phone", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("company_creation_requests", "phone")
