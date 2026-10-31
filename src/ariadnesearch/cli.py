from __future__ import annotations

import argparse
import json
import sys
from importlib.resources import files
from typing import Any

from ariadnesearch.ariadne import AriadneClient, AriadneError
from ariadnesearch.semantic import CandidateRecord, TermTotal, search_terms


DOCS_FILE = "ARIADNESEARCH_USAGE.md"


def build_search_output(
    query: str,
    terms: list[str],
    candidates: list[CandidateRecord],
    resource_type: str | None = None,
    period: str | None = None,
    country: str | None = None,
    page: int = 1,
    size_per_term: int = 5,
    bbox: str | None = None,
    totals_by_term: list[TermTotal] | None = None,
) -> dict[str, Any]:
    totals = totals_by_term or []
    return {
        "command": "search",
        "query": query,
        "expanded_terms": terms,
        "filters": {
            "resource_type": resource_type,
            "period": period,
            "country": country,
            "bbox": bbox,
        },
        "pagination": {"page": page, "size_per_term": size_per_term},
        "total": totals[0].total if len(totals) == 1 else None,
        "totals_by_term": [item.model_dump() for item in totals],
        "candidate_count": len(candidates),
        "candidates": [candidate.model_dump() for candidate in candidates],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ariadnesearch")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("docs")
    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("record_id")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--expand", action="append", default=[])
    search_parser.add_argument("--size", type=int, default=5, help="Results per term (1–50)")
    search_parser.add_argument("--page", type=int, default=1)
    search_parser.add_argument("--resource-type")
    search_parser.add_argument("--period")
    search_parser.add_argument("--country")
    search_parser.add_argument(
        "--bbox", help="Pass through north,west,south,east unchanged; not validated. "
        "Use north > south and west < east; reversed longitudes can give incorrect results."
    )

    args = parser.parse_args(argv)

    if args.command == "docs":
        return run_docs()
    if args.command == "search":
        return run_search(args)
    if args.command == "get":
        return run_get(args.record_id)

    parser.error("expected command: docs, search or get")


def run_docs() -> int:
    docs = files("ariadnesearch").joinpath(DOCS_FILE).read_text(encoding="utf-8")
    _write_stdout(docs)
    return 0


def run_search(args: argparse.Namespace) -> int:
    terms = [args.query, *args.expand]
    client = AriadneClient()

    try:
        result = search_terms(
            client,
            terms,
            size_per_term=args.size,
            page=args.page,
            resource_type=args.resource_type,
            period=args.period,
            country=args.country,
            bbox=args.bbox,
        )
    except (AriadneError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _write_stdout(
        json.dumps(
            build_search_output(
                args.query,
                terms,
                result.candidates,
                resource_type=args.resource_type,
                period=args.period,
                country=args.country,
                page=args.page,
                size_per_term=args.size,
                bbox=args.bbox,
                totals_by_term=result.totals_by_term,
            ),
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def run_get(record_id: str) -> int:
    try:
        record = AriadneClient().get_record(record_id)
    except (AriadneError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    _write_stdout(json.dumps(record, indent=2, ensure_ascii=False))
    return 0


def _write_stdout(text: str) -> None:
    try:
        sys.stdout.write(f"{text}\n")
    except UnicodeEncodeError:
        sys.stdout.buffer.write(f"{text}\n".encode("utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
