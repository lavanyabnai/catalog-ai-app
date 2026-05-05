"""Make clerk_user_id nullable and drop unique constraint.

Revision ID: 0003
Revises: 0002
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("users", "clerk_user_id", nullable=True)
    # PostgreSQL names the implicit unique constraint <table>_<col>_key
    op.drop_constraint("users_clerk_user_id_key", "users", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("users_clerk_user_id_key", "users", ["clerk_user_id"])
    op.alter_column("users", "clerk_user_id", nullable=False)
