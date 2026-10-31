from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ariadnesearch.ariadne import AriadneClient


PORTAL_RESOURCE_URL = "https://portal.ariadne-infrastructure.eu/resource"


class CandidateRecord(BaseModel):
    id: str
    portal_url: str
    title: str | None = None
    description: str | None = None
    resource_type: str | None = None
    source_identifier: str | None = None
    countries: list[str] = Field(default_factory=list)
    temporal_periods: list[str] = Field(default_factory=list)
    matched_terms: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class TermTotal(BaseModel):
    term: str
    total: dict[str, Any]


class SearchResults(BaseModel):
    candidates: list[CandidateRecord]
    totals_by_term: list[TermTotal]


def search_terms(
    client: AriadneClient,
    terms: list[str],
    size_per_term: int = 10,
    page: int = 1,
    resource_type: str | None = None,
    period: str | None = None,
    country: str | None = None,
    bbox: str | None = None,
) -> SearchResults:
    """Union independent catalogue queries; preserve their totals without summing."""
    cleaned_terms = [term.strip() for term in terms if term.strip()]
    if not cleaned_terms:
        raise ValueError("semantic_search requires at least one non-empty term")
    if page < 1:
        raise ValueError("page must be at least 1")
    if not 1 <= size_per_term <= 50:
        raise ValueError("size must be between 1 and 50")

    candidates: dict[str, CandidateRecord] = {}
    totals: list[TermTotal] = []

    for term in cleaned_terms:
        bbox_params = {"bbox": bbox} if bbox is not None else {}
        response = client.search(
            term,
            size=size_per_term,
            page=page,
            resource_type=resource_type,
            period=period,
            country=country,
            **bbox_params,
        )
        totals.append(TermTotal(term=term, total=response.total))

        for hit in response.hits:
            record_id = hit.get("id")
            if not isinstance(record_id, str) or not record_id:
                continue

            if record_id in candidates:
                candidates[record_id].matched_terms.append(term)
                continue

            candidates[record_id] = _normalise_hit(hit, term)

    return SearchResults(candidates=list(candidates.values()), totals_by_term=totals)


def semantic_search(
    client: AriadneClient,
    terms: list[str],
    size_per_term: int = 10,
    page: int = 1,
    resource_type: str | None = None,
    period: str | None = None,
    country: str | None = None,
    bbox: str | None = None,
) -> list[CandidateRecord]:
    """Compatibility wrapper: explicit term union, not semantic retrieval."""
    return search_terms(
        client, terms, size_per_term, page, resource_type, period, country, bbox
    ).candidates


def _normalise_hit(hit: dict[str, Any], matched_term: str) -> CandidateRecord:
    data = hit.get("data")
    if not isinstance(data, dict):
        data = {}

    title = data.get("title")
    if not isinstance(title, dict):
        title = {}

    description = data.get("description")
    if not isinstance(description, dict):
        description = {}

    return CandidateRecord(
        id=hit["id"],
        portal_url=f"{PORTAL_RESOURCE_URL}/{hit['id']}",
        title=title.get("text"),
        description=description.get("text"),
        resource_type=data.get("resourceType"),
        source_identifier=data.get("identifier"),
        countries=_extract_country_names(data),
        temporal_periods=_extract_period_names(data),
        matched_terms=[matched_term],
        raw=hit,
    )


def _extract_country_names(data: dict[str, Any]) -> list[str]:
    values: list[str] = []
    countries = data.get("country")
    if not isinstance(countries, list):
        return values

    for country in countries:
        if isinstance(country, dict):
            _append_unique(values, country.get("name"))
        else:
            _append_unique(values, country)

    return values


def _extract_period_names(data: dict[str, Any]) -> list[str]:
    values: list[str] = []

    for field_name in ("temporal", "nativePeriod"):
        periods = data.get(field_name)
        if not isinstance(periods, list):
            continue

        for period in periods:
            if isinstance(period, dict):
                _append_unique(values, period.get("periodName"))
            else:
                _append_unique(values, period)

    return values


def _append_unique(values: list[str], value: Any) -> None:
    if isinstance(value, str):
        stripped = value.strip()
        if stripped and stripped not in values:
            values.append(stripped)
