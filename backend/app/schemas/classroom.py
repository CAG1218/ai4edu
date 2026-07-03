"""
AI4Edu 课堂记录相关 Pydantic Schema
v2 新增：板书/录播 OCR/ASR 提取
"""
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ClassroomRecordCreate(BaseModel):
    """创建课堂记录请求"""

    classroom_id: Optional[int] = Field(None, description="课堂ID")
    course_id: Optional[int] = Field(None, description="课程ID")
    record_type: str = Field(..., description="类型: board_image/video_record")


class ClassroomRecordResponse(BaseModel):
    """课堂记录响应"""

    id: int = Field(..., description="记录ID")
    classroom_id: Optional[int] = Field(None, description="课堂ID")
    course_id: Optional[int] = Field(None, description="课程ID")
    record_type: str = Field(..., description="记录类型")
    status: str = Field(..., description="状态")
    transcript: Optional[str] = Field(None, description="提取文本")
    segments: Optional[List[Any]] = Field(None, description="分段信息")
    knowledge_points: Optional[List[Any]] = Field(None, description="知识点")
    provider: Optional[str] = Field(None, description="使用的 provider")
    error_msg: Optional[str] = Field(None, description="错误信息")
    file_url: Optional[str] = Field(None, description="MinIO 文件路径")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True
