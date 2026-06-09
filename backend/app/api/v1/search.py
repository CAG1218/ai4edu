"""
AI4Edu 搜索 API
提供混合检索、搜索建议、热门搜索、手动索引等端点
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas.common import APIResponse
from app.services.search_service import search_service

router = APIRouter()


@router.get("/", summary="混合检索")
async def search(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    search_type: Optional[str] = Query("all", description="搜索类型: all/note/resource/graph_node/course"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
) -> APIResponse:
    """
    混合检索：BM25(ES) + 向量(Chroma) + RRF 融合排序
    """
    result = await search_service.hybrid_search(q, search_type=search_type, limit=limit)
    return APIResponse(data=result)


@router.get("/suggest", summary="搜索建议")
async def search_suggest(
    q: str = Query(..., min_length=1, description="输入前缀"),
    limit: int = Query(10, ge=1, le=20, description="建议数量"),
) -> APIResponse:
    """搜索自动补全建议"""
    suggestions = await search_service.suggest(q, limit=limit)
    return APIResponse(data=suggestions)


@router.get("/hot", summary="热门搜索")
async def hot_searches(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
) -> APIResponse:
    """获取热门搜索关键词"""
    hot_list = await search_service.get_hot_searches(limit=limit)
    return APIResponse(data=hot_list)


@router.post("/index", summary="手动索引")
async def index_document(
    doc_id: str = Query(..., description="文档ID"),
    doc_type: Optional[str] = Query(None, description="文档类型"),
    title: Optional[str] = Query(None, description="标题"),
    content: Optional[str] = Query(None, description="内容"),
    description: Optional[str] = Query(None, description="描述"),
) -> APIResponse:
    """
    手动索引文档到 ES + Chroma
    """
    doc_data = {}
    if title:
        doc_data["title"] = title
    if content:
        doc_data["content"] = content
    if description:
        doc_data["description"] = description
    if doc_type:
        doc_data["doc_type"] = doc_type

    success = await search_service.index_document(doc_id, doc_data)
    if not success:
        raise HTTPException(status_code=500, detail="索引失败")
    return APIResponse(message="索引成功")
