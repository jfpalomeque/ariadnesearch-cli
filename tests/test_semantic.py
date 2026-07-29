from __future__ import annotations

import pytest

from archsearch.ariadne import SearchResponse
from archsearch.semantic import semantic_search


class FakeClient:
    def __init__(self, responses: dict[str, list[dict]]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, int, int, str | None, str | None, str | None]] = []

    def search(
        self,
        query: str,
        size: int = 10,
        page: int = 1,
        resource_type: str | None = None,
        period: str | None = None,
        country: str | None = None,
    ) -> SearchResponse:
        self.calls.append((query, size, page, resource_type, period, country))
        hits = self.responses.get(query, [])
        return SearchResponse(total={"value": len(hits), "relation": "eq"}, hits=hits)


def test_semantic_search_runs_one_search_per_non_empty_term() -> None:
    client = FakeClient({"radiocarbon": [], "C14": []})

    semantic_search(client, ["radiocarbon", "", " C14 "], size_per_term=3)

    assert client.calls == [
        ("radiocarbon", 3, 1, None, None, None),
        ("C14", 3, 1, None, None, None),
    ]


def test_semantic_search_passes_page_to_each_term() -> None:
    client = FakeClient({"radiocarbon": [], "C14": []})

    semantic_search(client, ["radiocarbon", "C14"], size_per_term=5, page=3)

    assert client.calls == [
        ("radiocarbon", 5, 3, None, None, None),
        ("C14", 5, 3, None, None, None),
    ]


def test_semantic_search_passes_resource_type_to_each_term() -> None:
    client = FakeClient({"radiocarbon": [], "C14": []})

    semantic_search(
        client,
        ["radiocarbon", "C14"],
        size_per_term=3,
        resource_type="Date",
    )

    assert client.calls == [
        ("radiocarbon", 3, 1, "Date", None, None),
        ("C14", 3, 1, "Date", None, None),
    ]


def test_semantic_search_passes_period_to_each_term() -> None:
    client = FakeClient({"radiocarbon": [], "C14": []})

    semantic_search(
        client,
        ["radiocarbon", "C14"],
        size_per_term=3,
        period="neolithic",
    )

    assert client.calls == [
        ("radiocarbon", 3, 1, None, "neolithic", None),
        ("C14", 3, 1, None, "neolithic", None),
    ]


def test_semantic_search_passes_country_to_each_term() -> None:
    client = FakeClient({"radiocarbon": [], "C14": []})

    semantic_search(
        client,
        ["radiocarbon", "C14"],
        size_per_term=3,
        country="England",
    )

    assert client.calls == [
        ("radiocarbon", 3, 1, None, None, "England"),
        ("C14", 3, 1, None, None, "England"),
    ]


def test_semantic_search_deduplicates_and_records_matched_terms() -> None:
    shared_hit = {
        "id": "abc",
        "data": {
            "title": {"text": "Radiocarbon date"},
            "description": {"text": "A sample description"},
            "resourceType": "dataset",
            "identifier": "https://example.test/resource/abc",
        },
    }
    client = FakeClient({"radiocarbon": [shared_hit], "C14": [shared_hit]})

    candidates = semantic_search(client, ["radiocarbon", "C14"], size_per_term=5)

    assert len(candidates) == 1
    assert candidates[0].id == "abc"
    assert candidates[0].portal_url == "https://portal.ariadne-infrastructure.eu/resource/abc"
    assert candidates[0].matched_terms == ["radiocarbon", "C14"]


def test_semantic_search_extracts_stable_fields_and_preserves_raw() -> None:
    hit = {
        "id": "abc",
        "data": {
            "title": {"text": "A title"},
            "description": {"text": "A description"},
            "resourceType": "collection",
            "identifier": "https://example.test/source",
            "extra": {"kept": True},
        },
    }
    client = FakeClient({"radiocarbon": [hit]})

    [candidate] = semantic_search(client, ["radiocarbon"])

    assert candidate.title == "A title"
    assert candidate.portal_url == "https://portal.ariadne-infrastructure.eu/resource/abc"
    assert candidate.description == "A description"
    assert candidate.resource_type == "collection"
    assert candidate.source_identifier == "https://example.test/source"
    assert candidate.raw == hit


def test_semantic_search_skips_hits_without_id() -> None:
    client = FakeClient({"radiocarbon": [{"data": {"title": {"text": "No id"}}}]})

    assert semantic_search(client, ["radiocarbon"]) == []


def test_semantic_search_requires_at_least_one_non_empty_term() -> None:
    client = FakeClient({})

    with pytest.raises(ValueError, match="at least one"):
        semantic_search(client, ["", "  "])


def test_semantic_search_rejects_page_less_than_one() -> None:
    client = FakeClient({})

    with pytest.raises(ValueError, match="page must be at least 1"):
        semantic_search(client, ["radiocarbon"], page=0)
