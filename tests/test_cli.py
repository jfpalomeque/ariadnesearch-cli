from __future__ import annotations

import json

import httpx
import pytest

from ariadnesearch import cli
from ariadnesearch.ariadne import AriadneClient
from ariadnesearch.semantic import CandidateRecord, SearchResults, TermTotal


def test_docs_prints_reference(capsys) -> None:
    exit_code = cli.main(["docs"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ariadnesearch search QUERY" in captured.out
    assert "--country" in captured.out
    assert "Candidate records include" in captured.out
    assert "ariadnesearch get RECORD_ID" in captured.out
    assert "reversed longitudes" in captured.out.lower()
    assert "totals_by_term" in captured.out
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
        "filters": {"resource_type": None, "period": None, "country": "England", "bbox": None},
        "pagination": {"page": 2, "size_per_term": 10},
        "total": None,
        "totals_by_term": [],
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
        bbox=None,
    ):
        calls.append((client, terms, size_per_term, page, resource_type, period, country))
        return SearchResults(candidates=[
            CandidateRecord(
                id="abc",
                portal_url="https://portal.ariadne-infrastructure.eu/resource/abc",
                matched_terms=["radiocarbon"],
            )
        ], totals_by_term=[TermTotal(term=term, total={"value": 10, "relation": "eq"}) for term in terms])

    monkeypatch.setattr(cli, "AriadneClient", FakeClient)
    monkeypatch.setattr(cli, "search_terms", fake_semantic_search)

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
        "bbox": None,
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
    monkeypatch.setattr(cli, "search_terms", fake_semantic_search)

    exit_code = cli.main(["search", "radiocarbon"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert captured.err == "error: page must be at least 1\n"


def install_mock_client(monkeypatch, handler):
    client = AriadneClient(client=httpx.Client(transport=httpx.MockTransport(handler)))
    monkeypatch.setattr(cli, "AriadneClient", lambda: client)


def test_search_bbox_and_api_total_end_to_end(monkeypatch, capsys) -> None:
    bbox = "54.4,-1.8,53.5,-0.4"
    calls = []

    def handler(request):
        calls.append(dict(request.url.params))
        return httpx.Response(200, json={
            "total": {"value": 123, "relation": "gte"},
            "hits": [{"id": "abc", "data": {}}], "aggregations": [],
        })

    install_mock_client(monkeypatch, handler)
    assert cli.main(["search", "Neolithic", "--bbox", bbox, "--country", "England",
                     "--period", "Neolithic", "--resource-type", "Dating",
                     "--size", "50", "--page", "2"]) == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["filters"]["bbox"] == bbox
    assert data["total"] == {"value": 123, "relation": "gte"}
    assert data["totals_by_term"] == [{"term": "Neolithic", "total": data["total"]}]
    assert data["candidate_count"] == 1
    assert data["pagination"] == {"page": 2, "size_per_term": 50}
    assert captured.err == ""
    assert calls == [{"q": "neolithic", "bbox": bbox, "country": "England",
                      "temporal": "neolithic", "ariadneSubject": "Date",
                      "size": "50", "page": "2"}]


def test_expansions_preserve_independent_totals_and_deduplicate(monkeypatch, capsys) -> None:
    calls = []

    def handler(request):
        term = request.url.params["q"]
        calls.append(term)
        return httpx.Response(200, json={
            "total": {"value": 100 if term == "radiocarbon" else 20, "relation": "eq"},
            "hits": [{"id": "shared"}, {"id": term}],
        })

    install_mock_client(monkeypatch, handler)
    assert cli.main(["search", "radiocarbon", "--expand", "C14", "--expand", "dating", "--size", "2"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert calls == ["radiocarbon", "c14", "dating"]
    assert data["total"] is None
    assert data["totals_by_term"] == [
        {"term": "radiocarbon", "total": {"value": 100, "relation": "eq"}},
        {"term": "C14", "total": {"value": 20, "relation": "eq"}},
        {"term": "dating", "total": {"value": 20, "relation": "eq"}},
    ]
    assert data["candidate_count"] == 4
    assert data["candidates"][0]["matched_terms"] == ["radiocarbon", "C14", "dating"]


@pytest.mark.parametrize("size", ["200", "51", "0", "-1", "invalid"])
def test_invalid_size_fails_without_request(monkeypatch, capsys, size) -> None:
    def handler(request):
        pytest.fail("invalid size must not make a request")

    install_mock_client(monkeypatch, handler)
    if size == "invalid":
        with pytest.raises(SystemExit) as exc:
            cli.main(["search", "neolithic", "--size", size])
        assert exc.value.code == 2
    else:
        assert cli.main(["search", "neolithic", "--size", size]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    expected = "invalid int value" if size == "invalid" else "between 1 and 50"
    assert expected in captured.err


@pytest.mark.parametrize("payload,message", [
    ({"error": {"msg": "Scrolling exceeded maximum"}}, "ARIADNE API error: Scrolling exceeded maximum"),
    ([], "bare JSON array []"),
])
def test_api_response_errors_reach_stderr(monkeypatch, capsys, payload, message) -> None:
    install_mock_client(monkeypatch, lambda request: httpx.Response(200, json=payload))
    assert cli.main(["search", "neolithic"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert message in captured.err


def test_zero_results_preserve_zero_total(monkeypatch, capsys) -> None:
    total = {"value": 0, "relation": "eq"}
    install_mock_client(monkeypatch, lambda request: httpx.Response(200, json={
        "total": total, "hits": [], "aggregations": [],
    }))
    assert cli.main(["search", "unlikely"]) == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["total"] == total
    assert data["candidate_count"] == 0
    assert data["candidates"] == []
    assert captured.err == ""


def test_get_prints_unmodified_record_json(monkeypatch, capsys) -> None:
    payload = {"id": "abc", "title": {"text": "Example"}, "extra": [1, 2]}

    def handler(request):
        assert request.url.path == "/api/getRecord/abc"
        return httpx.Response(200, json=payload)

    install_mock_client(monkeypatch, handler)
    assert cli.main(["get", "abc"]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == payload
    assert captured.err == ""


@pytest.mark.parametrize("response", [
    httpx.Response(200, text=""), httpx.Response(200, json={}),
    httpx.Response(500, text="server error"),
])
def test_get_failure_has_no_stdout(monkeypatch, capsys, response) -> None:
    install_mock_client(monkeypatch, lambda request: response)
    assert cli.main(["get", "missing"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("error: ARIADNE")
