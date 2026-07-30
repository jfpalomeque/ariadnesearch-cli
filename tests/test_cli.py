from __future__ import annotations

import json

from ariadnesearch import cli
from ariadnesearch.semantic import CandidateRecord


def test_docs_prints_reference(capsys) -> None:
    exit_code = cli.main(["docs"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ariadnesearch search QUERY" in captured.out
    assert "--country" in captured.out
    assert "Candidate records include" in captured.out
    assert captured.err == ""


def test_build_search_output_serialises_candidates() -> None:
    candidate = CandidateRecord(
        id="abc",
        portal_url="https://portal.ariadne-infrastructure.eu/resource/abc",
        title="Radiocarbon date",
        countries=["England"],
        temporal_periods=["neolithic"],
        matched_terms=["radiocarbon"],
        raw={"id": "abc"},
    )

    output = cli.build_search_output(
        "radiocarbon",
        ["radiocarbon"],
        [candidate],
        country="England",
        page=2,
        size_per_term=10,
    )

    assert output == {
        "command": "search",
        "query": "radiocarbon",
        "expanded_terms": ["radiocarbon"],
        "filters": {"resource_type": None, "period": None, "country": "England"},
        "pagination": {"page": 2, "size_per_term": 10},
        "candidate_count": 1,
        "candidates": [
            {
                "id": "abc",
                "portal_url": "https://portal.ariadne-infrastructure.eu/resource/abc",
                "title": "Radiocarbon date",
                "description": None,
                "resource_type": None,
                "source_identifier": None,
                "countries": ["England"],
                "temporal_periods": ["neolithic"],
                "matched_terms": ["radiocarbon"],
                "raw": {"id": "abc"},
            }
        ],
    }


def test_search_prints_json_without_live_network(monkeypatch, capsys) -> None:
    calls = []

    class FakeClient:
        pass

    def fake_semantic_search(
        client,
        terms,
        size_per_term=10,
        page=1,
        resource_type=None,
        period=None,
        country=None,
    ):
        calls.append((client, terms, size_per_term, page, resource_type, period, country))
        return [
            CandidateRecord(
                id="abc",
                portal_url="https://portal.ariadne-infrastructure.eu/resource/abc",
                matched_terms=["radiocarbon"],
            )
        ]

    monkeypatch.setattr(cli, "AriadneClient", FakeClient)
    monkeypatch.setattr(cli, "semantic_search", fake_semantic_search)

    exit_code = cli.main(
        [
            "search",
            "radiocarbon",
            "--expand",
            "C14",
            "--country",
            "England",
            "--period",
            "neolithic",
            "--resource-type",
            "Date",
            "--size",
            "3",
            "--page",
            "2",
        ]
    )

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert exit_code == 0
    assert data["command"] == "search"
    assert data["query"] == "radiocarbon"
    assert data["expanded_terms"] == ["radiocarbon", "C14"]
    assert data["filters"] == {
        "resource_type": "Date",
        "period": "neolithic",
        "country": "England",
    }
    assert data["pagination"] == {"page": 2, "size_per_term": 3}
    assert data["candidate_count"] == 1
    assert captured.err == ""
    assert calls == [
        (
            calls[0][0],
            ["radiocarbon", "C14"],
            3,
            2,
            "Date",
            "neolithic",
            "England",
        )
    ]


def test_search_errors_go_to_stderr(monkeypatch, capsys) -> None:
    class FakeClient:
        pass

    def fake_semantic_search(*args, **kwargs):
        raise ValueError("page must be at least 1")

    monkeypatch.setattr(cli, "AriadneClient", FakeClient)
    monkeypatch.setattr(cli, "semantic_search", fake_semantic_search)

    exit_code = cli.main(["search", "radiocarbon"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "error: page must be at least 1\n"
