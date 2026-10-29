# Data — BPI Challenge 2020: Domestic Declarations

## Source

- Dataset: BPI Challenge 2020, Domestic Declarations (travel expense declarations at a university, 2017–2018).
- Official DOI: https://doi.org/10.4121/uuid:3f422315-ed9d-4882-891f-e180b5b4feb5
- Licence: CC BY-NC 4.0 (attribution required; non-commercial use only).
- Citation: van Dongen, Boudewijn (2020): BPI Challenge 2020: Domestic Declarations. 4TU.ResearchData

Download URL, download time, file size, MD5 and the check against the publisher's values are recorded in
[`raw/bpi2020/SOURCE.md`](raw/bpi2020/SOURCE.md).

## Folders

| Path | What it is | Who writes it |
|---|---|---|
| `raw/bpi2020/DomesticDeclarations.xes.gz` | Original event log, unchanged | GitHub Actions (`.github/workflows/fetch-bpi2020.yml`) |
| `raw/bpi2020/SOURCE.md` | Provenance of the raw file | GitHub Actions |
| `processed/events.csv` | One row per event (56,437) | `analysis/01_clean.py` |
| `processed/cases.csv` | One row per case (10,500) | `analysis/01_clean.py` |

`raw/` is never modified. Everything in `processed/` is rebuilt from it with:

```bash
python3 analysis/01_clean.py
```

Every cleaning check and decision is in [`../docs/data-cleaning-log.md`](../docs/data-cleaning-log.md).
