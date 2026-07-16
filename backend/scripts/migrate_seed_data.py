"""
种子数据迁移脚本
1. 将 KnowledgeNode 节点的 subject 中文值映射为英文 ID
2. 将 cognitive_level JSON 中的中文 key 映射为英文 key

使用方法:
    cd backend
    python -m scripts.migrate_seed_data
"""
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

# 将 backend 目录加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from neo4j import AsyncGraphDatabase

from app.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# subject 中文 → 英文 ID 映射
SUBJECT_CN_TO_EN: Dict[str, str] = {
    "数学": "math",
    "物理": "physics",
    "物理学": "physics",
    "化学": "chemistry",
    "生物": "biology",
    "生物学": "biology",
    "计算机": "cs",
    "计算机科学": "cs",
    "语文": "chinese",
    "英语": "english",
    "历史": "history",
    "地理": "geography",
    "政治": "politics",
    "体育": "pe",
    "艺术": "art",
}

# cognitive_level 中文 key → 英文 key 映射
COG_KEY_CN_TO_EN: Dict[str, str] = {
    "记忆": "remember",
    "理解": "understand",
    "应用": "apply",
    "分析": "analyze",
    "评价": "evaluate",
    "创造": "create",
}

# 合法的英文 subject ID 集合（用于判断是否已是英文）
VALID_SUBJECT_IDS = {
    "math", "physics", "chemistry", "biology", "cs",
    "chinese", "english", "history", "geography",
    "politics", "pe", "art",
}

# 合法的英文 cognitive_level key 集合
VALID_COG_KEYS = {
    "remember", "understand", "apply", "analyze", "evaluate", "create",
}


async def migrate_seed_data() -> None:
    """执行种子数据迁移"""
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    )

    subject_migrated = 0
    cog_migrated = 0
    total_nodes = 0

    try:
        async with driver.session() as session:
            # 获取所有 KnowledgeNode 节点
            result = await session.run("MATCH (n:KnowledgeNode) RETURN n")
            records = await result.data()

            for record in records:
                node = record["n"]
                total_nodes += 1
                node_id = node.get("id", "")
                updates: Dict[str, Any] = {}

                # === 迁移 subject ===
                subject_val = node.get("subject", "")
                if subject_val and subject_val not in VALID_SUBJECT_IDS:
                    mapped = SUBJECT_CN_TO_EN.get(subject_val)
                    if mapped:
                        updates["subject"] = mapped
                        subject_migrated += 1
                        logger.info(f"  [{node_id}] subject: '{subject_val}' -> '{mapped}'")
                    else:
                        logger.warning(f"  [{node_id}] subject '{subject_val}' 无法映射，跳过")

                # === 迁移 cognitive_level ===
                cog_val = node.get("cognitive_level")
                if cog_val is not None:
                    cog_dict: Dict[str, Any] = {}

                    # 解析 JSON
                    if isinstance(cog_val, str):
                        try:
                            cog_dict = json.loads(cog_val)
                        except (json.JSONDecodeError, TypeError):
                            cog_dict = {}
                    elif isinstance(cog_val, dict):
                        cog_dict = cog_val

                    if cog_dict:
                        needs_migration = any(
                            k not in VALID_COG_KEYS for k in cog_dict.keys()
                        )
                        if needs_migration:
                            new_cog: Dict[str, Any] = {}
                            for k, v in cog_dict.items():
                                if k in VALID_COG_KEYS:
                                    new_cog[k] = v
                                elif k in COG_KEY_CN_TO_EN:
                                    new_cog[COG_KEY_CN_TO_EN[k]] = v
                                else:
                                    logger.warning(
                                        f"  [{node_id}] cognitive_level key '{k}' 无法映射，跳过"
                                    )
                            updates["cognitive_level"] = json.dumps(new_cog, ensure_ascii=False)
                            cog_migrated += 1
                            logger.info(
                                f"  [{node_id}] cognitive_level keys migrated: "
                                f"{list(cog_dict.keys())} -> {list(new_cog.keys())}"
                            )

                # 执行更新
                if updates:
                    set_clauses = ", ".join(f"n.{k} = ${k}" for k in updates.keys())
                    params = {"node_id": node_id, **updates}
                    await session.run(
                        f"MATCH (n:KnowledgeNode {{id: $node_id}}) SET {set_clauses}",
                        params,
                    )

        logger.info(
            f"\n迁移完成: 共 {total_nodes} 个节点, "
            f"subject 迁移 {subject_migrated} 个, "
            f"cognitive_level 迁移 {cog_migrated} 个"
        )

    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(migrate_seed_data())
