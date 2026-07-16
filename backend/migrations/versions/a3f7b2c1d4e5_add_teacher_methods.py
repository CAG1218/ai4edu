"""add teacher_methods and classroom_records

Revision ID: a3f7b2c1d4e5
Revises: 61a4199a88b0
Create Date: 2025-07-04 10:00:00.000000

新增 teacher_methods 和 classroom_records 两张表：
- teacher_methods: 存储老师讲授的解题方法/知识点讲解
- classroom_records: 课堂录播视频与板书的结构化记录
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a3f7b2c1d4e5"
down_revision = "61a4199a88b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建 teacher_methods 和 classroom_records 表"""

    # teacher_methods 表
    op.create_table(
        "teacher_methods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=True),
        sa.Column("classroom_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(300), nullable=False, comment="方法标题"),
        sa.Column("content", sa.Text(), nullable=False, comment="方法内容(结构化文本)"),
        sa.Column(
            "method_type",
            sa.String(30),
            nullable=False,
            comment="类型: board_note/video_transcript/textbook_solution/manual",
        ),
        sa.Column("knowledge_points", sa.Text(), nullable=True, comment="关联知识点(JSON数组)"),
        sa.Column("source_resource_id", sa.Integer(), nullable=True, comment="来源资源ID"),
        sa.Column("source_url", sa.String(1000), nullable=True, comment="来源链接"),
        sa.Column("subject", sa.String(50), nullable=False, comment="学科"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"]),
        sa.ForeignKeyConstraint(["source_resource_id"], ["resources.id"]),
        comment="老师方法表 - 存储老师讲授的解题方法/知识点讲解",
    )

    # 索引
    op.create_index("ix_teacher_methods_tenant_id", "teacher_methods", ["tenant_id"])
    op.create_index("ix_teacher_methods_teacher_id", "teacher_methods", ["teacher_id"])
    op.create_index("ix_teacher_methods_course_id", "teacher_methods", ["course_id"])
    op.create_index("ix_teacher_methods_subject", "teacher_methods", ["subject"])

    # classroom_records 表
    op.create_table(
        "classroom_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("classroom_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column(
            "record_type",
            sa.String(20),
            nullable=False,
            comment="类型: video/board_photo/transcript",
        ),
        sa.Column("resource_id", sa.Integer(), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True, comment="转录/OCR文本"),
        sa.Column("segments", sa.Text(), nullable=True, comment="分段时间戳文本(JSON)"),
        sa.Column("knowledge_points", sa.Text(), nullable=True, comment="覆盖知识点(JSON)"),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            comment="状态: pending/processing/ready/failed",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"]),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["resource_id"], ["resources.id"]),
        comment="课堂记录表 - 录播视频与板书的结构化记录",
    )

    # 索引
    op.create_index("ix_classroom_records_tenant_id", "classroom_records", ["tenant_id"])
    op.create_index("ix_classroom_records_classroom_id", "classroom_records", ["classroom_id"])
    op.create_index("ix_classroom_records_course_id", "classroom_records", ["course_id"])


def downgrade() -> None:
    """删除 classroom_records 和 teacher_methods 表"""
    op.drop_index("ix_classroom_records_course_id", table_name="classroom_records")
    op.drop_index("ix_classroom_records_classroom_id", table_name="classroom_records")
    op.drop_index("ix_classroom_records_tenant_id", table_name="classroom_records")
    op.drop_table("classroom_records")

    op.drop_index("ix_teacher_methods_subject", table_name="teacher_methods")
    op.drop_index("ix_teacher_methods_course_id", table_name="teacher_methods")
    op.drop_index("ix_teacher_methods_teacher_id", table_name="teacher_methods")
    op.drop_index("ix_teacher_methods_tenant_id", table_name="teacher_methods")
    op.drop_table("teacher_methods")
