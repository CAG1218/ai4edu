"""Focused tests for teacher evaluation authorization and visibility."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.v1.growth import list_evaluations
from app.core.exceptions import ValidationException
from app.schemas.growth import EvaluationCreate
from app.services.growth_service import GrowthService
from app.services.teacher_service import TeacherService


def query_result(*, first=None, scalar=None, rows=None):
    result = MagicMock()
    result.scalars.return_value.first.return_value = first
    result.scalar.return_value = scalar
    result.scalar_one_or_none.return_value = scalar
    result.all.return_value = rows or []
    return result


@pytest.mark.asyncio
async def test_teacher_cannot_evaluate_student_outside_selected_course() -> None:
    db = AsyncMock()
    db.execute.side_effect = [
        query_result(first=SimpleNamespace(id=8)),
        query_result(first=SimpleNamespace(id=3)),
        query_result(scalar=None),
    ]
    service = GrowthService(db)

    with pytest.raises(ValidationException, match="未选修"):
        await service.create_evaluation(
            teacher_id=2,
            tenant_id=1,
            data=EvaluationCreate(
                student_id=8,
                course_id=3,
                evaluation_type="overall",
                rating=4,
                content="课堂参与积极。",
                is_visible=True,
            ),
        )


@pytest.mark.asyncio
async def test_student_cannot_read_another_students_evaluations() -> None:
    user = SimpleNamespace(id=8, role="student", tenant_id=1)

    with pytest.raises(HTTPException) as exc_info:
        await list_evaluations(
            student_id=99,
            course_id=None,
            page=1,
            page_size=20,
            current_user=user,
            db=AsyncMock(),
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_course_student_query_is_scoped_to_current_teacher() -> None:
    db = AsyncMock()
    db.execute.return_value = query_result(rows=[])
    service = TeacherService(db)

    await service.list_students(tenant_id=1, teacher_id=2, course_id=3)

    statement = db.execute.await_args.args[0]
    sql = str(statement.compile(compile_kwargs={"literal_binds": True}))
    assert "JOIN course_enrollments" in sql
    assert "JOIN courses" in sql
    assert "courses.teacher_id = 2" in sql
    assert "courses.id = 3" in sql
    assert "course_enrollments.role = 'student'" in sql
    assert "users.role =" not in sql
