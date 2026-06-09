"""
AI4Edu AI智能体 API
提供AI对话、会话管理、智能体配置等端点
"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.agent import AgentMessage, AgentSession
from app.models.user import User
from app.schemas.agent import (
    AgentTypeResponse,
    IntentResult,
    MessageCreate,
    MessageResponse,
    SessionCreate,
    SessionResponse,
)
from app.schemas.common import APIResponse, PaginationParams, PaginatedResponse
from app.agents.intent_router import IntentRouter, IntentType, intent_router

router = APIRouter()

# 可用智能体类型列表
AGENT_TYPES = [
    AgentTypeResponse(
        agent_type="rag",
        name="知识问答",
        description="基于知识图谱和检索的知识问答",
        icon="Search",
        supported_features=["知识检索", "流式回答", "图谱关联"],
    ),
    AgentTypeResponse(
        agent_type="subject",
        name="学科专家",
        description="数学/物理/化学等专业解题",
        icon="Calculator",
        supported_features=["专业解题", "多步骤推导", "学科知识"],
    ),
    AgentTypeResponse(
        agent_type="quiz",
        name="测验出题",
        description="生成选择题/填空题/问答题",
        icon="Edit",
        supported_features=["自动出题", "多难度", "多题型"],
    ),
    AgentTypeResponse(
        agent_type="file_rag",
        name="文件解析",
        description="解析PDF/Word/PPT文件",
        icon="FileText",
        supported_features=["文件解析", "内容问答", "知识点提取"],
    ),
    AgentTypeResponse(
        agent_type="lesson_plan",
        name="备课助手",
        description="生成教案和教学计划",
        icon="BookOpen",
        supported_features=["教案生成", "教学设计", "目标设定"],
    ),
    AgentTypeResponse(
        agent_type="buddy",
        name="学伴",
        description="陪伴式学习对话",
        icon="Heart",
        supported_features=["学习陪伴", "鼓励互动", "情绪支持"],
    ),
    AgentTypeResponse(
        agent_type="diagnosis",
        name="学习诊断",
        description="知识掌握度诊断分析",
        icon="Activity",
        supported_features=["IRT诊断", "弱点分析", "学习路径"],
    ),
    AgentTypeResponse(
        agent_type="classroom",
        name="课堂管理",
        description="课堂互动辅助",
        icon="Users",
        supported_features=["互动建议", "出题", "参与度分析"],
    ),
    AgentTypeResponse(
        agent_type="psychology",
        name="心理支持",
        description="学习心理建议和压力疏导",
        icon="Smile",
        supported_features=["压力疏导", "情绪识别", "危机干预"],
    ),
    AgentTypeResponse(
        agent_type="anti_misconception",
        name="概念纠偏",
        description="识别常见错误概念并纠正",
        icon="AlertTriangle",
        supported_features=["错误识别", "概念纠正", "正确理解"],
    ),
    AgentTypeResponse(
        agent_type="general",
        name="通用助手",
        description="处理其他类型的请求",
        icon="MessageCircle",
        supported_features=["通用问答", "导航推荐"],
    ),
]


@router.get("/sessions", summary="获取AI会话列表")
async def list_sessions(
    pagination: PaginationParams = Depends(),
    agent_type: Optional[str] = Query(None, description="智能体类型筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """获取当前用户的AI会话列表"""
    from sqlalchemy import and_, desc, func, select

    conditions = [
        AgentSession.user_id == current_user.id,
        AgentSession.is_archived == False,
    ]
    if agent_type:
        conditions.append(AgentSession.agent_type == agent_type)

    # 总数
    count_stmt = select(func.count(AgentSession.id)).where(and_(*conditions))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    # 数据
    stmt = (
        select(AgentSession)
        .where(and_(*conditions))
        .order_by(desc(AgentSession.updated_at))
        .offset(pagination.offset)
        .limit(pagination.page_size)
    )
    result = await db.execute(stmt)
    sessions = result.scalars().all()

    items = [
        {
            "id": s.id,
            "agent_type": s.agent_type,
            "title": s.title,
            "message_count": s.message_count,
            "last_message_at": s.last_message_at.isoformat() if s.last_message_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sessions
    ]

    return APIResponse(
        code=0,
        data=PaginatedResponse(
            items=items, total=total, page=pagination.page, page_size=pagination.page_size
        ),
        message="success",
    )


@router.post("/sessions", summary="创建AI会话")
async def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """创建新的AI对话会话"""
    session = AgentSession(
        tenant_id=current_user.tenant_id or 0,
        user_id=current_user.id,
        agent_type=session_data.agent_type,
        title=session_data.title or f"{session_data.agent_type}会话",
        scene_type=session_data.scene_type,
        course_id=session_data.course_id,
        model_name=session_data.model_name or "gpt-4o",
        context=json.dumps(session_data.context, ensure_ascii=False) if session_data.context else None,
    )
    db.add(session)
    await db.flush()

    return APIResponse(
        code=0,
        data={
            "id": session.id,
            "agent_type": session.agent_type,
            "title": session.title,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        },
        message="success",
    )


@router.get("/sessions/{session_id}", summary="获取会话详情")
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """获取AI会话详情（含消息历史）"""
    from sqlalchemy import select

    stmt = select(AgentSession).where(AgentSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 获取消息历史
    msg_stmt = (
        select(AgentMessage)
        .where(AgentMessage.session_id == session_id)
        .order_by(AgentMessage.created_at)
    )
    msg_result = await db.execute(msg_stmt)
    messages = msg_result.scalars().all()

    return APIResponse(
        code=0,
        data={
            "id": session.id,
            "agent_type": session.agent_type,
            "title": session.title,
            "message_count": session.message_count,
            "messages": [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "content_type": m.content_type,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
        },
        message="success",
    )


@router.post("/sessions/{session_id}/messages", summary="发送消息")
async def send_message(
    session_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """向AI会话发送消息并获取回复"""
    from sqlalchemy import select

    # 获取会话
    stmt = select(AgentSession).where(AgentSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 保存用户消息
    user_msg = AgentMessage(
        session_id=session_id,
        role="user",
        content=message_data.content,
        content_type=message_data.content_type,
    )
    db.add(user_msg)

    # 意图路由
    detected_intent = intent_router.route(
        message_data.content,
        context={"current_agent_type": session.agent_type},
    )
    agent_type_str = intent_router.get_agent_type(detected_intent)

    # 获取对应Agent
    agent = _get_agent_instance(agent_type_str)

    # 获取历史消息
    msg_stmt = (
        select(AgentMessage)
        .where(AgentMessage.session_id == session_id)
        .order_by(AgentMessage.created_at)
    )
    msg_result = await db.execute(msg_stmt)
    history = msg_result.scalars().all()

    messages = [
        {"role": m.role, "content": m.content}
        for m in history
    ]

    # 调用Agent
    agent_result = await agent.execute(
        messages=messages,
        context={
            "user_id": current_user.id,
            "tenant_id": current_user.tenant_id,
            "session_id": session_id,
        },
    )

    # 保存AI回复
    ai_msg = AgentMessage(
        session_id=session_id,
        role="assistant",
        content=agent_result.get("content", ""),
        content_type="markdown",
        model_name=agent_result.get("model", ""),
    )
    db.add(ai_msg)

    # 更新会话
    session.message_count += 2
    session.last_message_at = __import__("datetime").datetime.utcnow()
    await db.flush()

    return APIResponse(
        code=0,
        data={
            "user_message": {
                "id": user_msg.id,
                "role": "user",
                "content": message_data.content,
            },
            "assistant_message": {
                "id": ai_msg.id,
                "role": "assistant",
                "content": agent_result.get("content", ""),
            },
            "detected_intent": detected_intent.value,
            "agent_type": agent_type_str,
        },
        message="success",
    )


@router.delete("/sessions/{session_id}", summary="删除会话")
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """删除AI会话"""
    from sqlalchemy import select

    stmt = select(AgentSession).where(AgentSession.id == session_id)
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="会话不存在")

    session.is_archived = True
    await db.flush()

    return APIResponse(code=0, data=None, message="会话已归档")


@router.get("/types", summary="获取智能体类型列表")
async def list_agent_types() -> APIResponse:
    """获取所有可用的AI智能体类型"""
    return APIResponse(
        code=0,
        data=[t.model_dump() for t in AGENT_TYPES],
        message="success",
    )


@router.post("/intent", summary="意图识别")
async def detect_intent(
    text: str = Query(..., description="待识别文本"),
) -> APIResponse:
    """识别用户输入的意图"""
    detected = intent_router.route(text)
    agent_type = intent_router.get_agent_type(detected)

    return APIResponse(
        code=0,
        data=IntentResult(
            intent=detected.value,
            agent_type=agent_type,
            confidence=1.0,
        ).model_dump(),
        message="success",
    )


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: int):
    """WebSocket 实时对话端点"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # 意图路由
            detected_intent = intent_router.route(data)
            agent_type_str = intent_router.get_agent_type(detected_intent)
            agent = _get_agent_instance(agent_type_str)

            # 流式输出
            async for chunk in agent.stream_execute(
                messages=[{"role": "user", "content": data}],
            ):
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk,
                    "agent_type": agent_type_str,
                })

            await websocket.send_json({"type": "done", "agent_type": agent_type_str})
    except Exception:
        await websocket.close()


def _get_agent_instance(agent_type: str):
    """根据agent_type获取Agent实例"""
    from app.agents.rag_agent import RAGAgent
    from app.agents.subject_agent import SubjectAgent
    from app.agents.quiz_agent import QuizAgent
    from app.agents.file_rag_agent import FileRAGAgent
    from app.agents.lesson_plan_agent import LessonPlanAgent
    from app.agents.buddy_agent import BuddyAgent
    from app.agents.diagnosis_agent import DiagnosisAgent
    from app.agents.classroom_agent import ClassroomAgent
    from app.agents.psychology_agent import PsychologyAgent
    from app.agents.anti_misconception_agent import AntiMisconceptionAgent
    from app.agents.general_agent import GeneralAgent

    agent_map = {
        "rag": RAGAgent,
        "subject": SubjectAgent,
        "quiz": QuizAgent,
        "file_rag": FileRAGAgent,
        "lesson_plan": LessonPlanAgent,
        "buddy": BuddyAgent,
        "diagnosis": DiagnosisAgent,
        "classroom": ClassroomAgent,
        "psychology": PsychologyAgent,
        "anti_misconception": AntiMisconceptionAgent,
        "general": GeneralAgent,
    }

    agent_class = agent_map.get(agent_type, GeneralAgent)
    return agent_class()
