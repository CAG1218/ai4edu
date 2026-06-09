"""
AI4Edu Agent相关Schema
SessionCreate / SessionResponse / MessageCreate / MessageResponse / AgentTypeResponse
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """创建AI会话请求"""

    agent_type: str = Field(..., description="智能体类型", min_length=1, max_length=30)
    title: Optional[str] = Field(None, description="会话标题", max_length=200)
    scene_type: Optional[str] = Field(None, description="场景类型", max_length=30)
    course_id: Optional[int] = Field(None, description="关联课程ID")
    model_name: Optional[str] = Field(None, description="模型名称", max_length=50)
    context: Optional[Dict[str, Any]] = Field(None, description="会话上下文(JSON)")


class SessionResponse(BaseModel):
    """AI会话响应"""

    id: int = Field(..., description="会话ID")
    tenant_id: int = Field(..., description="租户ID")
    user_id: int = Field(..., description="用户ID")
    agent_type: str = Field(..., description="智能体类型")
    title: Optional[str] = Field(None, description="会话标题")
    scene_type: Optional[str] = Field(None, description="场景类型")
    course_id: Optional[int] = Field(None, description="关联课程ID")
    model_name: str = Field(..., description="模型名称")
    message_count: int = Field(0, description="消息数量")
    total_tokens: int = Field(0, description="总Token消耗")
    is_archived: bool = Field(False, description="是否归档")
    last_message_at: Optional[datetime] = Field(None, description="最后消息时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class MessageCreate(BaseModel):
    """发送消息请求"""

    content: str = Field(..., description="消息内容", min_length=1)
    content_type: str = Field("text", description="内容类型: text/markdown/code/image")
    stream: bool = Field(False, description="是否流式输出")


class MessageResponse(BaseModel):
    """AI消息响应"""

    id: int = Field(..., description="消息ID")
    session_id: int = Field(..., description="会话ID")
    role: str = Field(..., description="角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    content_type: str = Field("text", description="内容类型")
    tokens: int = Field(0, description="Token数量")
    model_name: Optional[str] = Field(None, description="使用的模型")
    created_at: datetime = Field(..., description="创建时间")


class AgentTypeResponse(BaseModel):
    """智能体类型响应"""

    agent_type: str = Field(..., description="智能体类型标识")
    name: str = Field(..., description="智能体名称")
    description: str = Field(..., description="智能体描述")
    icon: Optional[str] = Field(None, description="图标")
    supported_features: List[str] = Field(default_factory=list, description="支持的功能")


class IntentResult(BaseModel):
    """意图识别结果"""

    intent: str = Field(..., description="意图类型")
    agent_type: str = Field(..., description="对应的Agent类型")
    confidence: float = Field(1.0, description="置信度")
