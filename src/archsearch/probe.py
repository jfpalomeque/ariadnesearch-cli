from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from archsearch.ariadne import AriadneClient, AriadneError
from archsearch.semantic import CandidateRecord, semantic_search


def build_output(
    query: str,
    terms: list[str],
    candidates: list[CandidateRecord],
    resource_type: str | None = None,
) -> dict[str, Any]:
    return {
        "query": query,
        "expanded_terms": terms,
        "filters": {"resource_type": resource_type},
        "candidate_count": len(candidates),
        "candidates": [candidate.model_dump() for candidate in candidates],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Minimal ARIADNE transparent semantic-search probe"
    )
    parser.add_argument("query", help="Main ARIADNE search term")
    parser.add_argument(
        "--expand",
        action="append",
        default=[],
        help="Additional transparent expansion term; may be repeated",
    )
    parser.add_argument("--size", type=int, default=5, help="Results to request per term")
    parser.add_argument(
        "--resource-type",
        help="ARIADNE resource type filter, e.g. Date or Site/monument",
    )
    args = parser.parse_args(argv)

    terms = [args.query, *args.expand]
    client = AriadneClient()

    try:
        candidates = semantic_search(
            client,
            terms,
            size_per_term=args.size,
            resource_type=args.resource_type,
        )
    except (AriadneError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            build_output(args.query, terms, candidates, resource_type=args.resource_type),
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
