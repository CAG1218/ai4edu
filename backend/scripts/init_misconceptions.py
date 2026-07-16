"""
Misconception 一次性初始化脚本
遍历 COMMON_MISCONCEPTIONS 规则库，按 subject + keywords 匹配节点 name，
以 source: "system" 写入 misconceptions 字段，设置 has_misconception=true

使用方法:
    cd backend
    python -m scripts.init_misconceptions
"""
import asyncio
import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# 将 backend 目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neo4j import AsyncGraphDatabase

from app.agents.anti_misconception_agent import COMMON_MISCONCEPTIONS
from app.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


async def init_misconceptions() -> None:
    """从 COMMON_MISCONCEPTIONS 规则库初始化 Neo4j 节点的 misconception 标注"""
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )

    total_matched = 0
    total_mc_written = 0

    try:
        async with driver.session() as session:
            for mc in COMMON_MISCONCEPTIONS:
                subject = mc.get("subject", "")
                keywords = mc.get("keywords", [])

                if not subject:
                    continue

                # 查询该学科的所有 KnowledgeNode
                result = await session.run(
                    "MATCH (n:KnowledgeNode {subject: $subject}) RETURN n",
                    {"subject": subject},
                )
                records = await result.data()

                for record in records:
                    node = record["n"]
                    node_id = node.get("id", "")
                    node_name = node.get("name", "")
                    node_desc = node.get("description", "") or ""

                    # 关键词匹配：检查 node name 或 description 是否包含任一 keyword
                    match_text = (node_name + " " + node_desc).lower()
                    matched_keywords = [
                        kw for kw in keywords if kw.lower() in match_text
                    ]

                    if not matched_keywords:
                        continue

                    # 也检查 topic 是否在 name 中
                    topic = mc.get("topic", "")
                    if topic and topic in node_name:
                        matched = True
                    elif matched_keywords:
                        matched = True
                    else:
                        matched = False

                    if not matched:
                        continue

                    # 构建 misconception 项
                    new_mc: Dict[str, Any] = {
                        "mc_id": "mc_" + uuid.uuid4().hex[:8],
                        "misconception": mc.get("misconception", ""),
                        "correction": mc.get("correction", ""),
                        "topic": topic,
                        "keywords": keywords,
                        "source": "system",
                        "annotated_by": None,
                        "annotated_at": datetime.now(timezone.utc).isoformat(),
                        "confidence": 1.0,
                    }

                    # 读取现有 misconceptions
                    existing_mc_raw = node.get("misconceptions")
                    existing_mc: List[Dict[str, Any]] = []
                    if existing_mc_raw:
                        if isinstance(existing_mc_raw, str):
                            try:
                                existing_mc = json.loads(existing_mc_raw)
                            except (json.JSONDecodeError, TypeError):
                                existing_mc = []
                        elif isinstance(existing_mc_raw, list):
                            existing_mc = existing_mc_raw

                    # 避免重复写入（检查 misconception 文本是否已存在）
                    already_exists = any(
                        item.get("misconception") == new_mc["misconception"]
                        for item in existing_mc
                    )
                    if already_exists:
                        logger.info(f"  [{node_id}] misconception 已存在，跳过: {new_mc['misconception'][:30]}...")
                        continue

                    existing_mc.append(new_mc)
                    mc_json = json.dumps(existing_mc, ensure_ascii=False)

                    await session.run(
                        "MATCH (n:KnowledgeNode {id: $node_id}) "
                        "SET n.misconceptions = $mc_json, "
                        "    n.has_misconception = true",
                        {"node_id": node_id, "mc_json": mc_json},
                    )

                    total_mc_written += 1
                    total_matched += 1
                    logger.info(
                        f"  [{node_id}] 写入 misconception: {new_mc['misconception'][:40]}..."
                    )

        logger.info(
            f"\n初始化完成: 共匹配 {total_matched} 个节点, "
            f"写入 {total_mc_written} 条 misconception 标注"
        )

    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(init_misconceptions())
