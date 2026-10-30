# ariadnesearch-cli

Minimal prototype for transparent ARIADNE catalogue search.

## Install and use the CLI

Install Python 3.11 or later and Git. In a terminal, create a virtual environment to keep the CLI and its dependencies separate from other Python projects.

```bash
python -m venv .venv
```

Activate the environment with the command for your shell.

| Shell | Command |
| --- | --- |
| Windows PowerShell | `.\.venv\Scripts\Activate.ps1` |
| macOS or Linux, Bash or Zsh | `source .venv/bin/activate` |

Install the CLI directly from GitHub. This installs the command and its runtime dependencies. The test tools are optional.

```bash
python -m pip install "git+https://github.com/jfpalomeque/ariadnesearch-cli.git"
```

Search for up to five catalogue records matching “radiocarbon” in England.

```bash
ariadnesearch search "radiocarbon" --country England --size 5
```

Search results are JSON on stdout. Errors go to stderr. To see all arguments, filters and output fields, run `ariadnesearch docs`.

## Commands and options

`ariadnesearch search QUERY [options]` searches the catalogue. Quote multi-word terms or filter values. `ariadnesearch docs` prints the bundled Markdown reference offline. Use `-h` or `--help` after the executable or either subcommand for command-line help.

| Search argument | Default | Meaning |
| --- | --- | --- |
| `QUERY` | Required | Free-text search term, lowercased before the request. |
| `--expand TERM` | None | Search an additional term. Repeat the flag for more terms. |
| `--size N` | `5` | Number of records requested per term. |
| `--page N` | `1` | Page to request for each term, starting at 1. |
| `--resource-type TYPE` | Unfiltered | ARIADNE subject facet, such as `Date` or `Site/monument`. The CLI accepts `Dating` as an alias for `Date`. |
| `--period PERIOD` | Unfiltered | Temporal facet, lowercased before the request, such as `"late neolithic"`. |
| `--country COUNTRY` | Unfiltered | Exact, case-sensitive country or region label, such as `England`. |

```bash
ariadnesearch search "radiocarbon" --expand C14 --country England --resource-type Date --period neolithic --size 5 --page 2
```

## Search output

A successful search writes one JSON object to stdout and exits with code 0, including when there are no matches. Errors go to stderr with a non-zero exit code. To save the complete response, append `> results.json` to the command.

The example below uses a fictional record to show every output field.

```json
{
  "command": "search",
  "query": "radiocarbon",
  "expanded_terms": ["radiocarbon", "C14"],
  "filters": {"resource_type": null, "period": null, "country": null},
  "pagination": {"page": 1, "size_per_term": 5},
  "candidate_count": 1,
  "candidates": [
    {
      "id": "example-id",
      "portal_url": "https://portal.ariadne-infrastructure.eu/resource/example-id",
      "title": "Example radiocarbon date",
      "description": null,
      "resource_type": "dataset",
      "source_identifier": null,
      "countries": [],
      "temporal_periods": [],
      "matched_terms": ["C14"],
      "raw": {
        "id": "example-id",
        "data": {"title": {"text": "Example radiocarbon date"}, "resourceType": "dataset"}
      }
    }
  ]
}
```

`expanded_terms` lists the original query and any terms supplied with `--expand`. Each term gets its own request for the selected page. The CLI merges hits with the same `id`, and `matched_terms` records which term searches returned each candidate.

`candidate_count` is the length of `candidates` after merging. With several terms it can exceed `size_per_term`. The CLI omits the catalogue-wide match total. An empty result has `"candidate_count": 0` and `"candidates": []`.

`portal_url` links to the ARIADNE record. `source_identifier` comes from the record’s own identifier field. Missing optional text values appear as `null`, and missing country or period lists appear as `[]`. The `raw` object preserves the original ARIADNE hit, including metadata beyond the fields extracted by the CLI.

## Development and tests

To change the CLI or run its tests, clone the repository and enter the project directory.

```bash
git clone https://github.com/jfpalomeque/ariadnesearch-cli.git
cd ariadnesearch-cli
```

With a virtual environment active, install the local checkout and its test tools, then run the suite.

```bash
python -m pip install -e ".[test]"
python -m pytest
```

The `.` selects the project in the current directory. The `-e` flag makes the install *editable*, so the next time you run `ariadnesearch`, it uses your edited Python files without a reinstall. The `[test]` extra installs `pytest`, the test runner declared in `pyproject.toml`. To work on the CLI without installing pytest, use `python -m pip install -e .`.

Run the suite after changing the client or CLI to catch regressions before others rely on the change. The tests use controlled responses and run offline, so changes in the live catalogue do not affect the results.

| Test file | What it checks |
| --- | --- |
| `tests/test_ariadne.py` | API request parameters, filters, response parsing and error handling |
| `tests/test_semantic.py` | Combining search terms, merging duplicate records and extracting metadata |
| `tests/test_cli.py` | The public command’s JSON output, error messages and bundled documentation |
| `tests/test_probe.py` | The original probe’s output format, filters and pagination fields |

## Resource Type Values

The CLI supports ARIADNE resource-type filtering with `--resource-type`, which maps to the ARIADNE API parameter `ariadneSubject`.

Example:

```bash
ariadnesearch search "radiocarbon" --resource-type Date --size 5
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

Note: the ARIADNE portal UI labels `Date` as `Dating`. The CLI accepts `--resource-type Dating` and sends `Date` to the API.

These are observed catalogue facet values, not a guaranteed permanent vocabulary.

## Period Filter

The CLI supports ARIADNE temporal period filtering with `--period`, which maps to the ARIADNE API parameter `temporal`.

Example:

```bash
ariadnesearch search "radiocarbon" --period neolithic --size 5
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

The CLI supports ARIADNE country/region facet filtering with `--country`, which maps to the ARIADNE API parameter `country`.

Example:

```bash
ariadnesearch search "radiocarbon" --country England --size 5
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

## Licence

The CLI and its documentation are distributed under the [MIT License](LICENSE). Catalogue records returned by ARIADNE retain their respective rights and licences.
