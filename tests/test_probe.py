from __future__ import annotations

from archsearch.probe import build_output
from archsearch.semantic import CandidateRecord


def test_build_output_serialises_candidates() -> None:
    candidate = CandidateRecord(
        id="abc",
        title="Radiocarbon date",
        matched_terms=["radiocarbon"],
        raw={"id": "abc"},
    )

    output = build_output("radiocarbon", ["radiocarbon"], [candidate])

    assert output == {
        "query": "radiocarbon",
        "expanded_terms": ["radiocarbon"],
        "candidate_count": 1,
        "candidates": [
            {
                "id": "abc",
                "title": "Radiocarbon date",
                "description": None,
                "resource_type": None,
                "source_identifier": None,
                "matched_terms": ["radiocarbon"],
                "raw": {"id": "abc"},
            }
        ],
    }
