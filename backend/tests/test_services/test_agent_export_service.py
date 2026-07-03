"""AgentExportService 测试 —— AI 智能体中心 v2

测试 Markdown / PDF 生成逻辑，不依赖真实 MinIO 和 DB。
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.agent_export_service import AgentExportService


@pytest.fixture
def mock_session():
    """模拟 AgentSession 对象。"""
    session = MagicMock()
    session.title = "导数复习"
    session.agent_type = "tutor"
    session.scene_type = "review"
    session.model_name = "deepseek-chat"
    session.message_count = 2
    session.total_tokens = 1500
    session.created_at = datetime(2025, 7, 3, 10, 0, 0)
    session.last_message_at = datetime(2025, 7, 3, 10, 30, 0)
    return session


@pytest.fixture
def mock_messages():
    """模拟 AgentMessage 列表。"""
    msg1 = MagicMock()
    msg1.role = "user"
    msg1.content = "老师，导数这道题怎么做？"
    msg1.model_name = None
    msg1.metadata_json = None
    msg1.created_at = datetime(2025, 7, 3, 10, 0, 0)

    msg2 = MagicMock()
    msg2.role = "assistant"
    msg2.content = "这道题用定义法来解..."
    msg2.model_name = "deepseek-chat"
    msg2.metadata_json = '{"citations": [{"title": "课堂笔记", "source_url": "http://example.com", "type": "note"}]}'
    msg2.created_at = datetime(2025, 7, 3, 10, 1, 0)
    return [msg1, msg2]


@pytest.fixture
def service():
    return AgentExportService(db=AsyncMock())


@pytest.mark.asyncio
async def test_create_export_record(service):
    """应创建 pending 状态的导出记录。"""
    export_record = MagicMock()

    with patch.object(service.db, "add") as mock_add, \
         patch.object(service.db, "flush", new_callable=AsyncMock) as mock_flush:
        from app.models.export import AgentExport

        result = await service.create_export_record(
            session_id=1, tenant_id=1, user_id=1, export_format="pdf"
        )
        mock_add.assert_called_once()
        mock_flush.assert_awaited_once()
        assert result.export_format == "pdf"
        assert result.status == "pending"


def test_generate_markdown_contains_title_and_messages(service, mock_session, mock_messages):
    """Markdown 应包含会话标题和消息内容。"""
    md_bytes = service._generate_markdown(mock_session, mock_messages)
    md_text = md_bytes.decode("utf-8")
    assert "# 导数复习" in md_text
    assert "老师，导数这道题怎么做？" in md_text
    assert "定义法" in md_text
    assert "课堂笔记" in md_text


def test_generate_markdown_role_labels(service, mock_session, mock_messages):
    """Markdown 应正确标识用户和助手角色。"""
    md_bytes = service._generate_markdown(mock_session, mock_messages)
    md_text = md_bytes.decode("utf-8")
    assert "用户" in md_text
    assert "助手" in md_text


def test_generate_pdf_returns_bytes(service, mock_session, mock_messages):
    """PDF 生成应返回非空字节。"""
    pdf_bytes = service._generate_pdf(mock_session, mock_messages)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


@pytest.mark.asyncio
async def test_get_download_url_completed_file(service):
    """已完成的导出记录应返回预签名 URL。"""
    export_record = MagicMock()
    export_record.status = "completed"
    export_record.file_key = "exports/1/1/test.pdf"
    export_record.tenant_id = 1

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = export_record
    service.db.execute = AsyncMock(return_value=mock_result)

    with patch.object(service, "_get_presigned_url", return_value="http://minio.test/signed"):
        url, expired_at = await service.get_download_url(1, 1)
        assert url == "http://minio.test/signed"


@pytest.mark.asyncio
async def test_get_download_url_not_completed_raises(service):
    """未完成的导出记录应抛出异常。"""
    export_record = MagicMock()
    export_record.status = "pending"
    export_record.tenant_id = 1

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = export_record
    service.db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError) as exc:
        await service.get_download_url(1, 1)
    assert "未完成" in str(exc.value)


@pytest.mark.asyncio
async def test_get_download_url_wrong_tenant_raises(service):
    """不属于该租户的记录应抛出异常。"""
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    service.db.execute = AsyncMock(return_value=mock_result)

    with pytest.raises(ValueError) as exc:
        await service.get_download_url(1, 2)
    assert "不存在" in str(exc.value)
