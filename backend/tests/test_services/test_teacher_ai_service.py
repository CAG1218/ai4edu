"""Tests for the independent teacher-workbench AI chain."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.teacher_ai_service import TeacherAIService


def test_render_context_contains_teacher_materials() -> None:
    service = TeacherAIService(AsyncMock())
    course = SimpleNamespace(id=7, name="高等数学", grade="大一", semester="2026秋")
    plan = SimpleNamespace(
        course_id=7,
        title="微积分教案",
        status="published",
        objectives='["理解导数"]',
        materials='["讲义"]',
        content="先复习极限，再讲解导数。",
    )
    diagnosis = SimpleNamespace(
        course_id=7,
        title="单元诊断",
        score=72,
        weaknesses='["复合函数求导"]',
        recommendations='["增加分层练习"]',
    )
    classroom = SimpleNamespace(
        course_id=7,
        title="导数课堂",
        status="ended",
        participant_count=28,
    )
    record = SimpleNamespace(
        course_id=7,
        record_type="transcript",
        transcript="多数学生在链式法则处需要更多示例。",
        knowledge_points='["链式法则"]',
    )
    resource = SimpleNamespace(
        course_id=7,
        title="导数补充讲义",
        resource_type="pdf",
        description="用于课后分层练习",
        tags='["导数", "练习"]',
        metadata_json='{"parsed_text_preview": "重点训练复合函数求导。"}',
        url=None,
    )

    material = service._render_context(
        {
            "courses": [course],
            "plans": [plan],
            "resources": [resource],
            "enrollment_stats": {7: {"student_count": 30, "average_progress": 66.5}},
            "diagnosis_stats": {7: {"count": 1, "average_score": 72}},
            "diagnoses": [diagnosis],
            "classrooms": [classroom],
            "records": [record],
        }
    )

    assert "微积分教案" in material
    assert "导数补充讲义" in material
    assert "重点训练复合函数求导" in material
    assert "复合函数求导" in material
    assert "链式法则" in material
    assert "学生30人" in material


@pytest.mark.asyncio
async def test_deepseek_call_is_direct_and_disables_thinking() -> None:
    service = TeacherAIService(AsyncMock())
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "model": "deepseek-v4-flash",
        "choices": [{"message": {"content": "建议先开展形成性诊断。"}}],
    }
    client = AsyncMock()
    client.post.return_value = response
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = client

    with (
        patch("app.services.teacher_ai_service.settings") as mock_settings,
        patch("app.services.teacher_ai_service.httpx.AsyncClient", return_value=context_manager),
    ):
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
        mock_settings.DEEPSEEK_MODEL = "deepseek-v4-flash"
        answer, model = await service._call_deepseek([{"role": "user", "content": "如何调整教案？"}])

    assert answer == "建议先开展形成性诊断。"
    assert model == "deepseek-v4-flash"
    payload = client.post.await_args.kwargs["json"]
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["model"] == "deepseek-v4-flash"


@pytest.mark.asyncio
async def test_deepseek_error_does_not_expose_key() -> None:
    service = TeacherAIService(AsyncMock())
    client = AsyncMock()
    client.post.side_effect = httpx.ConnectError("network unavailable")
    context_manager = AsyncMock()
    context_manager.__aenter__.return_value = client

    with (
        patch("app.services.teacher_ai_service.settings") as mock_settings,
        patch("app.services.teacher_ai_service.httpx.AsyncClient", return_value=context_manager),
    ):
        mock_settings.DEEPSEEK_API_KEY = "sensitive-secret"
        mock_settings.DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
        mock_settings.DEEPSEEK_MODEL = "deepseek-v4-flash"
        with pytest.raises(RuntimeError) as exc_info:
            await service._call_deepseek([{"role": "user", "content": "测试"}])

    assert "sensitive-secret" not in str(exc_info.value)
