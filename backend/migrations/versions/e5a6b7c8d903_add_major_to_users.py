"""add major column to users

Revision ID: e5a6b7c8d903
Revises: d4f5a6b7c802
Create Date: 2025-07-11 08:00:00.000000

大学化改造 — 用户表新增专业字段，用于按专业精准推荐课程与服务。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "e5a6b7c8d903"
down_revision = "d4f5a6b7c802"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """users 表新增 major 字段"""
    op.add_column(
        "users",
        sa.Column("major", sa.String(length=100), nullable=True, comment="专业"),
    )


def downgrade() -> None:
    """回滚 — 删除 users.major 字段"""
    op.drop_column("users", "major")
