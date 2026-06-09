"""
AI4Edu 课堂Schema
ClassroomCreate / ClassroomResponse / PollCreate / PollVote / PollResult
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ClassroomCreate(BaseModel):
    """创建课堂请求"""

    course_id: int = Field(..., description="课程ID")
    title: str = Field(..., description="课堂主题", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="课堂描述")
    max_participants: int = Field(100, description="最大参与人数", ge=1, le=500)
    settings: Optional[Dict[str, Any]] = Field(None, description="课堂配置")


class ClassroomResponse(BaseModel):
    """课堂响应"""

    id: int = Field(..., description="课堂ID")
    tenant_id: int = Field(..., description="租户ID")
    course_id: int = Field(..., description="课程ID")
    teacher_id: int = Field(..., description="教师ID")
    title: str = Field(..., description="课堂主题")
    description: Optional[str] = Field(None, description="课堂描述")
    status: str = Field(..., description="状态: scheduled/active/ended")
    access_code: Optional[str] = Field(None, description="加入码")
    max_participants: int = Field(..., description="最大参与人数")
    participant_count: int = Field(0, description="当前参与人数")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    ended_at: Optional[datetime] = Field(None, description="结束时间")
    created_at: datetime = Field(..., description="创建时间")


class ClassroomParticipantResponse(BaseModel):
    """课堂参与者响应"""

    id: int = Field(..., description="参与者ID")
    classroom_id: int = Field(..., description="课堂ID")
    user_id: int = Field(..., description="用户ID")
    role: str = Field(..., description="角色: teacher/assistant/student")
    hand_raised: bool = Field(False, description="是否举手")
    joined_at: datetime = Field(..., description="加入时间")


class JoinClassroomRequest(BaseModel):
    """加入课堂请求"""

    access_code: Optional[str] = Field(None, description="加入码（如需要）")


class PollCreate(BaseModel):
    """发起投票请求"""

    question: str = Field(..., description="投票问题", min_length=1, max_length=500)
    options: List[str] = Field(..., description="选项列表", min_length=2)
    poll_type: str = Field("single", description="类型: single/multiple")
    is_anonymous: bool = Field(False, description="是否匿名")


class PollVote(BaseModel):
    """投票请求"""

    selected_options: List[int] = Field(..., description="选中的选项索引列表", min_length=1)


class PollResult(BaseModel):
    """投票结果"""

    id: int = Field(..., description="投票ID")
    question: str = Field(..., description="投票问题")
    options: List[str] = Field(..., description="选项列表")
    poll_type: str = Field(..., description="类型")
    is_anonymous: bool = Field(..., description="是否匿名")
    status: str = Field(..., description="状态: active/closed")
    total_votes: int = Field(0, description="总投票数")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="各选项统计")
    created_at: datetime = Field(..., description="创建时间")
    closed_at: Optional[datetime] = Field(None, description="关闭时间")


class RaiseHandRequest(BaseModel):
    """举手/放下请求"""

    raised: bool = Field(True, description="True=举手，False=放下")


class DanmakuMessage(BaseModel):
    """弹幕消息"""

    content: str = Field(..., description="弹幕内容", min_length=1, max_length=200)
    color: Optional[str] = Field(None, description="颜色", max_length=7)
