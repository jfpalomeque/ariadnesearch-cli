from __future__ import annotations

import httpx
import pytest

from archsearch.ariadne import AriadneClient, AriadneNetworkError, AriadneResponseError


def make_client(handler):
    transport = httpx.MockTransport(handler)
    return AriadneClient(client=httpx.Client(transport=transport))


def test_search_sends_expected_params_and_lowercases_query() -> None:
    seen_request = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal seen_request
        seen_request = request
        return httpx.Response(
            200,
            json={
                "total": {"value": 1, "relation": "eq"},
                "hits": [{"id": "abc", "data": {}}],
                "aggregations": [],
            },
        )

    client = make_client(handler)
    response = client.search("RadioCarbon", size=2, page=3)

    assert response.hits == [{"id": "abc", "data": {}}]
    assert seen_request is not None
    assert seen_request.url.path == "/api/search"
    assert dict(seen_request.url.params) == {
        "q": "radiocarbon",
        "size": "2",
        "page": "3",
    }


def test_search_preserves_raw_response() -> None:
    payload = {
        "total": {"value": 0, "relation": "eq"},
        "hits": [],
        "aggregations": [],
    }

    client = make_client(lambda request: httpx.Response(200, json=payload))
    response = client.search("unlikely")

    assert response.total == {"value": 0, "relation": "eq"}
    assert response.hits == []
    assert response.raw == payload


def test_search_rejects_missing_hits() -> None:
    client = make_client(lambda request: httpx.Response(200, json={"total": {}}))

    with pytest.raises(AriadneResponseError, match="hits list"):
        client.search("radiocarbon")


def test_search_rejects_non_list_hits() -> None:
    client = make_client(
        lambda request: httpx.Response(200, json={"total": {}, "hits": {}})
    )

    with pytest.raises(AriadneResponseError, match="hits list"):
        client.search("radiocarbon")


def test_get_record_returns_valid_record() -> None:
    payload = {"id": "abc", "title": {"text": "Example"}}
    client = make_client(lambda request: httpx.Response(200, json=payload))

    assert client.get_record("abc") == payload


def test_get_record_rejects_empty_body() -> None:
    client = make_client(lambda request: httpx.Response(200, text=""))

    with pytest.raises(AriadneResponseError, match="empty response"):
        client.get_record("missing")


def test_get_record_rejects_missing_id() -> None:
    client = make_client(lambda request: httpx.Response(200, json={}))

    with pytest.raises(AriadneResponseError, match="empty or invalid"):
        client.get_record("missing")


def test_http_error_becomes_ariadne_network_error() -> None:
    client = make_client(lambda request: httpx.Response(500, text="server error"))

    with pytest.raises(AriadneNetworkError, match="request failed"):
        client.search("radiocarbon")
