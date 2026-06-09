"""
AI4Edu 全文检索 Service
混合检索：BM25(ES) + 向量(Chroma) + RRF 融合排序
"""
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings
from app.services.rag.embedder import Embedder

logger = logging.getLogger(__name__)


class SearchService:
    """全文检索服务"""

    def __init__(self):
        self.es_host = settings.ELASTICSEARCH_HOST
        self.embedder = Embedder()
        self._chroma_collection = None

    # ==================== ES 操作 ====================

    async def _es_request(
        self, method: str, path: str, json_data: Optional[Dict] = None
    ) -> Dict:
        """向 Elasticsearch 发送 HTTP 请求"""
        url = f"{self.es_host}/{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, json=json_data)
            response.raise_for_status()
            return response.json()

    async def _es_search(self, index: str, body: Dict) -> Dict:
        """执行 ES 搜索"""
        return await self._es_request("POST", f"{index}/_search", body)

    # ==================== Chroma 操作 ====================

    async def _get_chroma_collection(self):
        """获取 Chroma 向量集合（懒加载）"""
        if self._chroma_collection is None:
            try:
                import chromadb
                client = chromadb.Client()
                self._chroma_collection = client.get_or_create_collection(
                    name="ai4edu_vectors",
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as e:
                logger.warning(f"ChromaDB 不可用: {e}")
                self._chroma_collection = None
        return self._chroma_collection

    # ==================== BM25 检索 ====================

    async def _bm25_search(
        self, query: str, index: str = "ai4edu", limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        BM25 全文检索（通过 ES httpx 调用）
        """
        body = {
            "size": limit,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content^2", "description", "tags"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            },
            "highlight": {
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
                "fields": {
                    "title": {},
                    "content": {"fragment_size": 200, "number_of_fragments": 3},
                    "description": {"fragment_size": 150},
                },
            },
        }

        try:
            result = await self._es_search(index, body)
            hits = result.get("hits", {}).get("hits", [])
            return [
                {
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "source": hit["_source"],
                    "highlight": hit.get("highlight", {}),
                    "type": "bm25",
                }
                for hit in hits
            ]
        except Exception as e:
            logger.error(f"BM25 搜索失败: {e}")
            return []

    # ==================== 向量检索 ====================

    async def _vector_search(
        self, query: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        向量检索（Chroma SDK）
        """
        collection = await self._get_chroma_collection()
        if collection is None:
            return []

        try:
            query_embedding = await self.embedder.embed_query(query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )

            items = []
            if results and results["ids"] and results["ids"][0]:
                for i, doc_id in enumerate(results["ids"][0]):
                    items.append(
                        {
                            "id": doc_id,
                            "score": 1 - results["distances"][0][i],  # cosine distance -> similarity
                            "source": results["metadatas"][0][i] if results["metadatas"] else {},
                            "content": results["documents"][0][i] if results["documents"] else "",
                            "type": "vector",
                        }
                    )
            return items
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []

    # ==================== RRF 融合 ====================

    def _rrf_fuse(
        self,
        result_lists: List[List[Dict[str, Any]]],
        k: int = 60,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) 融合排序

        RRF(d) = Σ 1/(k + rank_i(d))

        Args:
            result_lists: 多个排序列表
            k: RRF 参数（默认60）
            limit: 返回数量
        """
        rrf_scores: Dict[str, float] = {}
        doc_info: Dict[str, Dict[str, Any]] = {}

        for result_list in result_lists:
            for rank, item in enumerate(result_list, start=1):
                doc_id = item["id"]
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = 0.0
                    doc_info[doc_id] = item
                rrf_scores[doc_id] += 1.0 / (k + rank)

        # 按 RRF 分数排序
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        results = []
        for doc_id in sorted_ids[:limit]:
            item = doc_info[doc_id].copy()
            item["rrf_score"] = round(rrf_scores[doc_id], 6)
            results.append(item)

        return results

    # ==================== 混合检索 ====================

    async def hybrid_search(
        self,
        query: str,
        search_type: str = "all",
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        混合检索：BM25 + 向量 + RRF 融合
        """
        # 并行执行 BM25 和向量检索
        import asyncio
        bm25_task = self._bm25_search(query, limit=limit * 2)
        vector_task = self._vector_search(query, limit=limit * 2)
        bm25_results, vector_results = await asyncio.gather(
            bm25_task, vector_task, return_exceptions=True
        )
        # 处理异常结果
        if isinstance(bm25_results, Exception):
            logger.error(f"BM25 搜索异常: {bm25_results}")
            bm25_results = []
        if isinstance(vector_results, Exception):
            logger.error(f"向量搜索异常: {vector_results}")
            vector_results = []

        # 按类型过滤
        if search_type != "all":
            bm25_results = [
                r for r in bm25_results
                if r.get("source", {}).get("doc_type") == search_type
                or r.get("source", {}).get("type") == search_type
            ]

        # RRF 融合
        fused_results = self._rrf_fuse(
            [bm25_results, vector_results],
            limit=limit,
        )

        # 合并高亮信息
        bm25_highlight_map = {r["id"]: r.get("highlight", {}) for r in bm25_results}
        for item in fused_results:
            item["highlight"] = bm25_highlight_map.get(item["id"], {})

        return {
            "query": query,
            "total": len(fused_results),
            "bm25_count": len(bm25_results),
            "vector_count": len(vector_results),
            "results": fused_results,
        }

    # ==================== 建议和热门 ====================

    async def suggest(self, prefix: str, limit: int = 10) -> List[str]:
        """
        搜索前缀建议（ES completion suggester）
        """
        body = {
            "size": 0,
            "suggest": {
                "title-suggest": {
                    "prefix": prefix,
                    "completion": {
                        "field": "title.suggest",
                        "size": limit,
                        "skip_duplicates": True,
                    },
                }
            },
        }

        try:
            result = await self._es_request("POST", "ai4edu/_search", body)
            options = (
                result.get("suggest", {})
                .get("title-suggest", [{}])[0]
                .get("options", [])
            )
            return [opt["text"] for opt in options]
        except Exception as e:
            logger.error(f"搜索建议失败: {e}")
            return []

    async def get_hot_searches(self, limit: int = 10) -> List[str]:
        """
        获取热门搜索关键词
        基于 ES 聚合搜索日志
        """
        body = {
            "size": 0,
            "aggs": {
                "hot_keywords": {
                    "terms": {
                        "field": "query_keyword.keyword",
                        "size": limit,
                    }
                }
            },
        }

        try:
            result = await self._es_request("POST", "ai4edu_search_logs/_search", body)
            buckets = result.get("aggregations", {}).get("hot_keywords", {}).get("buckets", [])
            return [bucket["key"] for bucket in buckets]
        except Exception as e:
            logger.error(f"获取热门搜索失败: {e}")
            # 回退默认
            return ["高等数学", "牛顿定律", "数据结构", "线性代数", "概率论"]

    # ==================== 索引操作 ====================

    async def index_document(self, doc_id: str, doc_data: Dict[str, Any]) -> bool:
        """
        手动索引文档到 ES + Chroma
        """
        # 索引到 ES
        try:
            await self._es_request("PUT", f"ai4edu/_doc/{doc_id}", doc_data)
        except Exception as e:
            logger.error(f"ES 索引失败: {e}")

        # 向量索引到 Chroma
        try:
            collection = await self._get_chroma_collection()
            if collection is not None:
                text = f"{doc_data.get('title', '')} {doc_data.get('content', '')} {doc_data.get('description', '')}"
                chunks = await self.embedder.chunk_text(text)
                if chunks:
                    embeddings = await self.embedder.embed_batch(chunks)
                    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
                    metadatas = [
                        {
                            "doc_id": doc_id,
                            "doc_type": doc_data.get("doc_type", "resource"),
                            "chunk_index": i,
                        }
                        for i in range(len(chunks))
                    ]
                    collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        documents=chunks,
                        metadatas=metadatas,
                    )
        except Exception as e:
            logger.error(f"Chroma 索引失败: {e}")

        return True

    async def index_node(self, node_id: str, node_data: Dict[str, Any]) -> bool:
        """
        索引知识节点
        """
        doc_data = {
            **node_data,
            "doc_type": "graph_node",
        }
        return await self.index_document(node_id, doc_data)


# 全局单例
search_service = SearchService()
