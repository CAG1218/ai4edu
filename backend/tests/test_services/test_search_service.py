"""全文检索核心排序、摘要与权限规则测试。"""

from types import SimpleNamespace

from app.services.search_service import SearchService


def test_note_summary_extracts_summary_and_keywords() -> None:
    service = SearchService()
    result = service.summarize_note(
        "梯度下降学习笔记",
        "梯度下降用于最小化损失函数。学习率决定每次参数更新的步长。学习率过大会导致震荡。",
    )

    assert result["summary"]
    assert len(result["summary"]) <= 220
    assert result["keywords"]


def test_database_keyword_search_boosts_title_matches() -> None:
    service = SearchService()
    documents = [
        {"id": "note:1", "score": 0, "type": "database", "highlight": {},
         "source": {"id": 1, "doc_type": "note", "title": "线性代数", "content": "矩阵基础"}},
        {"id": "note:2", "score": 0, "type": "database", "highlight": {},
         "source": {"id": 2, "doc_type": "note", "title": "复习记录", "content": "线性代数中的矩阵"}},
    ]

    results = service._database_keyword_search("线性代数", documents)

    assert [item["id"] for item in results] == ["note:1", "note:2"]
    assert "<mark>" in results[0]["highlight"]["title"][0]


def test_rrf_merges_chunks_into_one_document() -> None:
    service = SearchService()
    keyword = [{"id": "note:7", "type": "keyword", "source": {"id": 7, "doc_type": "note"}, "highlight": {}}]
    semantic = [
        {"id": "note:7:chunk:0", "type": "semantic", "source": {"id": 7, "doc_type": "note"}, "highlight": {}},
        {"id": "note:7:chunk:1", "type": "semantic", "source": {"id": 7, "doc_type": "note"}, "highlight": {}},
    ]

    results = service._rrf_fuse([keyword, semantic])

    assert len(results) == 1
    assert results[0]["id"] == "note:7"
    assert results[0]["matched_by"] == ["keyword", "semantic"]


def test_vector_metadata_visibility_respects_owner_and_course() -> None:
    user = SimpleNamespace(id=12)

    assert SearchService._metadata_visible({"doc_type": "note", "owner_id": 12}, user, set())
    assert not SearchService._metadata_visible({"doc_type": "note", "owner_id": 99}, user, set())
    assert SearchService._metadata_visible({"doc_type": "resource", "course_id": 3}, user, {3})
    assert not SearchService._metadata_visible({"doc_type": "resource", "course_id": 4}, user, {3})
