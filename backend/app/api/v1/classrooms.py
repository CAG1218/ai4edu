"""
AI4Edu 课堂互动 API
提供课堂创建、实时互动、举手、投票等端点
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.classroom import (
    ClassroomCreate,
    ClassroomResponse,
    DanmakuMessage,
    JoinClassroomRequest,
    PollCreate,
    PollResult,
    PollVote,
    RaiseHandRequest,
)
from app.schemas.common import APIResponse
from app.services.classroom_service import ClassroomService

router = APIRouter()


@router.post("/", summary="创建课堂")
async def create_classroom(
    classroom_data: ClassroomCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """创建新的课堂互动"""
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="只有教师可以创建课堂")

    service = ClassroomService(db)
    result = await service.create_classroom(
        tenant_id=current_user.tenant_id or 0,
        teacher_id=current_user.id,
        course_id=classroom_data.course_id,
        title=classroom_data.title,
        description=classroom_data.description,
        max_participants=classroom_data.max_participants,
        settings=classroom_data.settings,
    )
    return APIResponse(code=0, data=result, message="success")


@router.get("/{classroom_id}", summary="获取课堂详情")
async def get_classroom(
    classroom_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """获取课堂详情"""
    service = ClassroomService(db)
    result = await service.get_classroom(
        classroom_id=classroom_id,
        tenant_id=current_user.tenant_id or 0,
    )
    if not result:
        raise HTTPException(status_code=404, detail="课堂不存在")
    return APIResponse(code=0, data=result, message="success")


@router.post("/{classroom_id}/join", summary="加入课堂")
async def join_classroom(
    classroom_id: int,
    join_data: JoinClassroomRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """学生加入课堂"""
    service = ClassroomService(db)
    result = await service.join_classroom(
        classroom_id=classroom_id,
        tenant_id=current_user.tenant_id or 0,
        user_id=current_user.id,
        access_code=join_data.access_code,
    )
    return APIResponse(code=0, data=result, message="success")


@router.post("/{classroom_id}/leave", summary="离开课堂")
async def leave_classroom(
    classroom_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """学生离开课堂"""
    service = ClassroomService(db)
    success = await service.leave_classroom(
        classroom_id=classroom_id,
        tenant_id=current_user.tenant_id or 0,
        user_id=current_user.id,
    )
    if not success:
        raise HTTPException(status_code=400, detail="离开课堂失败")
    return APIResponse(code=0, data=None, message="已离开课堂")


@router.post("/{classroom_id}/raise-hand", summary="举手")
async def raise_hand(
    classroom_id: int,
    hand_data: RaiseHandRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """学生举手"""
    service = ClassroomService(db)
    success = await service.raise_hand(
        classroom_id=classroom_id,
        user_id=current_user.id,
        raised=hand_data.raised,
    )
    if not success:
        raise HTTPException(status_code=400, detail="操作失败")
    return APIResponse(code=0, data=None, message="举手成功" if hand_data.raised else "已放下手")


@router.post("/{classroom_id}/poll", summary="发起投票")
async def create_poll(
    classroom_id: int,
    poll_data: PollCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """教师发起课堂投票"""
    service = ClassroomService(db)
    result = await service.create_poll(
        classroom_id=classroom_id,
        teacher_id=current_user.id,
        question=poll_data.question,
        options=poll_data.options,
        poll_type=poll_data.poll_type,
        is_anonymous=poll_data.is_anonymous,
    )
    return APIResponse(code=0, data=result, message="success")


@router.post("/{classroom_id}/poll/{poll_id}/vote", summary="投票")
async def vote_poll(
    classroom_id: int,
    poll_id: int,
    vote_data: PollVote,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """学生对投票进行投票"""
    service = ClassroomService(db)
    success = await service.vote_poll(
        poll_id=poll_id,
        user_id=current_user.id,
        selected_options=vote_data.selected_options,
    )
    if not success:
        raise HTTPException(status_code=400, detail="投票失败")
    return APIResponse(code=0, data=None, message="投票成功")


@router.get("/{classroom_id}/poll/{poll_id}/result", summary="投票结果")
async def poll_result(
    classroom_id: int,
    poll_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """获取投票结果"""
    service = ClassroomService(db)
    result = await service.get_poll_result(
        poll_id=poll_id,
        tenant_id=current_user.tenant_id or 0,
    )
    return APIResponse(code=0, data=result, message="success")


@router.post("/{classroom_id}/end", summary="结束课堂")
async def end_classroom(
    classroom_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """结束课堂互动"""
    service = ClassroomService(db)
    success = await service.end_classroom(
        classroom_id=classroom_id,
        teacher_id=current_user.id,
    )
    if not success:
        raise HTTPException(status_code=400, detail="结束课堂失败")
    return APIResponse(code=0, data=None, message="课堂已结束")
