"""add v2 models: llm_usage_logs, tenant_quotas, agent_exports + field additions

Revision ID: c8e2a4f7b901
Revises: a3f7b2c1d4e5
Create Date: 2025-07-10 10:00:00.000000

v2 新增:
- llm_usage_logs: LLM 调用用量日志
- tenant_quotas: 租户配额配置
- agent_exports: 对话导出记录
- classroom_records 新增: file_url / provider / error_msg / updated_at
- teacher_methods 新增: recommended_model
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c8e2a4f7b901"
down_revision = "a3f7b2c1d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建 v2 新表 + 字段"""

    # 1. llm_usage_logs 表
    op.create_table(
        "llm_usage_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=False, comment="模型提供商"),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_usage_logs_tenant_id", "llm_usage_logs", ["tenant_id"])
    op.create_index("ix_llm_usage_logs_user_id", "llm_usage_logs", ["user_id"])
    op.create_index("ix_llm_usage_logs_session_id", "llm_usage_logs", ["session_id"])
    op.create_index("ix_llm_usage_logs_created_at", "llm_usage_logs", ["created_at"])

    # 2. tenant_quotas 表
    op.create_table(
        "tenant_quotas",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("daily_token_limit", sa.Integer(), nullable=False, server_default="500000"),
        sa.Column("monthly_token_limit", sa.Integer(), nullable=False, server_default="10000000"),
        sa.Column("strategy", sa.String(length=20), nullable=False, server_default="latency"),
        sa.Column("sticky_model", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id"),
    )
    op.create_index("ix_tenant_quotas_tenant_id", "tenant_quotas", ["tenant_id"])

    # 3. agent_exports 表
    op.create_table(
        "agent_exports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("export_format", sa.String(length=20), nullable=False, comment="pdf/markdown"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("file_key", sa.String(length=500), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_msg", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("expired_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["agent_sessions.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_exports_session_id", "agent_exports", ["session_id"])
    op.create_index("ix_agent_exports_tenant_id", "agent_exports", ["tenant_id"])
    op.create_index("ix_agent_exports_user_id", "agent_exports", ["user_id"])
    op.create_index("ix_agent_exports_created_at", "agent_exports", ["created_at"])

    # 4. classroom_records 新增字段
    op.add_column("classroom_records", sa.Column("file_url", sa.String(length=500), nullable=True, comment="MinIO 文件路径"))
    op.add_column("classroom_records", sa.Column("provider", sa.String(length=50), nullable=True, comment="OCR/ASR provider"))
    op.add_column("classroom_records", sa.Column("error_msg", sa.Text(), nullable=True, comment="错误信息"))
    op.add_column("classroom_records", sa.Column("updated_at", sa.DateTime(), nullable=True, comment="更新时间"))

    # 5. teacher_methods 新增字段
    op.add_column("teacher_methods", sa.Column("recommended_model", sa.String(length=100), nullable=True, comment="推荐模型"))


def downgrade() -> None:
    """回滚 v2 变更"""
    # teacher_methods
    op.drop_column("teacher_methods", "recommended_model")

    # classroom_records
    op.drop_column("classroom_records", "updated_at")
    op.drop_column("classroom_records", "error_msg")
    op.drop_column("classroom_records", "provider")
    op.drop_column("classroom_records", "file_url")

    # agent_exports
    op.drop_index("ix_agent_exports_created_at", table_name="agent_exports")
    op.drop_index("ix_agent_exports_user_id", table_name="agent_exports")
    op.drop_index("ix_agent_exports_tenant_id", table_name="agent_exports")
    op.drop_index("ix_agent_exports_session_id", table_name="agent_exports")
    op.drop_table("agent_exports")

    # tenant_quotas
    op.drop_index("ix_tenant_quotas_tenant_id", table_name="tenant_quotas")
    op.drop_table("tenant_quotas")

    # llm_usage_logs
    op.drop_index("ix_llm_usage_logs_created_at", table_name="llm_usage_logs")
    op.drop_index("ix_llm_usage_logs_session_id", table_name="llm_usage_logs")
    op.drop_index("ix_llm_usage_logs_user_id", table_name="llm_usage_logs")
    op.drop_index("ix_llm_usage_logs_tenant_id", table_name="llm_usage_logs")
    op.drop_table("llm_usage_logs")
