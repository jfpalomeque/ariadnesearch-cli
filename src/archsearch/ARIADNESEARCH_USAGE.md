# ariadnesearch CLI

Minimal command-line interface for transparent ARIADNE catalogue metadata search.

This tool searches ARIADNE records. Candidate records are catalogue metadata matches, not archaeological confirmation.

## Commands

```bash
ariadnesearch docs
ariadnesearch search QUERY [options]
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

## Arguments

| Argument | Required | Format | Meaning | Notes |
| --- | --- | --- | --- | --- |
| `QUERY` | yes | string | Main ARIADNE free-text query | Lowercased before sending to ARIADNE |
| `--expand` | no | repeatable string | Additional transparent search term | One ARIADNE search per term |
| `--size` | no | integer | Results to request per term | Default: `5` |
| `--page` | no | integer >= 1 | ARIADNE result page for each term | Default: `1` |
| `--resource-type` | no | string | ARIADNE resource type facet | Sent as `ariadneSubject` |
| `--period` | no | string | ARIADNE temporal period facet | Lowercased and sent as `temporal` |
| `--country` | no | string | ARIADNE country/region facet | Case-sensitive exact value |

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

Search output has this shape:

```json
{
  "command": "search",
  "query": "radiocarbon",
  "expanded_terms": ["radiocarbon", "C14"],
  "filters": {
    "resource_type": "Date",
    "period": "neolithic",
    "country": "England"
  },
  "pagination": {
    "page": 1,
    "size_per_term": 10
  },
  "candidate_count": 1,
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

## Geography

This CLI does not provide coordinate, radius, or bounding-box filtering. Agents may inspect `raw.data.spatial` and perform external spatial filtering. ARIADNE server-side `bbox` behaviour was observed but was not reliable enough to expose in this CLI.

## Agent Guidance

Run `ariadnesearch docs` to inspect supported arguments and known values. Use explicit query terms and explicit filters. Do not infer unsupported flags. Inspect `raw` when source metadata details matter.
