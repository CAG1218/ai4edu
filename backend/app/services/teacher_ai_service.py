"""Independent DeepSeek Q&A chain for the teacher workbench.

This service deliberately does not use AgentSession, AgentMessage, BaseAgent,
or any endpoint from the AI agent center. It builds a teacher-owned context
from relational teaching data and calls DeepSeek directly.
"""

import json
import logging
from typing import Any, Optional

import httpx
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.classroom import Classroom
from app.models.course import Course, CourseEnrollment
from app.models.diagnosis import Diagnosis
from app.models.lesson_plan import LessonPlan
from app.models.resource import Resource
from app.models.teacher_method import ClassroomRecord
from app.schemas.teacher_ai import TeacherAIChatRequest

logger = logging.getLogger(__name__)


TEACHER_AI_SYSTEM_PROMPT = """你是 AI4Edu 教师工作台中的教师专属教学助手。
你的回答必须优先依据下方提供的教师教案和班级学情材料，不得假装掌握未提供的数据。
你可以帮助教师分析班级薄弱点、调整教案、设计课堂活动、制定分层教学与复习方案。
当材料不足时，应明确说明缺少哪些数据，并给出可执行的数据补充建议。
回答应面向教师，使用清晰的中文；涉及学生情况时优先做班级层面的归纳，避免推断敏感个人信息。
如果教师指定了课程，只能使用该课程范围内的材料作答。"""


def _json_value(raw: Optional[str], fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


def _clip(value: Any, limit: int = 1800) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else f"{text[:limit]}……"


class TeacherAIService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_context_summary(
        self,
        tenant_id: int,
        teacher_id: int,
        course_id: Optional[int] = None,
    ) -> dict[str, Any]:
        context = await self._build_context(tenant_id, teacher_id, course_id)
        return {
            "courses": [
                {
                    "id": course.id,
                    "name": course.name,
                    "subject": course.subject,
                    "grade": course.grade,
                    "semester": course.semester,
                }
                for course in context["courses"]
            ],
            "summary": context["summary"],
            "sources": context["sources"],
        }

    async def chat(
        self,
        tenant_id: int,
        teacher_id: int,
        request: TeacherAIChatRequest,
    ) -> dict[str, Any]:
        context = await self._build_context(
            tenant_id=tenant_id,
            teacher_id=teacher_id,
            course_id=request.course_id,
        )
        material = self._render_context(context)
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": f"{TEACHER_AI_SYSTEM_PROMPT}\n\n【当前教师材料】\n{material}",
            }
        ]
        messages.extend(
            {"role": item.role, "content": item.content}
            for item in request.history[-12:]
        )
        messages.append({"role": "user", "content": request.message})

        answer, model = await self._call_deepseek(messages)
        return {
            "answer": answer,
            "model": model,
            "course_id": request.course_id,
            "context_summary": context["summary"],
            "sources": context["sources"],
        }

    async def _build_context(
        self,
        tenant_id: int,
        teacher_id: int,
        course_id: Optional[int],
    ) -> dict[str, Any]:
        course_conditions = [
            Course.tenant_id == tenant_id,
            Course.teacher_id == teacher_id,
            Course.is_active.is_(True),
        ]
        if course_id is not None:
            course_conditions.append(Course.id == course_id)

        courses = (
            await self.db.execute(
                select(Course).where(and_(*course_conditions)).order_by(Course.name)
            )
        ).scalars().all()
        if course_id is not None and not courses:
            raise ValueError("课程不存在或不属于当前教师")

        course_ids = [course.id for course in courses]
        if not course_ids:
            return {
                "courses": [],
                "plans": [],
                "resources": [],
                "enrollment_stats": {},
                "diagnosis_stats": {},
                "diagnoses": [],
                "classrooms": [],
                "records": [],
                "sources": [],
                "summary": self._empty_summary(),
            }

        plans = (
            await self.db.execute(
                select(LessonPlan)
                .where(
                    LessonPlan.tenant_id == tenant_id,
                    LessonPlan.teacher_id == teacher_id,
                    LessonPlan.course_id.in_(course_ids),
                    LessonPlan.is_active.is_(True),
                )
                .order_by(desc(LessonPlan.updated_at))
                .limit(20)
            )
        ).scalars().all()

        resource_conditions = [
            Resource.tenant_id == tenant_id,
            Resource.uploader_id == teacher_id,
            Resource.is_active.is_(True),
            Resource.deleted_at.is_(None),
        ]
        if course_id is not None:
            resource_conditions.append(Resource.course_id == course_id)
        else:
            resource_conditions.append(
                (Resource.course_id.is_(None)) | (Resource.course_id.in_(course_ids))
            )
        resources = (
            await self.db.execute(
                select(Resource)
                .where(and_(*resource_conditions))
                .order_by(desc(Resource.updated_at))
                .limit(30)
            )
        ).scalars().all()

        enrollment_rows = (
            await self.db.execute(
                select(
                    CourseEnrollment.course_id,
                    func.count(func.distinct(CourseEnrollment.user_id)),
                    func.avg(CourseEnrollment.progress),
                )
                .where(
                    CourseEnrollment.course_id.in_(course_ids),
                    CourseEnrollment.dropped_at.is_(None),
                )
                .group_by(CourseEnrollment.course_id)
            )
        ).all()
        enrollment_stats = {
            row[0]: {"student_count": int(row[1] or 0), "average_progress": round(float(row[2] or 0), 1)}
            for row in enrollment_rows
        }
        unique_student_count = int(
            (
                await self.db.execute(
                    select(func.count(func.distinct(CourseEnrollment.user_id))).where(
                        CourseEnrollment.course_id.in_(course_ids),
                        CourseEnrollment.dropped_at.is_(None),
                    )
                )
            ).scalar_one()
            or 0
        )

        diagnosis_rows = (
            await self.db.execute(
                select(Diagnosis.course_id, func.count(Diagnosis.id), func.avg(Diagnosis.score))
                .where(
                    Diagnosis.tenant_id == tenant_id,
                    Diagnosis.course_id.in_(course_ids),
                    Diagnosis.status == "completed",
                )
                .group_by(Diagnosis.course_id)
            )
        ).all()
        diagnosis_stats = {
            row[0]: {"count": int(row[1] or 0), "average_score": round(float(row[2] or 0), 1)}
            for row in diagnosis_rows
        }
        diagnoses = (
            await self.db.execute(
                select(Diagnosis)
                .where(
                    Diagnosis.tenant_id == tenant_id,
                    Diagnosis.course_id.in_(course_ids),
                    Diagnosis.status == "completed",
                )
                .order_by(desc(Diagnosis.completed_at), desc(Diagnosis.id))
                .limit(40)
            )
        ).scalars().all()

        classrooms = (
            await self.db.execute(
                select(Classroom)
                .where(
                    Classroom.tenant_id == tenant_id,
                    Classroom.teacher_id == teacher_id,
                    Classroom.course_id.in_(course_ids),
                )
                .order_by(desc(Classroom.updated_at))
                .limit(20)
            )
        ).scalars().all()
        records = (
            await self.db.execute(
                select(ClassroomRecord)
                .where(
                    ClassroomRecord.tenant_id == tenant_id,
                    ClassroomRecord.course_id.in_(course_ids),
                    ClassroomRecord.status == "ready",
                )
                .order_by(desc(ClassroomRecord.updated_at))
                .limit(20)
            )
        ).scalars().all()

        summary = {
            "course_count": len(courses),
            "lesson_plan_count": len(plans),
            "resource_count": len(resources),
            "student_count": unique_student_count,
            "diagnosis_count": sum(item["count"] for item in diagnosis_stats.values()),
            "classroom_count": len(classrooms),
            "classroom_record_count": len(records),
        }
        sources = []
        if plans:
            sources.append("教案")
        if resources:
            sources.append("教师上传资源")
        if enrollment_stats:
            sources.append("选课与学习进度")
        if diagnoses:
            sources.append("班级学习诊断")
        if classrooms:
            sources.append("课堂情况")
        if records:
            sources.append("课堂记录")

        return {
            "courses": courses,
            "plans": plans,
            "resources": resources,
            "enrollment_stats": enrollment_stats,
            "diagnosis_stats": diagnosis_stats,
            "diagnoses": diagnoses,
            "classrooms": classrooms,
            "records": records,
            "sources": sources,
            "summary": summary,
        }

    @staticmethod
    def _empty_summary() -> dict[str, int]:
        return {
            "course_count": 0,
            "lesson_plan_count": 0,
            "resource_count": 0,
            "student_count": 0,
            "diagnosis_count": 0,
            "classroom_count": 0,
            "classroom_record_count": 0,
        }

    def _render_context(self, context: dict[str, Any]) -> str:
        if not context["courses"]:
            return "当前教师尚无可用课程、教案或班级学情数据。"

        course_names = {course.id: course.name for course in context["courses"]}
        lines = ["一、课程与班级概况"]
        for course in context["courses"]:
            enrollment = context["enrollment_stats"].get(course.id, {})
            diagnosis = context["diagnosis_stats"].get(course.id, {})
            lines.append(
                f"- {course.name}（{course.grade}，{course.semester}）："
                f"学生{enrollment.get('student_count', 0)}人，平均学习进度"
                f"{enrollment.get('average_progress', 0)}%，已完成诊断"
                f"{diagnosis.get('count', 0)}次，平均分{diagnosis.get('average_score', 0)}。"
            )

        lines.append("\n二、教师教案")
        if not context["plans"]:
            lines.append("- 暂无教案。")
        for plan in context["plans"]:
            lines.append(
                f"- 课程：{course_names.get(plan.course_id, plan.course_id)}；教案：{plan.title}；"
                f"状态：{plan.status}；目标：{_clip(_json_value(plan.objectives, []), 800)}；"
                f"材料：{_clip(_json_value(plan.materials, []), 600)}；"
                f"内容：{_clip(plan.content, 2200)}"
            )

        lines.append("\n三、教师上传资源")
        if not context["resources"]:
            lines.append("- 暂无教师上传且符合当前课程范围的资源。")
        for resource in context["resources"]:
            metadata = _json_value(resource.metadata_json, {})
            parsed_preview = metadata.get("parsed_text_preview", "") if isinstance(metadata, dict) else ""
            tags = _json_value(resource.tags, [])
            course_name = course_names.get(resource.course_id, "未关联课程")
            lines.append(
                f"- {resource.title}（{resource.resource_type}，课程：{course_name}）："
                f"描述：{_clip(resource.description, 500)}；标签：{_clip(tags, 300)}；"
                f"解析内容：{_clip(parsed_preview, 1000)}；链接：{_clip(resource.url, 500)}"
            )

        lines.append("\n四、班级诊断与薄弱点")
        if not context["diagnoses"]:
            lines.append("- 暂无已完成的诊断数据。")
        for diagnosis in context["diagnoses"]:
            lines.append(
                f"- {course_names.get(diagnosis.course_id, '未关联课程')}：{diagnosis.title}，"
                f"得分{diagnosis.score if diagnosis.score is not None else '未评分'}，"
                f"薄弱点：{_clip(_json_value(diagnosis.weaknesses, []), 600)}，"
                f"建议：{_clip(_json_value(diagnosis.recommendations, []), 600)}"
            )

        lines.append("\n五、课堂情况与课堂记录")
        if not context["classrooms"]:
            lines.append("- 暂无课堂记录。")
        for classroom in context["classrooms"]:
            lines.append(
                f"- {course_names.get(classroom.course_id, classroom.course_id)}：{classroom.title}，"
                f"状态{classroom.status}，参与人数{classroom.participant_count}。"
            )
        for record in context["records"]:
            lines.append(
                f"- 课堂材料（{course_names.get(record.course_id, record.course_id)}，"
                f"{record.record_type}）：{_clip(record.transcript, 1200)}；"
                f"知识点：{_clip(_json_value(record.knowledge_points, []), 500)}"
            )
        return "\n".join(lines)

    async def _call_deepseek(self, messages: list[dict[str, str]]) -> tuple[str, str]:
        if not settings.DEEPSEEK_API_KEY:
            raise RuntimeError("DeepSeek API Key 未配置")
        payload = {
            "model": settings.DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2000,
            "thinking": {"type": "disabled"},
        }
        headers = {
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{settings.DEEPSEEK_API_BASE.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.warning("teacher_ai_deepseek_request_failed: %s", type(exc).__name__)
            raise RuntimeError("DeepSeek 服务暂时不可用") from exc

        answer = str(data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        if not answer:
            raise RuntimeError("DeepSeek 未返回有效回答")
        return answer, str(data.get("model") or settings.DEEPSEEK_MODEL)
