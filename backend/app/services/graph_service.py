"""
AI4Edu 知识图谱 Service
基于 Neo4j 实现知识图谱查询、BFS邻居发现、推荐等业务逻辑
所有 Cypher 查询均使用参数化以防止注入
"""
import logging
from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

# 12个学科分类
SUBJECT_CATEGORIES = [
    {"id": "math", "name": "数学", "icon": "Calculator", "color": "#1976D2"},
    {"id": "physics", "name": "物理学", "icon": "Cpu", "color": "#F57C00"},
    {"id": "chemistry", "name": "化学", "icon": "Flask", "color": "#4CAF50"},
    {"id": "biology", "name": "生物学", "icon": "Microscope", "color": "#388E3C"},
    {"id": "cs", "name": "计算机科学", "icon": "Monitor", "color": "#7B1FA2"},
    {"id": "chinese", "name": "语文", "icon": "Reading", "color": "#D32F2F"},
    {"id": "english", "name": "英语", "icon": "ChatDotRound", "color": "#00796B"},
    {"id": "history", "name": "历史", "icon": "Clock", "color": "#5D4037"},
    {"id": "geography", "name": "地理", "icon": "Place", "color": "#0288D1"},
    {"id": "politics", "name": "政治", "icon": "Stamp", "color": "#C62828"},
    {"id": "pe", "name": "体育", "icon": "TrophyBase", "color": "#FF6F00"},
    {"id": "art", "name": "艺术", "icon": "Brush", "color": "#AD1457"},
]


class GraphService:
    """知识图谱服务"""

    def __init__(self):
        """初始化 Neo4j 驱动"""
        self._driver: Optional[AsyncDriver] = None

    async def _get_driver(self) -> AsyncDriver:
        """获取 Neo4j 异步驱动（懒加载单例）"""
        if self._driver is None:
            self._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
        return self._driver

    async def close(self):
        """关闭驱动连接"""
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def _run(self, cypher: str, params: Optional[Dict] = None) -> List[Dict]:
        """执行参数化 Cypher 查询并返回记录列表"""
        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run(cypher, params or {})
            records = await result.data()
            return records

    # ==================== 图谱广场 ====================

    async def get_square_stats(self, tenant_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取学科广场统计：每个学科的节点数和完整度
        """
        stats = []
        for subject in SUBJECT_CATEGORIES:
            # 统计该学科下的节点数
            count_result = await self._run(
                "MATCH (n:KnowledgeNode {subject: $subject}) RETURN count(n) AS cnt",
                {"subject": subject["id"]},
            )
            node_count = count_result[0]["cnt"] if count_result else 0

            # 统计该学科下有描述的节点数（用于计算完整度）
            desc_result = await self._run(
                "MATCH (n:KnowledgeNode {subject: $subject}) "
                "WHERE n.description IS NOT NULL AND n.description <> '' "
                "RETURN count(n) AS cnt",
                {"subject": subject["id"]},
            )
            desc_count = desc_result[0]["cnt"] if desc_result else 0

            completeness = await self.calculate_completeness(subject["id"])

            stats.append({
                "id": subject["id"],
                "name": subject["name"],
                "icon": subject["icon"],
                "color": subject["color"],
                "node_count": node_count,
                "completeness": completeness,
            })

        return stats

    async def calculate_completeness(self, subject: str) -> float:
        """
        计算某学科的知识图谱完整度（0-100）
        基于节点属性填充率和关系密度
        """
        # 节点总数
        node_result = await self._run(
            "MATCH (n:KnowledgeNode {subject: $subject}) RETURN count(n) AS cnt",
            {"subject": subject},
        )
        total_nodes = node_result[0]["cnt"] if node_result else 0
        if total_nodes == 0:
            return 0.0

        # 有描述的节点数
        desc_result = await self._run(
            "MATCH (n:KnowledgeNode {subject: $subject}) "
            "WHERE n.description IS NOT NULL AND n.description <> '' "
            "RETURN count(n) AS cnt",
            {"subject": subject},
        )
        desc_nodes = desc_result[0]["cnt"] if desc_result else 0

        # 有认知目标的节点数
        cog_result = await self._run(
            "MATCH (n:KnowledgeNode {subject: $subject}) "
            "WHERE n.cognitive_level IS NOT NULL "
            "RETURN count(n) AS cnt",
            {"subject": subject},
        )
        cog_nodes = cog_result[0]["cnt"] if cog_result else 0

        # 关系数
        rel_result = await self._run(
            "MATCH (:KnowledgeNode {subject: $subject})-[r]->(:KnowledgeNode {subject: $subject}) "
            "RETURN count(r) AS cnt",
            {"subject": subject},
        )
        rel_count = rel_result[0]["cnt"] if rel_result else 0

        # 完整度 = 属性填充率(60%) + 关系密度(40%)
        attr_score = (desc_nodes / total_nodes * 0.5 + cog_nodes / total_nodes * 0.5) * 60
        # 关系密度：期望每个节点至少2条关系
        density_score = min(rel_count / (total_nodes * 2) * 40, 40) if total_nodes > 0 else 0

        return round(min(attr_score + density_score, 100), 1)

    # ==================== 节点操作 ====================

    async def get_node_detail(self, node_id: str) -> Optional[Dict[str, Any]]:
        """获取节点详情"""
        result = await self._run(
            "MATCH (n:KnowledgeNode {id: $node_id}) RETURN n",
            {"node_id": node_id},
        )
        if not result:
            return None
        return result[0]["n"]

    async def get_neighbors(self, node_id: str, depth: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        BFS 获取邻居节点和关系
        """
        # 获取目标节点
        node_result = await self._run(
            "MATCH (n:KnowledgeNode {id: $node_id}) RETURN n",
            {"node_id": node_id},
        )
        if not node_result:
            return {"nodes": [], "links": []}

        # BFS 遍历邻居
        cypher = (
            "MATCH path = (start:KnowledgeNode {id: $node_id})-[:RELATED*1..%d]-(neighbor:KnowledgeNode) "
            "RETURN DISTINCT neighbor, "
            "[rel in relationships(path) | {source: startNode(rel).id, target: endNode(rel).id, type: type(rel), label: rel.label}] AS rels "
            "LIMIT $limit"
        ) % depth

        records = await self._run(cypher, {"node_id": node_id, "limit": limit})

        nodes_map = {node_id: node_result[0]["n"]}
        links = []

        for record in records:
            neighbor = record["neighbor"]
            nodes_map[neighbor["id"]] = neighbor
            for rel in record["rels"]:
                link = {
                    "source": rel["source"],
                    "target": rel["target"],
                    "type": rel["type"],
                    "label": rel.get("label", rel["type"]),
                }
                # 去重
                if not any(l["source"] == link["source"] and l["target"] == link["target"] for l in links):
                    links.append(link)

        return {
            "nodes": list(nodes_map.values()),
            "links": links,
        }

    async def get_node_resources(self, node_id: str) -> List[Dict[str, Any]]:
        """获取节点关联资源"""
        result = await self._run(
            "MATCH (n:KnowledgeNode {id: $node_id})-[:HAS_RESOURCE]->(r:Resource) RETURN r",
            {"node_id": node_id},
        )
        return [record["r"] for record in result]

    async def get_recommendations(self, node_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取推荐节点：基于同路径和相似标签
        """
        # 同路径上的兄弟节点
        sibling_result = await self._run(
            "MATCH (n:KnowledgeNode {id: $node_id})-[:RELATED]->(parent)-[:RELATED]->(sibling:KnowledgeNode) "
            "WHERE sibling.id <> $node_id "
            "RETURN DISTINCT sibling "
            "LIMIT $limit",
            {"node_id": node_id, "limit": limit},
        )

        recommendations = [record["sibling"] for record in sibling_result]

        # 如果不够，补充同学科节点
        if len(recommendations) < limit:
            node_detail = await self.get_node_detail(node_id)
            if node_detail and node_detail.get("subject"):
                same_subject = await self._run(
                    "MATCH (n:KnowledgeNode {subject: $subject}) "
                    "WHERE n.id <> $node_id "
                    "RETURN n "
                    "LIMIT $extra_limit",
                    {
                        "subject": node_detail["subject"],
                        "node_id": node_id,
                        "extra_limit": limit - len(recommendations),
                    },
                )
                recommendations.extend([record["n"] for record in same_subject])

        return recommendations[:limit]

    async def search_nodes(self, query: str, subject: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索知识节点（参数化查询防注入）
        """
        if subject:
            result = await self._run(
                "MATCH (n:KnowledgeNode {subject: $subject}) "
                "WHERE n.name CONTAINS $query OR n.description CONTAINS $query "
                "RETURN n LIMIT $limit",
                {"subject": subject, "query": query, "limit": limit},
            )
        else:
            result = await self._run(
                "MATCH (n:KnowledgeNode) "
                "WHERE n.name CONTAINS $query OR n.description CONTAINS $query "
                "RETURN n LIMIT $limit",
                {"query": query, "limit": limit},
            )
        return [record["n"] for record in result]

    async def create_node(self, node_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建知识节点
        """
        props = ", ".join(f"{k}: ${k}" for k in node_data.keys())
        cypher = f"CREATE (n:KnowledgeNode {{{props}}}) RETURN n"
        result = await self._run(cypher, node_data)
        return result[0]["n"] if result else {}

    async def update_node(self, node_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        更新知识节点属性
        """
        set_clauses = ", ".join(f"n.{k} = ${k}" for k in update_data.keys())
        params = {"node_id": node_id, **update_data}
        cypher = f"MATCH (n:KnowledgeNode {{id: $node_id}}) SET {set_clauses} RETURN n"
        result = await self._run(cypher, params)
        return result[0]["n"] if result else None

    async def create_relationship(
        self, from_id: str, to_id: str, rel_type: str = "RELATED", label: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        创建节点间关系

        注意：Neo4j Cypher 不支持将关系类型作为参数传递，
        因此必须对 rel_type 进行白名单校验以防止 Cypher 注入。
        """
        # 白名单校验 rel_type，防止 Cypher 注入
        import re
        if not re.match(r"^[A-Z_][A-Z0-9_]*$", rel_type):
            raise ValueError(f"Invalid relationship type: {rel_type}. Must be UPPER_CASE_WITH_UNDERSCORES only.")

        params: Dict[str, Any] = {"from_id": from_id, "to_id": to_id, "label": label}
        if label:
            cypher = (
                "MATCH (a:KnowledgeNode {id: $from_id}), (b:KnowledgeNode {id: $to_id}) "
                f"CREATE (a)-[r:{rel_type} {{label: $label}}]->(b) RETURN type(r) AS rel_type, properties(r) AS props"
            )
        else:
            cypher = (
                "MATCH (a:KnowledgeNode {id: $from_id}), (b:KnowledgeNode {id: $to_id}) "
                f"CREATE (a)-[r:{rel_type}]->(b) RETURN type(r) AS rel_type, properties(r) AS props"
            )

        result = await self._run(cypher, params)
        if result:
            return {"type": result[0]["rel_type"], "props": result[0]["props"]}
        return None

    async def delete_relationship(self, from_id: str, to_id: str, rel_type: str = "RELATED") -> bool:
        """
        删除节点间关系

        注意：与 create_relationship 同理，rel_type 需白名单校验。
        """
        import re
        if not re.match(r"^[A-Z_][A-Z0-9_]*$", rel_type):
            raise ValueError(f"Invalid relationship type: {rel_type}. Must be UPPER_CASE_WITH_UNDERSCORES only.")

        await self._run(
            f"MATCH (a:KnowledgeNode {{id: $from_id}})-[r:{rel_type}]->(b:KnowledgeNode {{id: $to_id}}) DELETE r",
            {"from_id": from_id, "to_id": to_id},
        )
        return True

    async def get_cognitive_goals(self, node_id: str) -> Dict[str, Any]:
        """
        获取节点的认知目标雷达图数据
        六维：记忆、理解、应用、分析、评价、创造
        """
        node = await self.get_node_detail(node_id)
        if not node:
            return {}

        cognitive_level = node.get("cognitive_level", {})
        if isinstance(cognitive_level, str):
            import json
            try:
                cognitive_level = json.loads(cognitive_level)
            except (json.JSONDecodeError, TypeError):
                cognitive_level = {}

        # 默认六维数据
        dimensions = ["记忆", "理解", "应用", "分析", "评价", "创造"]
        dimension_keys = ["remember", "understand", "apply", "analyze", "evaluate", "create"]

        values = []
        for key in dimension_keys:
            values.append(cognitive_level.get(key, 0))

        return {
            "dimensions": dimensions,
            "values": values,
            "node_name": node.get("name", ""),
        }


# 全局单例
graph_service = GraphService()
