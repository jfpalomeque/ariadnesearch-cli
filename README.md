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

## Output Shape

Candidate records lift a small set of common ARIADNE metadata into top-level fields for convenience, including `countries` and `temporal_periods`. The original ARIADNE search hit is preserved unchanged under `raw`.

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
