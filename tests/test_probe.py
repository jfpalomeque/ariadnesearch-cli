from __future__ import annotations

from ariadnesearch.probe import build_output
from ariadnesearch.semantic import CandidateRecord


def test_build_output_serialises_candidates() -> None:
    candidate = CandidateRecord(
        id="abc",
        portal_url="https://portal.ariadne-infrastructure.eu/resource/abc",
        title="Radiocarbon date",
        matched_terms=["radiocarbon"],
        raw={"id": "abc"},
    )

    output = build_output("radiocarbon", ["radiocarbon"], [candidate])

    assert output == {
        "query": "radiocarbon",
        "expanded_terms": ["radiocarbon"],
        "filters": {"resource_type": None, "period": None, "country": None},
        "pagination": {"page": 1, "size_per_term": 5},
        "candidate_count": 1,
        "candidates": [
            {
                "id": "abc",
                "portal_url": "https://portal.ariadne-infrastructure.eu/resource/abc",
                "title": "Radiocarbon date",
                "description": None,
                "resource_type": None,
                "source_identifier": None,
                "countries": [],
                "temporal_periods": [],
                "matched_terms": ["radiocarbon"],
                "raw": {"id": "abc"},
            }
        ],
    }


def test_build_output_includes_resource_type_filter() -> None:
    output = build_output("radiocarbon", ["radiocarbon"], [], resource_type="Date")

    assert output["filters"] == {
        "resource_type": "Date",
        "period": None,
        "country": None,
    }


def test_build_output_includes_period_filter() -> None:
    output = build_output("radiocarbon", ["radiocarbon"], [], period="neolithic")

    assert output["filters"] == {
        "resource_type": None,
        "period": "neolithic",
        "country": None,
    }


def test_build_output_includes_country_filter() -> None:
    output = build_output("radiocarbon", ["radiocarbon"], [], country="England")

    assert output["filters"] == {
        "resource_type": None,
        "period": None,
        "country": "England",
    }


def test_build_output_includes_pagination() -> None:
    output = build_output("radiocarbon", ["radiocarbon"], [], page=3, size_per_term=50)

    assert output["pagination"] == {"page": 3, "size_per_term": 50}
