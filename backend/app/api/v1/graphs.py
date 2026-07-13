"""
AI4Edu 知识图谱 API
提供图谱广场、节点查询、邻居遍历、推荐、misconception管理、跨学科图谱、任务查询等端点
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, require_role
from app.database import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.graph import (
    MisconceptionCreate,
    MisconceptionUpdate,
    AutoSuggestResponse,
)
from app.services.graph_service import graph_service
from app.agents.anti_misconception_agent import AntiMisconceptionAgent

router = APIRouter()

# AntiMisconception Agent 实例（用于 AI 辅助标注）
_anti_mc_agent = AntiMisconceptionAgent()


@router.get("/square", summary="图谱广场")
async def get_square(
    user: User = Depends(get_current_user),
) -> APIResponse:
    """获取学科分类广场统计（12学科 + 节点数 + 完整度 + misconception计数）"""
    stats = await graph_service.get_square_stats()
    return APIResponse(data=stats)


@router.get("/nodes/{node_id}", summary="获取节点详情")
async def get_node_detail(
    node_id: str,
    user: User = Depends(get_current_user),
) -> APIResponse:
    """获取知识节点详情"""
    node = await graph_service.get_node_detail(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    return APIResponse(data=node)


@router.get("/nodes/{node_id}/neighbors", summary="获取邻居节点")
async def get_neighbors(
    node_id: str,
    depth: int = Query(1, ge=1, le=3, description="BFS深度"),
    limit: int = Query(50, ge=1, le=200, description="返回数量上限"),
    user: User = Depends(get_current_user),
) -> APIResponse:
    """BFS获取节点的邻居子图"""
    result = await graph_service.get_neighbors(node_id, depth=depth, limit=limit)
    return APIResponse(data=result)


@router.get("/nodes/{node_id}/resources", summary="获取节点关联资源")
async def get_node_resources(
    node_id: str,
    user: User = Depends(get_current_user),
) -> APIResponse:
    """获取知识点关联的资源列表"""
    resources = await graph_service.get_node_resources(node_id)
    return APIResponse(data=resources)


@router.get("/nodes/{node_id}/recommendations", summary="获取推荐节点")
async def get_node_recommendations(
    node_id: str,
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
    user: User = Depends(get_current_user),
) -> APIResponse:
    """基于同路径、同学科和跨学科关联获取推荐节点"""
    recommendations = await graph_service.get_recommendations(node_id, limit=limit)
    return APIResponse(data=recommendations)


@router.get("/nodes/{node_id}/cognitive", summary="获取认知目标")
async def get_cognitive_goals(
    node_id: str,
    include_avg: bool = Query(False, description="是否包含学科均值"),
    user: User = Depends(get_current_user),
) -> APIResponse:
    """获取节点的认知目标雷达图数据（六维）"""
    data = await graph_service.get_cognitive_goals(node_id, include_avg=include_avg)
    if not data:
        raise HTTPException(status_code=404, detail="节点不存在")
    return APIResponse(data=data)


@router.post("/nodes", summary="创建知识节点")
async def create_node(
    id: str = Query(..., description="节点ID"),
    name: str = Query(..., description="节点名称"),
    subject: str = Query(..., description="学科分类"),
    description: Optional[str] = Query(None, description="节点描述"),
    cognitive_level: Optional[str] = Query(None, description="认知水平JSON"),
    has_misconception: bool = Query(False, description="是否有误解标注"),
    misconceptions: Optional[str] = Query(None, description="误解标注JSON"),
    user: User = Depends(require_role(["teacher", "admin", "super_admin"])),
) -> APIResponse:
    """创建新的知识节点（教师+权限）"""
    node_data: dict = {"id": id, "name": name, "subject": subject}
    if description:
        node_data["description"] = description
    if cognitive_level:
        node_data["cognitive_level"] = cognitive_level
    node_data["has_misconception"] = has_misconception
    if misconceptions:
        node_data["misconceptions"] = misconceptions

    node = await graph_service.create_node(node_data)
    return APIResponse(data=node, message="节点创建成功")


@router.put("/nodes/{node_id}", summary="更新知识节点")
async def update_node(
    node_id: str,
    name: Optional[str] = Query(None, description="节点名称"),
    description: Optional[str] = Query(None, description="节点描述"),
    cognitive_level: Optional[str] = Query(None, description="认知水平JSON"),
    has_misconception: Optional[bool] = Query(None, description="是否有误解标注"),
    misconceptions: Optional[str] = Query(None, description="误解标注JSON"),
    user: User = Depends(require_role(["teacher", "admin", "super_admin"])),
) -> APIResponse:
    """更新知识节点属性（教师+权限）"""
    update_data: dict = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if cognitive_level is not None:
        update_data["cognitive_level"] = cognitive_level
    if has_misconception is not None:
        update_data["has_misconception"] = has_misconception
    if misconceptions is not None:
        update_data["misconceptions"] = misconceptions

    if not update_data:
        raise HTTPException(status_code=400, detail="未提供更新数据")

    node = await graph_service.update_node(node_id, update_data)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    return APIResponse(data=node, message="节点更新成功")


@router.post("/nodes/{from_id}/link/{to_id}", summary="创建节点关系")
async def create_relationship(
    from_id: str,
    to_id: str,
    rel_type: str = Query("RELATED", description="关系类型"),
    label: Optional[str] = Query(None, description="关系标签"),
    user: User = Depends(require_role(["teacher", "admin", "super_admin"])),
) -> APIResponse:
    """创建两个知识节点之间的关系（教师+权限）"""
    result = await graph_service.create_relationship(from_id, to_id, rel_type, label)
    if not result:
        raise HTTPException(status_code=400, detail="创建关系失败，请检查节点是否存在")
    return APIResponse(data=result, message="关系创建成功")


@router.delete("/nodes/{from_id}/link/{to_id}", summary="删除节点关系")
async def delete_relationship(
    from_id: str,
    to_id: str,
    rel_type: str = Query("RELATED", description="关系类型"),
    user: User = Depends(require_role(["teacher", "admin", "super_admin"])),
) -> APIResponse:
    """删除两个知识节点之间的关系（教师+权限）"""
    await graph_service.delete_relationship(from_id, to_id, rel_type)
    return APIResponse(message="关系删除成功")


@router.get("/search", summary="搜索知识节点")
async def search_nodes(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    user: User = Depends(get_current_user),
) -> APIResponse:
    """搜索知识节点"""
    results = await graph_service.search_nodes(q, subject=subject, limit=limit)
    return APIResponse(data=results)


# ==================== Misconception 端点 ====================

@router.get("/nodes/{node_id}/misconceptions", summary="获取节点误解标注")
async def get_misconceptions(
    node_id: str,
    user: User = Depends(get_current_user),
) -> APIResponse:
    """获取节点的误解标注列表（全体用户可访问）"""
    misconceptions = await graph_service.get_misconceptions(node_id)
    return APIResponse(data=misconceptions)


@router.post("/nodes/{node_id}/misconceptions", summary="添加误解标注")
async def add_misconception(
    node_id: str,
    body: MisconceptionCreate,
    user: User = Depends(require_role(["teacher", "admin", "super_admin"])),
) -> APIResponse:
    """添加误解标注（教师+权限）"""
    # 验证节点存在
    node = await graph_service.get_node_detail(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    data = body.model_dump()
    mc = await graph_service.add_misconception(node_id, data, user.id)
    return APIResponse(data=mc, message="误解标注添加成功")


@router.put("/nodes/{node_id}/misconceptions/{mc_id}", summary="编辑误解标注")
async def update_misconception(
    node_id: str,
    mc_id: str,
    body: MisconceptionUpdate,
    user: User = Depends(require_role(["teacher", "admin", "super_admin"])),
) -> APIResponse:
    """编辑误解标注（教师+权限）"""
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="未提供更新数据")

    mc = await graph_service.update_misconception(node_id, mc_id, data)
    if not mc:
        raise HTTPException(status_code=404, detail="误解标注不存在")
    return APIResponse(data=mc, message="误解标注更新成功")


@router.delete("/nodes/{node_id}/misconceptions/{mc_id}", summary="删除误解标注")
async def delete_misconception(
    node_id: str,
    mc_id: str,
    user: User = Depends(require_role(["teacher", "admin", "super_admin"])),
) -> APIResponse:
    """删除误解标注（教师+权限）"""
    success = await graph_service.delete_misconception(node_id, mc_id)
    if not success:
        raise HTTPException(status_code=404, detail="误解标注不存在")
    return APIResponse(message="删除成功")


@router.post("/nodes/{node_id}/misconceptions/auto-suggest", summary="AI辅助标注建议")
async def auto_suggest_misconceptions(
    node_id: str,
    user: User = Depends(require_role(["teacher", "admin", "super_admin"])),
) -> APIResponse:
    """AI辅助标注建议（教师+权限）"""
    # 获取节点详情
    node = await graph_service.get_node_detail(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")

    node_name = node.get("name", "")
    node_desc = node.get("description", "") or ""
    node_subject = node.get("subject", "")

    # 调用 Agent 获取建议
    suggestions = _anti_mc_agent.suggest_for_node(node_name, node_desc, node_subject)

    response = AutoSuggestResponse(
        suggestions=suggestions,
        total=len(suggestions),
    )
    return APIResponse(data=response.model_dump())


# ==================== 任务端点 ====================

@router.get("/nodes/{node_id}/tasks", summary="获取节点关联任务")
async def get_node_tasks(
    node_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """获取节点关联的学习任务（全体用户可访问）"""
    tasks = await graph_service.get_node_tasks(node_id, db, user_id=user.id)
    return APIResponse(data=tasks)


# ==================== 跨学科图谱端点 ====================

@router.get("/cross-subject", summary="跨学科关联图谱")
async def get_cross_subject_graph(
    subjects: str = Query(..., description="学科ID列表，逗号分隔，如 math,physics"),
    min_strength: float = Query(0.0, ge=0.0, le=1.0, description="最小关系强度阈值"),
    max_nodes: int = Query(100, ge=10, le=500, description="最大节点数"),
    user: User = Depends(get_current_user),
) -> APIResponse:
    """获取跨学科知识点关联网络（全体用户可访问）"""
    subject_list = [s.strip() for s in subjects.split(",") if s.strip()]
    if len(subject_list) < 2:
        raise HTTPException(status_code=400, detail="至少需要选择2个学科")

    result = await graph_service.get_cross_subject_graph(
        subjects=subject_list,
        min_strength=min_strength,
        max_nodes=max_nodes,
    )
    return APIResponse(data=result)
