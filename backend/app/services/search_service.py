"""全文检索服务：数据库多源召回、Elasticsearch 关键词检索和 Chroma 语义检索。"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

import httpx
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.course import Course, CourseEnrollment
from app.models.note import Note
from app.models.resource import Resource
from app.models.user import User
from app.services.rag.embedder import Embedder

logger = logging.getLogger(__name__)

SEARCH_TYPES = {"note", "resource", "course", "graph_node"}
STOP_WORDS = {
    "的", "了", "和", "是", "在", "与", "及", "或", "一个", "一种", "我们", "你们",
    "this", "that", "with", "from", "the", "and", "for", "are", "was",
}


class SearchService:
    """提供带权限过滤的混合全文检索。"""

    def __init__(self) -> None:
        self.es_host = settings.ELASTICSEARCH_HOST.rstrip("/")
        self.embedder = Embedder()
        self._chroma_collection = None

    async def _es_request(self, method: str, path: str, json_data: Optional[Dict] = None) -> Dict:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.request(method, f"{self.es_host}/{path}", json=json_data)
            response.raise_for_status()
            return response.json()

    async def _get_chroma_collection(self):
        if self._chroma_collection is None:
            try:
                import chromadb

                client = chromadb.Client()
                self._chroma_collection = client.get_or_create_collection(
                    name="ai4edu_vectors", metadata={"hnsw:space": "cosine"}
                )
            except Exception as exc:
                logger.warning("ChromaDB 不可用: %s", exc)
        return self._chroma_collection

    @staticmethod
    def canonical_id(doc_type: str, doc_id: Any) -> str:
        value = str(doc_id)
        return value if value.startswith(f"{doc_type}:") else f"{doc_type}:{value}"

    @staticmethod
    def _source_type(item: Dict[str, Any]) -> str:
        source = item.get("source", {})
        return str(source.get("doc_type") or source.get("type") or "")

    @staticmethod
    def _plain_text(value: Optional[str]) -> str:
        text = re.sub(r"<[^>]+>", " ", value or "")
        text = re.sub(r"[`#>*_~\[\]()]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def summarize_note(self, title: str, content: Optional[str], max_length: int = 220) -> Dict[str, Any]:
        """生成无需外部 AI 服务也可稳定工作的抽取式摘要和主题词。"""
        plain = self._plain_text(content)
        tokens = re.findall(r"[\u4e00-\u9fff]{2,6}|[A-Za-z][A-Za-z0-9_-]{2,}", f"{title} {plain}".lower())
        counts = Counter(token for token in tokens if token not in STOP_WORDS)
        keywords = [word for word, _ in counts.most_common(8)]

        sentences = [part.strip() for part in re.split(r"(?<=[。！？!?；;])|\n+", plain) if part.strip()]
        if not sentences:
            summary = plain[:max_length]
        else:
            scored = []
            for position, sentence in enumerate(sentences[:80]):
                keyword_score = sum(counts.get(word, 0) for word in set(tokens) if word in sentence.lower())
                scored.append((keyword_score + 1 / (position + 1), position, sentence))
            selected = sorted(sorted(scored, reverse=True)[:3], key=lambda row: row[1])
            summary = "".join(row[2] for row in selected)[:max_length]

        return {"summary": summary, "keywords": keywords}

    async def _accessible_course_ids(self, db: AsyncSession, user: User) -> Set[int]:
        if user.role == "super_admin":
            stmt = select(Course.id).where(
                Course.tenant_id == (user.tenant_id or 0), Course.is_active.is_(True)
            )
        elif user.role == "teacher":
            stmt = select(Course.id).where(
                Course.tenant_id == (user.tenant_id or 0), Course.teacher_id == user.id, Course.is_active.is_(True)
            )
        else:
            stmt = (
                select(CourseEnrollment.course_id)
                .join(Course, Course.id == CourseEnrollment.course_id)
                .where(
                    Course.tenant_id == (user.tenant_id or 0),
                    CourseEnrollment.user_id == user.id,
                    CourseEnrollment.dropped_at.is_(None),
                    Course.is_active.is_(True),
                )
            )
        return set((await db.execute(stmt)).scalars().all())

    async def _load_accessible_documents(
        self,
        db: AsyncSession,
        user: User,
        search_types: Set[str],
        date_from: Optional[datetime],
    ) -> List[Dict[str, Any]]:
        """从主数据库加载可见文档，同时作为搜索基础设施不可用时的降级数据源。"""
        tenant_id = user.tenant_id or 0
        course_ids = await self._accessible_course_ids(db, user)
        documents: List[Dict[str, Any]] = []

        if "note" in search_types:
            conditions = [Note.tenant_id == tenant_id, Note.owner_id == user.id, Note.is_deleted.is_(False)]
            if date_from:
                conditions.append(Note.updated_at >= date_from)
            notes = (await db.execute(select(Note).where(and_(*conditions)))).scalars().all()
            for note in notes:
                smart = self.summarize_note(note.title, note.content_plain or note.content)
                documents.append({
                    "id": self.canonical_id("note", note.id),
                    "score": 0.0,
                    "type": "database",
                    "source": {
                        "id": note.id, "doc_type": "note", "title": note.title,
                        "content": note.content_plain or self._plain_text(note.content),
                        "summary": smart["summary"], "keywords": smart["keywords"],
                        "tags": self._json_list(note.tags), "owner_id": note.owner_id,
                        "tenant_id": note.tenant_id, "course_id": note.course_id,
                        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
                    },
                    "highlight": {},
                })

        if "resource" in search_types:
            visibility = or_(Resource.is_public.is_(True), Resource.uploader_id == user.id)
            if course_ids:
                visibility = or_(visibility, Resource.course_id.in_(course_ids))
            conditions = [
                Resource.tenant_id == tenant_id, Resource.is_active.is_(True), Resource.deleted_at.is_(None), visibility
            ]
            if date_from:
                conditions.append(Resource.updated_at >= date_from)
            resources = (await db.execute(select(Resource).where(and_(*conditions)))).scalars().all()
            for resource in resources:
                metadata = self._json_dict(resource.metadata_json)
                documents.append({
                    "id": self.canonical_id("resource", resource.id),
                    "score": 0.0, "type": "database",
                    "source": {
                        "id": resource.id, "doc_type": "resource", "title": resource.title,
                        "content": metadata.get("parsed_text_preview", ""),
                        "description": resource.description or "", "summary": metadata.get("ai_summary", ""),
                        "tags": self._json_list(resource.tags), "resource_type": resource.resource_type,
                        "uploader_id": resource.uploader_id, "tenant_id": resource.tenant_id,
                        "course_id": resource.course_id, "is_public": resource.is_public,
                        "updated_at": resource.updated_at.isoformat() if resource.updated_at else None,
                    },
                    "highlight": {},
                })

        if "course" in search_types and course_ids:
            conditions = [Course.id.in_(course_ids), Course.tenant_id == tenant_id, Course.is_active.is_(True)]
            if date_from:
                conditions.append(Course.updated_at >= date_from)
            courses = (await db.execute(select(Course).where(and_(*conditions)))).scalars().all()
            for course in courses:
                documents.append({
                    "id": self.canonical_id("course", course.id), "score": 0.0, "type": "database",
                    "source": {
                        "id": course.id, "doc_type": "course", "title": course.name,
                        "description": course.description or "", "subject": course.subject,
                        "teacher_id": course.teacher_id, "tenant_id": course.tenant_id,
                        "course_id": course.id,
                        "updated_at": course.updated_at.isoformat() if course.updated_at else None,
                    },
                    "highlight": {},
                })
        return documents

    @staticmethod
    def _json_list(value: Optional[str]) -> List[Any]:
        try:
            parsed = json.loads(value or "[]")
            return parsed if isinstance(parsed, list) else []
        except (TypeError, json.JSONDecodeError):
            return []

    @staticmethod
    def _json_dict(value: Optional[str]) -> Dict[str, Any]:
        try:
            parsed = json.loads(value or "{}")
            return parsed if isinstance(parsed, dict) else {}
        except (TypeError, json.JSONDecodeError):
            return {}

    def _database_keyword_search(self, query: str, documents: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        terms = [term.lower() for term in re.findall(r"[\w\u4e00-\u9fff]+", query) if term.strip()]
        results = []
        for item in documents:
            source = item["source"]
            fields = {
                "title": str(source.get("title", "")), "summary": str(source.get("summary", "")),
                "content": str(source.get("content", "")), "description": str(source.get("description", "")),
                "tags": " ".join(map(str, source.get("tags", []))),
            }
            score = sum(
                fields["title"].lower().count(term) * 5
                + fields["summary"].lower().count(term) * 3
                + fields["content"].lower().count(term) * 2
                + fields["description"].lower().count(term) * 2
                + fields["tags"].lower().count(term) * 2.5
                for term in terms
            )
            if score <= 0:
                continue
            result = {**item, "score": float(score), "type": "keyword"}
            result["highlight"] = self._local_highlight(fields, terms)
            results.append(result)
        return sorted(results, key=lambda row: row["score"], reverse=True)

    @staticmethod
    def _local_highlight(fields: Dict[str, str], terms: Sequence[str]) -> Dict[str, List[str]]:
        highlights: Dict[str, List[str]] = {}
        for name in ("title", "summary", "content", "description"):
            value = fields[name]
            if not value or not any(term in value.lower() for term in terms):
                continue
            safe = value[:260]
            for term in sorted(terms, key=len, reverse=True):
                safe = re.sub(re.escape(term), lambda m: f"<mark>{m.group(0)}</mark>", safe, flags=re.I)
            highlights[name] = [safe]
        return highlights

    async def _bm25_search(
        self, query: str, search_types: Set[str], user: User, course_ids: Set[int], limit: int
    ) -> List[Dict[str, Any]]:
        tenant_id = user.tenant_id or 0
        should_visibility: List[Dict[str, Any]] = [
            {"bool": {"must": [{"term": {"doc_type": "note"}}, {"term": {"owner_id": user.id}}]}},
            {"bool": {"must": [{"term": {"doc_type": "resource"}}], "should": [
                {"term": {"is_public": True}}, {"term": {"uploader_id": user.id}},
                *([{"terms": {"course_id": sorted(course_ids)}}] if course_ids else []),
            ], "minimum_should_match": 1}},
        ]
        if course_ids:
            should_visibility.extend([
                {"bool": {"must": [{"term": {"doc_type": "course"}}, {"terms": {"course_id": sorted(course_ids)}}]}},
                {"bool": {"must": [{"term": {"doc_type": "graph_node"}}, {"terms": {"course_id": sorted(course_ids)}}]}},
            ])
        body = {
            "size": limit,
            "query": {"bool": {
                "must": [{"multi_match": {"query": query, "fields": ["title^5", "summary^3", "content^2", "description^2", "tags"], "type": "best_fields", "fuzziness": "AUTO"}}],
                "filter": [{"term": {"tenant_id": tenant_id}}, {"terms": {"doc_type": sorted(search_types)}}],
                "should": should_visibility, "minimum_should_match": 1,
            }},
            "highlight": {"pre_tags": ["<mark>"], "post_tags": ["</mark>"], "fields": {
                "title": {}, "summary": {"fragment_size": 180}, "content": {"fragment_size": 220, "number_of_fragments": 2}, "description": {"fragment_size": 180}
            }},
        }
        try:
            result = await self._es_request("POST", "ai4edu/_search", body)
            return [{"id": hit["_id"], "score": hit.get("_score", 0), "source": hit.get("_source", {}),
                     "highlight": hit.get("highlight", {}), "type": "keyword"}
                    for hit in result.get("hits", {}).get("hits", [])]
        except Exception as exc:
            logger.info("Elasticsearch 不可用，使用数据库关键词检索: %s", exc)
            return []

    async def _vector_search(
        self, query: str, search_types: Set[str], user: User, course_ids: Set[int], limit: int
    ) -> List[Dict[str, Any]]:
        collection = await self._get_chroma_collection()
        if collection is None:
            return []
        try:
            embedding = await self.embedder.embed_query(query)
            results = collection.query(query_embeddings=[embedding], n_results=limit, include=["documents", "metadatas", "distances"])
            items = []
            for index, chunk_id in enumerate((results.get("ids") or [[]])[0]):
                metadata = ((results.get("metadatas") or [[]])[0][index] or {})
                doc_type = str(metadata.get("doc_type", ""))
                if doc_type not in search_types or int(metadata.get("tenant_id", -1)) != (user.tenant_id or 0):
                    continue
                if not self._metadata_visible(metadata, user, course_ids):
                    continue
                source = dict(metadata)
                source["content"] = (results.get("documents") or [[]])[0][index]
                distance = (results.get("distances") or [[]])[0][index]
                items.append({"id": metadata.get("document_id", chunk_id), "score": max(0.0, 1 - distance),
                              "source": source, "highlight": {}, "type": "semantic"})
            return items
        except Exception as exc:
            logger.info("语义检索不可用: %s", exc)
            return []

    @staticmethod
    def _metadata_visible(metadata: Dict[str, Any], user: User, course_ids: Set[int]) -> bool:
        doc_type = metadata.get("doc_type")
        if doc_type == "note":
            return int(metadata.get("owner_id", -1)) == user.id
        if bool(metadata.get("is_public")) or int(metadata.get("uploader_id", -1)) == user.id:
            return True
        try:
            return int(metadata.get("course_id", -1)) in course_ids
        except (TypeError, ValueError):
            return False

    def _rrf_fuse(self, result_lists: Iterable[Sequence[Dict[str, Any]]], k: int = 60) -> List[Dict[str, Any]]:
        scores: Dict[str, float] = {}
        info: Dict[str, Dict[str, Any]] = {}
        channels: Dict[str, Set[str]] = {}
        for result_list in result_lists:
            seen: Set[str] = set()
            for rank, item in enumerate(result_list, 1):
                doc_type = self._source_type(item)
                raw_id = item.get("source", {}).get("id") or item["id"]
                doc_id = self.canonical_id(doc_type, raw_id) if doc_type else str(item["id"])
                if doc_id in seen:
                    continue
                seen.add(doc_id)
                scores[doc_id] = scores.get(doc_id, 0.0) + 1 / (k + rank)
                channels.setdefault(doc_id, set()).add(str(item.get("type", "unknown")))
                current = info.get(doc_id)
                if current is None or len(item.get("highlight", {})) > len(current.get("highlight", {})):
                    info[doc_id] = {**item, "id": doc_id}
        fused = []
        for doc_id in sorted(scores, key=scores.get, reverse=True):
            item = dict(info[doc_id])
            item["rrf_score"] = round(scores[doc_id], 6)
            item["matched_by"] = sorted(channels[doc_id])
            fused.append(item)
        return fused

    async def hybrid_search(
        self, query: str, db: AsyncSession, user: User, search_type: str = "all", search_mode: str = "hybrid",
        sources: Optional[Sequence[str]] = None, date_range: Optional[str] = None, page: int = 1, page_size: int = 20,
    ) -> Dict[str, Any]:
        selected = set(sources or ([] if search_type == "all" else [search_type])) or set(SEARCH_TYPES)
        selected &= SEARCH_TYPES
        date_from = self._date_from_range(date_range)
        course_ids = await self._accessible_course_ids(db, user)
        documents = await self._load_accessible_documents(db, user, selected, date_from)
        accessible_ids = {str(item["id"]) for item in documents}
        local_keyword = self._database_keyword_search(query, documents)

        keyword_task = self._bm25_search(query, selected, user, course_ids, page_size * 5)
        semantic_task = self._vector_search(query, selected, user, course_ids, page_size * 5)
        es_keyword, semantic = await asyncio.gather(keyword_task, semantic_task)
        # 主数据库是权限事实源，防止外部索引因异步更新而短暂返回已撤权内容。
        es_keyword = [item for item in es_keyword if self._externally_visible(item, accessible_ids, user, course_ids)]
        semantic = [item for item in semantic if self._externally_visible(item, accessible_ids, user, course_ids)]
        if date_from:
            es_keyword = [item for item in es_keyword if self._within_date(item, date_from)]
            semantic = [item for item in semantic if self._within_date(item, date_from)]
        keyword = self._deduplicate([*es_keyword, *local_keyword])
        lists = [keyword] if search_mode == "keyword" else [semantic] if search_mode == "semantic" else [keyword, semantic]
        fused = self._rrf_fuse(lists)
        offset = (page - 1) * page_size
        return {
            "query": query, "total": len(fused), "page": page, "page_size": page_size,
            "keyword_count": len(keyword), "semantic_count": len(semantic),
            "sources": sorted(selected), "mode": search_mode, "results": fused[offset:offset + page_size],
        }

    async def index_search(
        self,
        query: str,
        tenant_id: int,
        user_id: int,
        course_ids: Optional[Sequence[int]] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """供 RAG 智能体使用的受限索引检索（不绕过租户与用户权限）。"""
        from types import SimpleNamespace

        user = SimpleNamespace(id=user_id, tenant_id=tenant_id, role="student")
        allowed_courses = set(course_ids or [])
        keyword, semantic = await asyncio.gather(
            self._bm25_search(query, SEARCH_TYPES, user, allowed_courses, limit * 3),
            self._vector_search(query, SEARCH_TYPES, user, allowed_courses, limit * 3),
        )
        fused = self._rrf_fuse([keyword, semantic])[:limit]
        return {"query": query, "total": len(fused), "results": fused}

    @staticmethod
    def _date_from_range(date_range: Optional[str]) -> Optional[datetime]:
        days = {"1d": 1, "7d": 7, "30d": 30, "365d": 365}.get(date_range or "")
        return datetime.utcnow() - timedelta(days=days) if days else None

    @staticmethod
    def _within_date(item: Dict[str, Any], date_from: datetime) -> bool:
        value = item.get("source", {}).get("updated_at")
        if not value:
            return False
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None) >= date_from
        except (TypeError, ValueError):
            return False

    def _externally_visible(
        self, item: Dict[str, Any], accessible_ids: Set[str], user: User, course_ids: Set[int]
    ) -> bool:
        source = item.get("source", {})
        doc_type = self._source_type(item)
        if doc_type == "graph_node":
            try:
                return (
                    int(source.get("tenant_id", -1)) == (user.tenant_id or 0)
                    and int(source.get("course_id", -1)) in course_ids
                )
            except (TypeError, ValueError):
                return False
        raw_id = source.get("id") or item.get("id")
        return self.canonical_id(doc_type, raw_id) in accessible_ids if doc_type else False

    def _deduplicate(self, items: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        for item in items:
            doc_type = self._source_type(item)
            raw_id = item.get("source", {}).get("id") or item["id"]
            doc_id = self.canonical_id(doc_type, raw_id) if doc_type else str(item["id"])
            current = result.get(doc_id)
            if current is None or item.get("score", 0) > current.get("score", 0):
                result[doc_id] = {**item, "id": doc_id}
        return sorted(result.values(), key=lambda row: row.get("score", 0), reverse=True)

    async def suggest(self, prefix: str, db: AsyncSession, user: User, limit: int = 10) -> List[str]:
        documents = await self._load_accessible_documents(db, user, SEARCH_TYPES - {"graph_node"}, None)
        prefix_lower = prefix.lower()
        titles = [str(item["source"].get("title", "")) for item in documents]
        return [title for title in titles if prefix_lower in title.lower()][:limit]

    async def get_hot_searches(self, limit: int = 10) -> List[str]:
        try:
            result = await self._es_request("POST", "ai4edu_search_logs/_search", {
                "size": 0, "aggs": {"hot_keywords": {"terms": {"field": "query_keyword.keyword", "size": limit}}}
            })
            return [bucket["key"] for bucket in result.get("aggregations", {}).get("hot_keywords", {}).get("buckets", [])]
        except Exception:
            return ["高等数学", "牛顿定律", "数据结构", "线性代数", "概率论"][:limit]

    async def index_document(self, doc_id: str, doc_data: Dict[str, Any]) -> bool:
        doc_type = str(doc_data.get("doc_type", "resource"))
        canonical = self.canonical_id(doc_type, doc_id)
        payload = {**doc_data, "id": doc_data.get("id", doc_id), "document_id": canonical}
        es_ok = False
        chroma_ok = False
        try:
            await self._es_request("PUT", f"ai4edu/_doc/{canonical}", payload)
            es_ok = True
        except Exception as exc:
            logger.warning("Elasticsearch 索引失败: %s", exc)

        try:
            collection = await self._get_chroma_collection()
            if collection is not None:
                collection.delete(where={"document_id": canonical})
                text = " ".join(str(payload.get(key, "")) for key in ("title", "summary", "content", "description"))
                chunks = self.embedder.chunk_text(text)
                if chunks:
                    embeddings = await self.embedder.embed_batch(chunks)
                    ids = [f"{canonical}:chunk:{index}" for index in range(len(chunks))]
                    metadata = self._chroma_metadata(payload, canonical)
                    collection.upsert(ids=ids, embeddings=embeddings, documents=chunks,
                                      metadatas=[{**metadata, "chunk_index": index} for index in range(len(chunks))])
                    chroma_ok = True
        except Exception as exc:
            logger.warning("Chroma 索引失败: %s", exc)
        return es_ok or chroma_ok

    @staticmethod
    def _chroma_metadata(payload: Dict[str, Any], canonical: str) -> Dict[str, Any]:
        allowed = ("id", "doc_type", "title", "summary", "tenant_id", "owner_id", "uploader_id", "course_id", "is_public", "updated_at")
        metadata = {key: payload[key] for key in allowed if payload.get(key) is not None and isinstance(payload[key], (str, int, float, bool))}
        metadata["document_id"] = canonical
        return metadata

    async def index_note(self, note_data: Dict[str, Any]) -> bool:
        smart = self.summarize_note(note_data.get("title", ""), note_data.get("content_plain") or note_data.get("content"))
        return await self.index_document(str(note_data["id"]), {
            "id": note_data["id"], "doc_type": "note", "title": note_data.get("title", ""),
            "content": note_data.get("content_plain") or self._plain_text(note_data.get("content")),
            "summary": smart["summary"], "keywords": smart["keywords"], "tags": note_data.get("tags", []),
            "tenant_id": note_data.get("tenant_id"), "owner_id": note_data.get("owner_id"),
            "course_id": note_data.get("course_id"), "updated_at": note_data.get("updated_at"),
        })

    async def delete_document(self, doc_type: str, doc_id: Any) -> None:
        canonical = self.canonical_id(doc_type, doc_id)
        try:
            await self._es_request("DELETE", f"ai4edu/_doc/{canonical}")
        except Exception:
            pass
        try:
            collection = await self._get_chroma_collection()
            if collection is not None:
                collection.delete(where={"document_id": canonical})
        except Exception:
            pass

    async def index_node(self, node_id: str, node_data: Dict[str, Any]) -> bool:
        return await self.index_document(node_id, {**node_data, "doc_type": "graph_node"})


search_service = SearchService()
