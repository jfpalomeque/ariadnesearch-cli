# ariadnesearch CLI

Minimal command-line interface for transparent ARIADNE catalogue metadata search.

This tool searches ARIADNE records. Candidate records are catalogue metadata matches, not archaeological confirmation.

## Commands

```bash
ariadnesearch docs
ariadnesearch search QUERY [options]
ariadnesearch get RECORD_ID
```

## docs

Prints this local reference document. This command does not call the ARIADNE API.

```bash
ariadnesearch docs
```

## search

Runs a transparent ARIADNE search and prints JSON to stdout.

```bash
ariadnesearch search "radiocarbon" --expand C14 --country England --period neolithic --resource-type Date --size 10 --page 1
```

## get

Prints the API record JSON unchanged (no search wrapper), using a candidate's `id`:

```bash
ariadnesearch get a307b42cbeea146bb1768849482c3a9de38fe2d623c9e2177d2a5388dad9564a
```

Success writes JSON to stdout and exits `0`. Network, empty-body and invalid-record errors go to stderr with a non-zero exit and no result on stdout.

## Arguments

| Argument | Required | Format | Meaning | Notes |
| --- | --- | --- | --- | --- |
| `QUERY` | yes | string | Main ARIADNE free-text query | Lowercased before sending to ARIADNE |
| `--expand` | no | repeatable string | Additional transparent search term | One ARIADNE search per term |
| `--size` | no | integer 1–50 | Results to request per term | Default: `5`; other values rejected, not clamped |
| `--page` | no | integer >= 1 | ARIADNE result page for each term | Default: `1` |
| `--resource-type` | no | string | ARIADNE resource type facet | Sent as `ariadneSubject` |
| `--period` | no | string | ARIADNE temporal period facet | Lowercased and sent as `temporal` |
| `--country` | no | string | ARIADNE country/region facet | Case-sensitive exact value |
| `--bbox` | no | string | API bounding box | `north,west,south,east`, forwarded unchanged; not validated |

## Expansion and pagination

Each non-empty term (query plus repeated `--expand` values) is trimmed and searched independently, once for the selected page, with the same filters. Candidates are unioned by record `id`; duplicate records contain all matching terms in `matched_terms`. Before deduplication, the maximum number of hits is `effective page size × number of terms`. This is explicit text-query expansion, not semantic retrieval or archaeological interpretation.

ARIADNE's maximum page size is 50. The maximum retrieval window is 10,000 records: `from + size <= 10000`, where `from = (page - 1) × size`. Totals can exceed this ceiling, but not all matches can then be retrieved. There is no automatic pagination. Beyond the window, HTTP 200 can contain `{"error":{"msg":"Scrolling exceeded maximum"}}`; the CLI reports the API message as an error, not as missing hits or zero matches.

## Known Resource Type Values

Observed ARIADNE `ariadneSubject` values include:

```text
Site/monument
Artefact
Fieldwork
Coin
Fieldwork report
Fieldwork archive
Maritime
Inscription
Monument
Rock Art
Date
Scientific analysis
Burial
Building survey
E-Publication
Not provided
```

The CLI accepts `Dating` as an alias and sends `Date` to ARIADNE.

These are observed catalogue facet values, not a guaranteed permanent vocabulary.

## Known Period Values

Observed period values include:

```text
neolithic
early neolithic
middle neolithic
late neolithic
bronze age
early bronze age
middle bronze age
late bronze age
mesolithic
roman
medieval
post medieval
iron age
prehistoric
later prehistoric
```

The CLI lowercases `--period` before sending it. Period matching appears to use exact ARIADNE facet values. A search for `--period neolithic` should not be assumed to include records tagged only as `early neolithic`, `middle neolithic`, or `late neolithic`.

## Known Country Values

Observed country/region values include:

```text
England
Scotland
Wales
Northern Ireland
Ireland
United Kingdom
Great Britain
Isle of Man
Česká republika
```

Country values are case-sensitive. During testing, `England` returned matches while `england` returned none. `UK` should not be assumed to match `United Kingdom`, and `Czech Republic` should not be assumed to match `Česká republika`.

## Output Contract

Successful `search` commands write JSON to stdout and return exit code `0`. Errors are written to stderr and return a non-zero exit code. A successful search with zero candidates still returns exit code `0`.

This example shows the JSON returned for a search with zero matches.

```json
{
  "command": "search",
  "query": "radiocarbon",
  "expanded_terms": ["radiocarbon", "C14"],
  "filters": {
    "resource_type": "Date",
    "period": "neolithic",
    "country": "England",
    "bbox": null
  },
  "pagination": {
    "page": 1,
    "size_per_term": 10
  },
  "total": null,
  "totals_by_term": [
    {"term": "radiocarbon", "total": {"value": 0, "relation": "eq"}},
    {"term": "C14", "total": {"value": 0, "relation": "eq"}}
  ],
  "candidate_count": 0,
  "candidates": []
}
```

Candidate records include:

```text
id
portal_url
title
description
resource_type
source_identifier
countries
temporal_periods
matched_terms
raw
```

Top-level candidate fields are local normalised convenience fields. `raw` preserves the original ARIADNE search hit.

`candidate_count` counts candidates returned by this invocation after deduplication, not all API matches. `total` is the unchanged API total object for a single non-empty term (including its `relation`, not just `value`). It is `null` for multiple terms because their overlap is unknown. `totals_by_term` preserves every executed term and its API total; do not sum these totals. A valid zero-result object preserves its zero total and returns empty candidates successfully. `expanded_terms` echoes the supplied terms; `totals_by_term` uses trimmed non-empty terms actually searched.

## Geography

The CLI exposes ARIADNE's server-side `bbox` filter as pure pass-through. Callers supply coordinates in `north,west,south,east` order (NW corner, then SE corner):

```bash
ariadnesearch search "neolithic" --bbox "54.4,-1.8,53.5,-0.4" --country England --size 5
```

**Warning: bbox geometry is not validated locally.** For an ordinary non-antimeridian box, use `north > south` and `west < east`. Reversed longitudes (`west > east`) invoke antimeridian semantics and can give plausible but incorrect results for the intended area. The CLI does not reorder, trim or convert bbox strings. Invalid geometry can produce a bare JSON array `[]`, which is reported as an invalid-response error, never treated as a valid zero-match object.

The bbox filter works alongside `q`, `country`, `temporal` (CLI `--period`), `ariadneSubject` (CLI `--resource-type`), `page` and `size`. There is no server-side radius search. Flags for `spatial`, `geo`, `lat`, `lon`, `radius` and `within` are not supported. The CLI performs no geocoding, point-to-box conversion, distance filtering or geographic analysis; the user or calling agent handles these tasks and may inspect `raw.data.spatial`.

## Agent Guidance

Run `ariadnesearch docs` to inspect supported arguments and known values. Use explicit query terms and explicit filters. Do not infer unsupported flags. Inspect `raw` when source metadata details matter.
