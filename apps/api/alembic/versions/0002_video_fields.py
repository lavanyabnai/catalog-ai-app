"""video_fields — add video_pending_hero to asset_bundles and daily_video_cap to tenants

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "asset_bundles",
        sa.Column(
            "video_pending_hero",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "tenants",
        sa.Column("daily_video_cap", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tenants", "daily_video_cap")
    op.drop_column("asset_bundles", "video_pending_hero")
