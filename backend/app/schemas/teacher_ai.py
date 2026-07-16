"""Schemas for the teacher-workbench-only AI assistant."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class TeacherAIHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=8000)


class TeacherAIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    course_id: Optional[int] = Field(default=None, ge=1)
    history: list[TeacherAIHistoryMessage] = Field(default_factory=list, max_length=20)


class TeacherAIContextSummary(BaseModel):
    course_count: int = 0
    lesson_plan_count: int = 0
    resource_count: int = 0
    student_count: int = 0
    diagnosis_count: int = 0
    classroom_count: int = 0
    classroom_record_count: int = 0


class TeacherAIChatResponse(BaseModel):
    answer: str
    model: str
    course_id: Optional[int] = None
    context_summary: TeacherAIContextSummary
    sources: list[str] = Field(default_factory=list)
