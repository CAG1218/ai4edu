"""Initialize a small, reusable knowledge graph for all supported subjects.

Usage:
    cd backend
    python -m scripts.init_graph_data

The script is idempotent: nodes and relationships are merged by stable IDs, so
it is safe to run again after restarting the development environment.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neo4j import AsyncGraphDatabase

from app.config import settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


SUBJECT_NODES: dict[str, list[tuple[str, str, str]]] = {
    "math": [
        ("math_functions", "函数", "研究变量之间的对应关系、图像与基本性质。"),
        ("math_derivatives", "导数", "描述函数的瞬时变化率，并用于研究单调性与极值。"),
        ("math_probability", "概率", "用数学方法描述随机事件及其发生可能性。"),
        ("math_vectors", "向量", "用大小和方向描述量，并进行线性运算。"),
    ],
    "physics": [
        ("physics_motion", "运动学", "描述物体的位置、速度和加速度随时间的变化。"),
        ("physics_newton_laws", "牛顿运动定律", "建立力、质量与运动状态变化之间的联系。"),
        ("physics_energy", "功和能", "通过功、动能和势能分析物理过程中的能量转化。"),
        ("physics_waves", "机械波", "研究振动在介质中的传播规律及波的基本特征。"),
    ],
    "chemistry": [
        ("chemistry_atoms", "原子结构", "认识原子的组成、电子排布和元素性质。"),
        ("chemistry_bonds", "化学键", "理解原子之间通过电子相互作用形成物质。"),
        ("chemistry_reactions", "化学反应", "研究物质转化过程、反应方程式与能量变化。"),
        ("chemistry_acid_base", "酸碱反应", "研究酸、碱的性质以及中和与离子反应。"),
    ],
    "biology": [
        ("biology_cells", "细胞", "认识生命活动的基本结构和功能单位。"),
        ("biology_genetics", "遗传规律", "研究遗传信息的传递、表达和性状分离。"),
        ("biology_evolution", "生物进化", "理解自然选择与物种演化的基本机制。"),
        ("biology_ecology", "生态系统", "研究生物与环境之间的相互作用及能量流动。"),
    ],
    "cs": [
        ("cs_algorithms", "算法", "用明确步骤解决计算问题，并分析正确性与效率。"),
        ("cs_data_structures", "数据结构", "组织和存储数据以支持高效访问与修改。"),
        ("cs_networks", "计算机网络", "理解数据在网络中的分层传输与通信协议。"),
        ("cs_ai", "人工智能", "研究机器感知、推理、学习和决策的方法。"),
    ],
    "chinese": [
        ("chinese_classics", "文言文阅读", "理解常见文言实词、句式和古代文本内容。"),
        ("chinese_reading", "现代文阅读", "分析文本结构、表达手法和作者观点。"),
        ("chinese_writing", "写作", "围绕主题组织材料并准确、连贯地表达观点。"),
        ("chinese_rhetoric", "修辞", "识别并运用比喻、拟人、排比等表达手法。"),
    ],
    "english": [
        ("english_vocabulary", "英语词汇", "掌握词义、词形变化和语境中的正确用法。"),
        ("english_grammar", "英语语法", "理解句子结构、时态、语态和从句规则。"),
        ("english_reading", "英语阅读", "获取文本信息并推断主旨、态度和逻辑关系。"),
        ("english_writing", "英语写作", "使用恰当词汇和句式清晰表达信息与观点。"),
    ],
    "history": [
        ("history_ancient_china", "中国古代史", "认识中国古代政治、经济与文化的发展脉络。"),
        ("history_modern_china", "中国近现代史", "理解近代以来中国社会变迁与现代化进程。"),
        ("history_world", "世界史", "从全球视角认识文明交流与世界格局演变。"),
        ("history_industrial_revolution", "工业革命", "理解技术进步对生产方式和社会结构的影响。"),
    ],
    "geography": [
        ("geography_maps", "地图基础", "使用比例尺、方向和图例读取与表达空间信息。"),
        ("geography_climate", "气候", "分析气温、降水分布及其主要影响因素。"),
        ("geography_plate_tectonics", "板块构造", "解释地震、火山和地形形成的基本机制。"),
        ("geography_human", "人文地理", "研究人口、城市和产业活动的空间分布。"),
    ],
    "politics": [
        ("politics_constitution", "宪法与法治", "理解宪法地位、公民权利义务和法治原则。"),
        ("politics_economy", "经济生活", "分析市场、生产、消费和宏观调控等经济现象。"),
        ("politics_philosophy", "生活与哲学", "运用辩证和历史的观点认识与解决问题。"),
        ("politics_international", "国际关系", "认识国家利益、国际组织与全球治理。"),
    ],
    "pe": [
        ("pe_physiology", "运动生理", "理解运动对人体机能和能量代谢的影响。"),
        ("pe_skills", "运动技能", "掌握基本动作模式与专项运动技术。"),
        ("pe_fitness", "体能训练", "科学发展力量、速度、耐力、柔韧与协调能力。"),
        ("pe_health", "运动健康", "学习运动安全、损伤预防与健康生活方式。"),
    ],
    "art": [
        ("art_color", "色彩", "理解色彩属性、搭配规律及其视觉和情感作用。"),
        ("art_composition", "构图", "运用比例、均衡、对比与节奏组织视觉元素。"),
        ("art_history", "艺术史", "认识代表性艺术流派、作品及其时代背景。"),
        ("art_design", "艺术设计", "围绕需求综合运用造型、色彩和媒介完成创作。"),
    ],
}


# (source ID, target ID, relationship type, display label)
WITHIN_SUBJECT_RELATIONSHIPS: list[tuple[str, str, str, str]] = []
for subject_nodes in SUBJECT_NODES.values():
    ids = [node[0] for node in subject_nodes]
    WITHIN_SUBJECT_RELATIONSHIPS.extend(
        [
            (ids[0], ids[1], "PREREQUISITE", "前置知识"),
            (ids[1], ids[2], "RELATED", "相关知识"),
            (ids[2], ids[3], "APPLICATION", "拓展应用"),
            (ids[0], ids[3], "RELATED", "主题关联"),
        ]
    )


CROSS_SUBJECT_RELATIONSHIPS = [
    ("math_vectors", "physics_motion", "APPLICATION", "向量描述运动"),
    ("math_functions", "physics_newton_laws", "APPLICATION", "函数建模"),
    ("math_probability", "biology_genetics", "APPLICATION", "遗传概率"),
    ("math_functions", "cs_algorithms", "RELATED", "计算与建模"),
    ("math_vectors", "art_composition", "APPLICATION", "空间与构图"),
    ("physics_energy", "chemistry_reactions", "RELATED", "反应能量变化"),
    ("physics_waves", "cs_networks", "RELATED", "信号传播"),
    ("chemistry_atoms", "biology_cells", "PREREQUISITE", "生命物质基础"),
    ("chemistry_reactions", "biology_cells", "APPLICATION", "细胞代谢"),
    ("biology_ecology", "geography_climate", "RELATED", "气候与生态"),
    ("biology_evolution", "history_world", "RELATED", "科学思想史"),
    ("chinese_writing", "english_writing", "RELATED", "跨语言写作"),
    ("chinese_rhetoric", "art_composition", "RELATED", "表达与审美"),
    ("history_industrial_revolution", "politics_economy", "RELATED", "工业化与经济"),
    ("history_world", "politics_international", "PREREQUISITE", "国际格局演变"),
    ("geography_human", "politics_economy", "RELATED", "区域经济"),
    ("cs_ai", "politics_philosophy", "RELATED", "智能与伦理"),
    ("cs_ai", "art_design", "APPLICATION", "智能设计"),
    ("pe_physiology", "biology_cells", "RELATED", "人体机能基础"),
    ("pe_health", "biology_ecology", "RELATED", "健康与环境"),
]


def cognitive_level(index: int) -> str:
    """Return varied but complete Bloom-dimension seed data."""
    profiles = [
        [80, 75, 55, 45, 30, 25],
        [70, 80, 70, 55, 40, 30],
        [65, 75, 75, 70, 50, 40],
        [60, 70, 75, 75, 60, 55],
    ]
    keys = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
    return json.dumps(dict(zip(keys, profiles[index % len(profiles)])), ensure_ascii=False)


async def initialize() -> dict[str, Any]:
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )
    relationships = WITHIN_SUBJECT_RELATIONSHIPS + CROSS_SUBJECT_RELATIONSHIPS

    try:
        await driver.verify_connectivity()
        async with driver.session() as session:
            await (
                await session.run(
                    "CREATE CONSTRAINT knowledge_node_id IF NOT EXISTS "
                    "FOR (n:KnowledgeNode) REQUIRE n.id IS UNIQUE"
                )
            ).consume()

            for subject, nodes in SUBJECT_NODES.items():
                for index, (node_id, name, description) in enumerate(nodes):
                    await (
                        await session.run(
                            "MERGE (n:KnowledgeNode {id: $id}) "
                            "ON CREATE SET n.has_misconception = false, n.misconceptions = '[]' "
                            "SET n.name = $name, n.subject = $subject, "
                            "n.description = $description, n.cognitive_level = $cognitive_level, "
                            "n.seed_source = 'ai4edu_base_v1'",
                            {
                                "id": node_id,
                                "name": name,
                                "subject": subject,
                                "description": description,
                                "cognitive_level": cognitive_level(index),
                            },
                        )
                    ).consume()

            allowed_types = {"PREREQUISITE", "APPLICATION", "RELATED"}
            for source, target, rel_type, label in relationships:
                if rel_type not in allowed_types:
                    raise ValueError(f"Unsupported relationship type: {rel_type}")
                await (
                    await session.run(
                        "MATCH (a:KnowledgeNode {id: $source}), (b:KnowledgeNode {id: $target}) "
                        f"MERGE (a)-[r:{rel_type}]->(b) "
                        "SET r.label = $label, r.seed_source = 'ai4edu_base_v1'",
                        {"source": source, "target": target, "label": label},
                    )
                ).consume()

            result = await session.run(
                "MATCH (n:KnowledgeNode) "
                "WITH count(n) AS nodes "
                "MATCH (:KnowledgeNode)-[r]->(:KnowledgeNode) "
                "RETURN nodes, count(r) AS relationships"
            )
            summary = await result.single()

            distribution_result = await session.run(
                "MATCH (n:KnowledgeNode) "
                "RETURN n.subject AS subject, count(n) AS count ORDER BY subject"
            )
            distribution = {
                row["subject"]: row["count"] async for row in distribution_result
            }

        return {
            "nodes": summary["nodes"] if summary else 0,
            "relationships": summary["relationships"] if summary else 0,
            "subjects": distribution,
        }
    finally:
        await driver.close()


async def main() -> None:
    result = await initialize()
    logger.info(
        "Knowledge graph initialized: %s nodes, %s relationships, subjects=%s",
        result["nodes"],
        result["relationships"],
        result["subjects"],
    )


if __name__ == "__main__":
    asyncio.run(main())
