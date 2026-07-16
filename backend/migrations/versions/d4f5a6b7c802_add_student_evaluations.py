"""add student_evaluations table

Revision ID: d4f5a6b7c802
Revises: c8e2a4f7b901
Create Date: 2025-07-10 12:00:00.000000

学生成长档案 — 教师对学生的评价表
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d4f5a6b7c802"
down_revision = "c8e2a4f7b901"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建 student_evaluations 表"""
    op.create_table(
        "student_evaluations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("evaluation_type", sa.String(length=30), nullable=False, comment="评价类型: overall/academic/attitude/improvement"),
        sa.Column("rating", sa.Integer(), nullable=False, comment="评分1-5星"),
        sa.Column("content", sa.Text(), nullable=False, comment="评价内容"),
        sa.Column("suggestion", sa.Text(), nullable=True, comment="学习建议"),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default="true", comment="是否对学生可见"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_evaluations_tenant_id", "student_evaluations", ["tenant_id"])
    op.create_index("ix_student_evaluations_student_id", "student_evaluations", ["student_id"])
    op.create_index("ix_student_evaluations_teacher_id", "student_evaluations", ["teacher_id"])
    op.create_index("ix_student_evaluations_course_id", "student_evaluations", ["course_id"])


def downgrade() -> None:
    """回滚 — 删除 student_evaluations 表"""
    op.drop_index("ix_student_evaluations_course_id", table_name="student_evaluations")
    op.drop_index("ix_student_evaluations_teacher_id", table_name="student_evaluations")
    op.drop_index("ix_student_evaluations_student_id", table_name="student_evaluations")
    op.drop_index("ix_student_evaluations_tenant_id", table_name="student_evaluations")
    op.drop_table("student_evaluations")
