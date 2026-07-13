"""学生与教师全文检索 API。"""

from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models.note import Note
from app.models.user import User
from app.schemas.common import APIResponse
from app.services.search_service import SEARCH_TYPES, search_service

router = APIRouter()
search_user = require_role(["student", "teacher"])


@router.get("/", summary="多源混合全文检索")
async def search(
    q: str = Query(..., min_length=1, max_length=200, description="搜索词"),
    search_type: str = Query("all", description="兼容筛选: all/note/resource/graph_node/course"),
    mode: Literal["hybrid", "keyword", "semantic"] = Query("hybrid", description="检索模式"),
    sources: Optional[List[str]] = Query(None, description="多选数据源"),
    date_range: Optional[Literal["1d", "7d", "30d", "365d"]] = Query(None, description="更新时间范围"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    limit: Optional[int] = Query(None, ge=1, le=50, description="兼容旧客户端的每页数量"),
    current_user: User = Depends(search_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    selected = sources or ([] if search_type == "all" else [search_type])
    invalid = set(selected) - SEARCH_TYPES
    if invalid:
        raise HTTPException(status_code=422, detail=f"不支持的数据源: {', '.join(sorted(invalid))}")
    result = await search_service.hybrid_search(
        q.strip(), db=db, user=current_user, search_type=search_type, search_mode=mode,
        sources=selected, date_range=date_range, page=page, page_size=limit or page_size,
    )
    return APIResponse(data=result)


@router.get("/suggest", summary="可见内容搜索建议")
async def search_suggest(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=20),
    current_user: User = Depends(search_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    return APIResponse(data=await search_service.suggest(q.strip(), db, current_user, limit))


@router.get("/hot", summary="热门搜索")
async def hot_searches(
    limit: int = Query(10, ge=1, le=20),
    _: User = Depends(search_user),
) -> APIResponse:
    return APIResponse(data=await search_service.get_hot_searches(limit))


@router.post("/notes/{note_id}/reindex", summary="重新生成笔记摘要并建立索引")
async def reindex_note(
    note_id: int,
    current_user: User = Depends(search_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    result = await db.execute(select(Note).where(and_(
        Note.id == note_id, Note.tenant_id == (current_user.tenant_id or 0),
        Note.owner_id == current_user.id, Note.is_deleted.is_(False),
    )))
    note = result.scalars().first()
    if note is None:
        raise HTTPException(status_code=404, detail="笔记不存在或无权索引")
    data = {
        "id": note.id, "title": note.title, "content": note.content,
        "content_plain": note.content_plain, "tags": search_service._json_list(note.tags),
        "tenant_id": note.tenant_id, "owner_id": note.owner_id, "course_id": note.course_id,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
    }
    await search_service.index_note(data)
    smart = search_service.summarize_note(note.title, note.content_plain or note.content)
    return APIResponse(data=smart, message="笔记摘要索引已更新")


@router.post("/index", summary="教师手动索引教学文档")
async def index_document(
    doc_id: str = Query(...),
    doc_type: Literal["resource", "course", "graph_node"] = Query("resource"),
    title: Optional[str] = Query(None),
    content: Optional[str] = Query(None),
    description: Optional[str] = Query(None),
    course_id: Optional[int] = Query(None),
    current_user: User = Depends(require_role(["teacher"])),
) -> APIResponse:
    success = await search_service.index_document(doc_id, {
        "doc_type": doc_type, "title": title or "", "content": content or "",
        "description": description or "", "course_id": course_id,
        "tenant_id": current_user.tenant_id or 0, "uploader_id": current_user.id,
        "teacher_id": current_user.id, "is_public": False,
    })
    if not success:
        raise HTTPException(status_code=503, detail="搜索索引服务暂不可用")
    return APIResponse(message="索引成功")
