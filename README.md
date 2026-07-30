# Semantic CLI

Minimal prototype for transparent ARIADNE catalogue search.

## CLI

Install locally:

```bash
python -m pip install -e ".[test]"
```

Show the bundled agent/human reference:

```bash
ariadnesearch docs
```

Search ARIADNE:

```bash
ariadnesearch search "radiocarbon" --country England --size 5
```

Search results are JSON on stdout. Errors are written to stderr. Full supported arguments, known values, output fields, and caveats are documented by `ariadnesearch docs`.

## Output Shape

Candidate records lift a small set of common ARIADNE metadata into top-level fields for convenience, including `countries` and `temporal_periods`. The original ARIADNE search hit is preserved unchanged under `raw`.

## Resource Type Values

The probe supports ARIADNE resource-type filtering with `--resource-type`, which maps to the ARIADNE API parameter `ariadneSubject`.

Example:

```bash
python -m archsearch.probe "radiocarbon" --resource-type Date --size 5
```

Current observed `ariadneSubject` values from the live ARIADNE aggregation endpoint:

| Value | Current count |
| --- | ---: |
| `Site/monument` | 1,412,663 |
| `Artefact` | 1,075,121 |
| `Fieldwork` | 478,197 |
| `Coin` | 476,184 |
| `Fieldwork report` | 435,600 |
| `Fieldwork archive` | 120,153 |
| `Maritime` | 100,248 |
| `Inscription` | 83,375 |
| `Monument` | 29,561 |
| `Rock Art` | 27,494 |
| `Date` | 13,592 |
| `Scientific analysis` | 12,424 |
| `Burial` | 12,152 |
| `Building survey` | 2,094 |
| `E-Publication` | 77 |
| `Not provided` | 32 |

Note: the ARIADNE portal UI labels `Date` as `Dating`. The probe accepts `--resource-type Dating` and sends `Date` to the API.

These are observed catalogue facet values, not a guaranteed permanent vocabulary.

## Period Filter

The probe supports ARIADNE temporal period filtering with `--period`, which maps to the ARIADNE API parameter `temporal`.

Example:

```bash
python -m archsearch.probe "radiocarbon" --period neolithic --size 5
```

Period values are sent to ARIADNE in lowercase because observed API behavior is case-sensitive. For example, `temporal=neolithic` returns matches, while `temporal=Neolithic` returned none during testing.

Observed period examples include:

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

The ARIADNE temporal filter appears to match exact period facet values. A search for `--period neolithic` should not be assumed to include records tagged only as `early neolithic`, `middle neolithic`, or `late neolithic`. Some records may still appear in both broad and subperiod searches if their metadata contains both period labels.

If broad Neolithic coverage is important, run separate searches for `neolithic`, `early neolithic`, `middle neolithic`, and `late neolithic`, then compare or merge the candidate records.

## Country Filter

The probe supports ARIADNE country/region facet filtering with `--country`, which maps to the ARIADNE API parameter `country`.

Example:

```bash
python -m archsearch.probe "radiocarbon" --country England --size 5
```

Country values are sent as exact ARIADNE facet labels after whitespace trimming. They are case-sensitive: for example, `England` returned matches during testing, while `england` returned none. `UK` should not be assumed to match `United Kingdom`.

Observed examples include:

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

This is a catalogue country/region filter, not exact coordinate, bounding-box, or radius search.
