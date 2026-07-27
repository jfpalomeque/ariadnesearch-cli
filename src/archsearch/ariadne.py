from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field


DEFAULT_BASE_URL = "https://portal.ariadne-infrastructure.eu/api"


class AriadneError(Exception):
    """Base exception for ARIADNE client failures."""


class AriadneNetworkError(AriadneError):
    """Raised when a request to ARIADNE cannot be completed successfully."""


class AriadneResponseError(AriadneError):
    """Raised when ARIADNE returns an unusable response shape."""


class SearchResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    total: dict[str, Any]
    hits: list[dict[str, Any]]
    aggregations: Any = None
    raw: dict[str, Any] = Field(default_factory=dict)


class AriadneClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout)

    def search(self, query: str, size: int = 10, page: int = 1) -> SearchResponse:
        data = self._get_json(
            "/search",
            params={"q": query.lower(), "size": size, "page": page},
        )

        if not isinstance(data, dict):
            raise AriadneResponseError("ARIADNE search response was not a JSON object")
        if not isinstance(data.get("hits"), list):
            raise AriadneResponseError("ARIADNE search response did not contain a hits list")

        return SearchResponse(
            total=data.get("total", {}),
            hits=data["hits"],
            aggregations=data.get("aggregations"),
            raw=data,
        )

    def get_record(self, record_id: str) -> dict[str, Any]:
        data = self._get_json(f"/getRecord/{record_id}")

        if not isinstance(data, dict) or not data.get("id"):
            raise AriadneResponseError(
                f"ARIADNE record response was empty or invalid for {record_id}"
            )

        return data

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"

        try:
            response = self._client.get(
                url,
                params=params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AriadneNetworkError(f"ARIADNE request failed for {url}: {exc}") from exc

        if not response.text.strip():
            raise AriadneResponseError(f"ARIADNE returned an empty response for {url}")

        try:
            return response.json()
        except ValueError as exc:
            raise AriadneResponseError(f"ARIADNE returned non-JSON for {url}") from exc
