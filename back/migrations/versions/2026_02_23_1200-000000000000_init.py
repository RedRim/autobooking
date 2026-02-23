"""init

Revision ID: 000000000000
Revises:
Create Date: 2026-02-23 12:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "000000000000"
down_revision: str | None = None
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
