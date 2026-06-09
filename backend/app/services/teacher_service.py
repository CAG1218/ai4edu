"""
AI4Edu 教师工作台服务
班级概览、学生分析、备课管理
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.lesson_plan_agent import LessonPlanAgent
from app.core.exceptions import NotFoundException, PermissionDeniedException
from app.models.lesson_plan import LessonPlan
from app.models.user import User
from app.models.diagnosis import Diagnosis
from app.schemas.common import PaginatedResponse, PaginationParams

logger = logging.getLogger(__name__)


class TeacherService:
    """教师工作台服务"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_dashboard(
        self,
        tenant_id: int,
        teacher_id: int,
    ) -> Dict[str, Any]:
        """
        获取教师仪表盘数据

        Args:
            tenant_id: 租户ID
            teacher_id: 教师ID

        Returns:
            仪表盘数据
        """
        # 教案统计
        plan_count_stmt = select(func.count(LessonPlan.id)).where(
            and_(
                LessonPlan.teacher_id == teacher_id,
                LessonPlan.tenant_id == tenant_id,
                LessonPlan.is_active == True,
            )
        )
        plan_count_result = await self.db.execute(plan_count_stmt)
        plan_count = plan_count_result.scalar() or 0

        # 最近教案
        recent_plans_stmt = (
            select(LessonPlan)
            .where(
                and_(
                    LessonPlan.teacher_id == teacher_id,
                    LessonPlan.tenant_id == tenant_id,
                    LessonPlan.is_active == True,
                )
            )
            .order_by(desc(LessonPlan.updated_at))
            .limit(5)
        )
        recent_plans_result = await self.db.execute(recent_plans_stmt)
        recent_plans = recent_plans_result.scalars().all()

        # 学生总数（简化统计）
        student_count = 0  # 后续可从课程-学生关系统计

        return {
            "teacher_id": teacher_id,
            "lesson_plan_count": plan_count,
            "student_count": student_count,
            "recent_lesson_plans": [
                {
                    "id": p.id,
                    "title": p.title,
                    "status": p.status,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                }
                for p in recent_plans
            ],
        }

    async def list_lesson_plans(
        self,
        tenant_id: int,
        teacher_id: int,
        pagination: PaginationParams,
        course_id: Optional[int] = None,
    ) -> PaginatedResponse:
        """
        获取教案列表

        Args:
            tenant_id: 租户ID
            teacher_id: 教师ID
            pagination: 分页参数
            course_id: 课程ID筛选

        Returns:
            分页教案列表
        """
        conditions = [
            LessonPlan.teacher_id == teacher_id,
            LessonPlan.tenant_id == tenant_id,
            LessonPlan.is_active == True,
        ]

        if course_id:
            conditions.append(LessonPlan.course_id == course_id)

        # 总数
        count_stmt = select(func.count(LessonPlan.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 数据
        stmt = (
            select(LessonPlan)
            .where(and_(*conditions))
            .order_by(desc(LessonPlan.updated_at))
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
        result = await self.db.execute(stmt)
        plans = result.scalars().all()

        items = [
            {
                "id": p.id,
                "title": p.title,
                "course_id": p.course_id,
                "duration_minutes": p.duration_minutes,
                "ai_generated": p.ai_generated,
                "status": p.status,
                "version": p.version,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in plans
        ]

        return PaginatedResponse(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    async def create_lesson_plan(
        self,
        tenant_id: int,
        teacher_id: int,
        course_id: int,
        title: str,
        objectives: Optional[List[str]] = None,
        content: Optional[str] = None,
        materials: Optional[List[str]] = None,
        duration_minutes: int = 45,
    ) -> Dict[str, Any]:
        """
        创建教案

        Args:
            tenant_id: 租户ID
            teacher_id: 教师ID
            course_id: 课程ID
            title: 教案标题
            objectives: 教学目标
            content: 教案内容
            materials: 教学材料
            duration_minutes: 时长

        Returns:
            创建的教案信息
        """
        plan = LessonPlan(
            tenant_id=tenant_id,
            course_id=course_id,
            teacher_id=teacher_id,
            title=title,
            objectives=json.dumps(objectives or [], ensure_ascii=False),
            content=content,
            materials=json.dumps(materials or [], ensure_ascii=False),
            duration_minutes=duration_minutes,
            ai_generated=False,
            status="draft",
            version=1,
        )
        self.db.add(plan)
        await self.db.flush()

        return self._plan_to_dict(plan)

    async def get_lesson_plan(
        self,
        plan_id: int,
        tenant_id: int,
    ) -> Optional[Dict[str, Any]]:
        """获取教案详情"""
        stmt = select(LessonPlan).where(
            and_(
                LessonPlan.id == plan_id,
                LessonPlan.tenant_id == tenant_id,
                LessonPlan.is_active == True,
            )
        )
        result = await self.db.execute(stmt)
        plan = result.scalars().first()

        if not plan:
            return None

        return self._plan_to_dict(plan)

    async def update_lesson_plan(
        self,
        plan_id: int,
        tenant_id: int,
        teacher_id: int,
        title: Optional[str] = None,
        objectives: Optional[List[str]] = None,
        content: Optional[str] = None,
        materials: Optional[List[str]] = None,
        duration_minutes: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """更新教案"""
        stmt = select(LessonPlan).where(
            and_(
                LessonPlan.id == plan_id,
                LessonPlan.tenant_id == tenant_id,
                LessonPlan.is_active == True,
            )
        )
        result = await self.db.execute(stmt)
        plan = result.scalars().first()

        if not plan:
            return None

        if plan.teacher_id != teacher_id:
            raise PermissionDeniedException(message="只能修改自己的教案")

        if title is not None:
            plan.title = title
        if objectives is not None:
            plan.objectives = json.dumps(objectives, ensure_ascii=False)
        if content is not None:
            plan.content = content
        if materials is not None:
            plan.materials = json.dumps(materials, ensure_ascii=False)
        if duration_minutes is not None:
            plan.duration_minutes = duration_minutes
        if status is not None:
            plan.status = status

        plan.version += 1
        await self.db.flush()

        return self._plan_to_dict(plan)

    async def delete_lesson_plan(
        self,
        plan_id: int,
        tenant_id: int,
        teacher_id: int,
    ) -> bool:
        """删除教案（软删除）"""
        stmt = select(LessonPlan).where(
            and_(
                LessonPlan.id == plan_id,
                LessonPlan.tenant_id == tenant_id,
                LessonPlan.is_active == True,
            )
        )
        result = await self.db.execute(stmt)
        plan = result.scalars().first()

        if not plan:
            return False

        if plan.teacher_id != teacher_id:
            raise PermissionDeniedException(message="只能删除自己的教案")

        plan.is_active = False
        await self.db.flush()
        return True

    async def ai_generate_lesson_plan(
        self,
        plan_id: int,
        tenant_id: int,
        teacher_id: int,
    ) -> Dict[str, Any]:
        """
        使用AI根据课程信息生成教案

        Args:
            plan_id: 教案ID
            tenant_id: 租户ID
            teacher_id: 教师ID

        Returns:
            AI生成的教案内容
        """
        plan_data = await self.get_lesson_plan(plan_id, tenant_id)
        if not plan_data:
            raise NotFoundException(message="教案不存在")

        # 调用LessonPlanAgent
        agent = LessonPlanAgent()
        result = await agent.generate_lesson_plan(
            title=plan_data["title"],
            subject="",  # 可从课程信息获取
            context={"tenant_id": tenant_id, "user_id": teacher_id},
        )

        # 更新教案内容
        generated_content = result.get("content", "")
        stmt = select(LessonPlan).where(LessonPlan.id == plan_id)
        db_result = await self.db.execute(stmt)
        plan = db_result.scalars().first()
        if plan:
            plan.content = generated_content
            plan.ai_generated = True
            plan.version += 1
            await self.db.flush()

        return {
            "id": plan_id,
            "content": generated_content,
            "ai_generated": True,
        }

    async def list_students(
        self,
        tenant_id: int,
        teacher_id: int,
        course_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取教师所教学生列表

        Args:
            tenant_id: 租户ID
            teacher_id: 教师ID
            course_id: 课程ID筛选

        Returns:
            学生列表
        """
        # 简化实现：查询该租户下的学生
        conditions = [
            User.tenant_id == tenant_id,
            User.role == "student",
            User.is_active == True,
        ]

        stmt = select(User).where(and_(*conditions)).limit(50)
        result = await self.db.execute(stmt)
        students = result.scalars().all()

        return [
            {
                "id": s.id,
                "nickname": s.nickname,
                "avatar_url": s.avatar_url,
                "grade": s.grade,
                "school": s.school,
            }
            for s in students
        ]

    async def get_learning_analytics(
        self,
        tenant_id: int,
        teacher_id: int,
        course_id: Optional[int] = None,
        time_range: str = "week",
    ) -> Dict[str, Any]:
        """
        获取学情分析数据

        Args:
            tenant_id: 租户ID
            teacher_id: 教师ID
            course_id: 课程ID
            time_range: 时间范围 day/week/month

        Returns:
            学情分析数据
        """
        # 诊断统计（简化版本）
        diagnosis_count_stmt = select(func.count(Diagnosis.id)).where(
            Diagnosis.tenant_id == tenant_id,
        )
        if course_id:
            diagnosis_count_stmt = diagnosis_count_stmt.where(
                Diagnosis.course_id == course_id,
            )
        result = await self.db.execute(diagnosis_count_stmt)
        total_diagnoses = result.scalar() or 0

        # 平均分
        avg_score_stmt = select(func.avg(Diagnosis.score)).where(
            and_(
                Diagnosis.tenant_id == tenant_id,
                Diagnosis.status == "completed",
                Diagnosis.score.isnot(None),
            ),
        )
        if course_id:
            avg_score_stmt = avg_score_stmt.where(Diagnosis.course_id == course_id)
        avg_result = await self.db.execute(avg_score_stmt)
        avg_score = avg_result.scalar() or 0.0

        return {
            "time_range": time_range,
            "total_diagnoses": total_diagnoses,
            "average_score": round(float(avg_score), 1),
            "student_engagement": {
                "active_students": 0,  # 后续从ClickHouse统计
                "total_students": 0,
            },
            "knowledge_distribution": [],  # 后续从诊断数据聚合
        }

    def _plan_to_dict(self, plan: LessonPlan) -> Dict[str, Any]:
        """将LessonPlan模型转换为字典"""
        objectives = []
        if plan.objectives:
            try:
                objectives = json.loads(plan.objectives)
            except (json.JSONDecodeError, TypeError):
                pass

        materials = []
        if plan.materials:
            try:
                materials = json.loads(plan.materials)
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "id": plan.id,
            "tenant_id": plan.tenant_id,
            "course_id": plan.course_id,
            "teacher_id": plan.teacher_id,
            "title": plan.title,
            "objectives": objectives,
            "content": plan.content,
            "materials": materials,
            "duration_minutes": plan.duration_minutes,
            "ai_generated": plan.ai_generated,
            "status": plan.status,
            "version": plan.version,
            "is_active": plan.is_active,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
        }
