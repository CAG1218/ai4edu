"""
AI4Edu 知识图谱 API
提供图谱广场、节点查询、邻居遍历、推荐等端点
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.common import APIResponse
from app.services.graph_service import graph_service

router = APIRouter()


@router.get("/square", summary="图谱广场")
async def get_square() -> APIResponse:
    """获取学科分类广场统计（12学科 + 节点数 + 完整度）"""
    stats = await graph_service.get_square_stats()
    return APIResponse(data=stats)


@router.get("/nodes/{node_id}", summary="获取节点详情")
async def get_node_detail(node_id: str) -> APIResponse:
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
) -> APIResponse:
    """BFS获取节点的邻居子图"""
    result = await graph_service.get_neighbors(node_id, depth=depth, limit=limit)
    return APIResponse(data=result)


@router.get("/nodes/{node_id}/resources", summary="获取节点关联资源")
async def get_node_resources(node_id: str) -> APIResponse:
    """获取知识点关联的资源列表"""
    resources = await graph_service.get_node_resources(node_id)
    return APIResponse(data=resources)


@router.get("/nodes/{node_id}/recommendations", summary="获取推荐节点")
async def get_node_recommendations(
    node_id: str,
    limit: int = Query(10, ge=1, le=50, description="推荐数量"),
) -> APIResponse:
    """基于同路径和相似标签获取推荐节点"""
    recommendations = await graph_service.get_recommendations(node_id, limit=limit)
    return APIResponse(data=recommendations)


@router.get("/nodes/{node_id}/cognitive", summary="获取认知目标")
async def get_cognitive_goals(node_id: str) -> APIResponse:
    """获取节点的认知目标雷达图数据（六维）"""
    data = await graph_service.get_cognitive_goals(node_id)
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
) -> APIResponse:
    """创建新的知识节点"""
    node_data = {"id": id, "name": name, "subject": subject}
    if description:
        node_data["description"] = description
    if cognitive_level:
        node_data["cognitive_level"] = cognitive_level

    node = await graph_service.create_node(node_data)
    return APIResponse(data=node, message="节点创建成功")


@router.put("/nodes/{node_id}", summary="更新知识节点")
async def update_node(
    node_id: str,
    name: Optional[str] = Query(None, description="节点名称"),
    description: Optional[str] = Query(None, description="节点描述"),
    cognitive_level: Optional[str] = Query(None, description="认知水平JSON"),
) -> APIResponse:
    """更新知识节点属性"""
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if cognitive_level is not None:
        update_data["cognitive_level"] = cognitive_level

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
) -> APIResponse:
    """创建两个知识节点之间的关系"""
    result = await graph_service.create_relationship(from_id, to_id, rel_type, label)
    if not result:
        raise HTTPException(status_code=400, detail="创建关系失败，请检查节点是否存在")
    return APIResponse(data=result, message="关系创建成功")


@router.delete("/nodes/{from_id}/link/{to_id}", summary="删除节点关系")
async def delete_relationship(
    from_id: str,
    to_id: str,
    rel_type: str = Query("RELATED", description="关系类型"),
) -> APIResponse:
    """删除两个知识节点之间的关系"""
    await graph_service.delete_relationship(from_id, to_id, rel_type)
    return APIResponse(message="关系删除成功")


@router.get("/search", summary="搜索知识节点")
async def search_nodes(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    subject: Optional[str] = Query(None, description="学科筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
) -> APIResponse:
    """搜索知识节点"""
    results = await graph_service.search_nodes(q, subject=subject, limit=limit)
    return APIResponse(data=results)
