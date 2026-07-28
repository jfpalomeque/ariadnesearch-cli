# Semantic CLI

Minimal prototype for transparent ARIADNE catalogue search.

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
