"""
AI4Edu 教师工作台 API
提供教案管理、作业批改、学情分析等端点
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_role
from app.models.user import User
from app.schemas.common import APIResponse, PaginationParams
from app.services.teacher_service import TeacherService

router = APIRouter()


class LessonPlanCreate(BaseModel):
    """创建教案请求"""

    course_id: int = Field(..., description="课程ID")
    title: str = Field(..., description="教案标题", min_length=1, max_length=300)
    objectives: Optional[list[str]] = Field(None, description="教学目标")
    content: Optional[str] = Field(None, description="教案内容")
    materials: Optional[list[str]] = Field(None, description="教学材料")
    duration_minutes: int = Field(45, description="时长(分钟)")


class LessonPlanUpdate(BaseModel):
    """更新教案请求"""

    title: Optional[str] = Field(None, description="教案标题")
    objectives: Optional[list[str]] = Field(None, description="教学目标")
    content: Optional[str] = Field(None, description="教案内容")
    materials: Optional[list[str]] = Field(None, description="教学材料")
    duration_minutes: Optional[int] = Field(None, description="时长(分钟)")
    status: Optional[str] = Field(None, description="状态: draft/published/archived")


@router.get("/dashboard", summary="教师仪表盘")
async def teacher_dashboard(
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """获取教师工作台仪表盘数据"""
    service = TeacherService(db)
    result = await service.get_dashboard(
        tenant_id=current_user.tenant_id or 0,
        teacher_id=current_user.id,
    )
    return APIResponse(code=0, data=result, message="success")


@router.get("/lesson-plans", summary="获取教案列表")
async def list_lesson_plans(
    pagination: PaginationParams = Depends(),
    course_id: Optional[int] = Query(None, description="课程ID筛选"),
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """获取教案列表"""
    service = TeacherService(db)
    result = await service.list_lesson_plans(
        tenant_id=current_user.tenant_id or 0,
        teacher_id=current_user.id,
        pagination=pagination,
        course_id=course_id,
    )
    return APIResponse(code=0, data=result.model_dump(), message="success")


@router.post("/lesson-plans", summary="创建教案")
async def create_lesson_plan(
    plan_data: LessonPlanCreate,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """创建新教案（支持AI辅助生成）"""
    service = TeacherService(db)
    result = await service.create_lesson_plan(
        tenant_id=current_user.tenant_id or 0,
        teacher_id=current_user.id,
        course_id=plan_data.course_id,
        title=plan_data.title,
        objectives=plan_data.objectives,
        content=plan_data.content,
        materials=plan_data.materials,
        duration_minutes=plan_data.duration_minutes,
    )
    return APIResponse(code=0, data=result, message="success")


@router.get("/lesson-plans/{plan_id}", summary="获取教案详情")
async def get_lesson_plan(
    plan_id: int,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """获取教案详情"""
    service = TeacherService(db)
    result = await service.get_lesson_plan(
        plan_id=plan_id,
        tenant_id=current_user.tenant_id or 0,
    )
    if not result:
        raise HTTPException(status_code=404, detail="教案不存在")
    return APIResponse(code=0, data=result, message="success")


@router.put("/lesson-plans/{plan_id}", summary="更新教案")
async def update_lesson_plan(
    plan_id: int,
    plan_data: LessonPlanUpdate,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """更新教案"""
    service = TeacherService(db)
    result = await service.update_lesson_plan(
        plan_id=plan_id,
        tenant_id=current_user.tenant_id or 0,
        teacher_id=current_user.id,
        title=plan_data.title,
        objectives=plan_data.objectives,
        content=plan_data.content,
        materials=plan_data.materials,
        duration_minutes=plan_data.duration_minutes,
        status=plan_data.status,
    )
    if not result:
        raise HTTPException(status_code=404, detail="教案不存在或无权修改")
    return APIResponse(code=0, data=result, message="success")


@router.delete("/lesson-plans/{plan_id}", summary="删除教案")
async def delete_lesson_plan(
    plan_id: int,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """删除教案"""
    service = TeacherService(db)
    success = await service.delete_lesson_plan(
        plan_id=plan_id,
        tenant_id=current_user.tenant_id or 0,
        teacher_id=current_user.id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="教案不存在")
    return APIResponse(code=0, data=None, message="教案已删除")


@router.post("/lesson-plans/{plan_id}/ai-generate", summary="AI生成教案")
async def ai_generate_lesson_plan(
    plan_id: int,
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """使用AI根据课程信息生成教案"""
    service = TeacherService(db)
    result = await service.ai_generate_lesson_plan(
        plan_id=plan_id,
        tenant_id=current_user.tenant_id or 0,
        teacher_id=current_user.id,
    )
    return APIResponse(code=0, data=result, message="success")


@router.get("/students", summary="获取学生列表")
async def list_students(
    course_id: Optional[int] = Query(None, description="课程ID筛选"),
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """获取教师所教学生列表"""
    service = TeacherService(db)
    result = await service.list_students(
        tenant_id=current_user.tenant_id or 0,
        teacher_id=current_user.id,
        course_id=course_id,
    )
    return APIResponse(code=0, data=result, message="success")


@router.get("/analytics", summary="学情分析")
async def learning_analytics(
    course_id: Optional[int] = Query(None, description="课程ID"),
    time_range: Optional[str] = Query("week", description="时间范围: day/week/month"),
    current_user: User = Depends(require_role(["teacher", "admin"])),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """获取学情分析数据"""
    service = TeacherService(db)
    result = await service.get_learning_analytics(
        tenant_id=current_user.tenant_id or 0,
        teacher_id=current_user.id,
        course_id=course_id,
        time_range=time_range or "week",
    )
    return APIResponse(code=0, data=result, message="success")
