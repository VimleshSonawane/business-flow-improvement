# Business Flow Improvement: Approval Workflow (DMAIC, real data)

Why 1 in 10 travel-expense claims at a university waits more than 20 days to be paid, and three
proposed fixes that meet every target in a what-if model built on the real 2018 process log.

**Links:**
[Tableau dashboard](https://public.tableau.com/app/profile/vimlesh.vilas.sonawane/viz/ApprovalWorkflowBaselineBPI2020realdata/Baselinedashboard) ·
[Final presentation (PDF)](docs/approval-workflow-final-presentation.pdf) ·
[Findings and business case](docs/findings-and-business-case.md) ·
[Live demo page](https://business-flow-improvement-demo.vercel.app)

**Author:** Vimlesh Sonawane, project manager and analyst. Self-initiated portfolio project, run as
a DMAIC project (Define, Measure, Analyze, Improve, Control).

## Results at a glance

### 2018 baseline (measured)

| KPI | Value | Base | Source |
|---|---:|---|---|
| Median days from submission to payment | 8.05 | 7,903 paid 2018 claims | `data/outputs/tableau/kpi_summary.csv` (1a) |
| P90 days from submission to payment | 20.25 | 7,903 paid 2018 claims | `kpi_summary.csv` (1d) |
| Claims rejected at least once | 13.14% | 1,072 of 8,160 submitted 2018 claims | `kpi_summary.csv` (4a) |
| Payments made on a Monday or Thursday | 99.66% | 7,876 of 7,903 payments | `kpi_summary.csv` (3b) |

### Main findings (measured)

From [`docs/findings-and-business-case.md`](docs/findings-and-business-case.md) and
[`docs/baseline-kpi-report.md`](docs/baseline-kpi-report.md):

1. **Payments run in batches.** Payments are released on Mondays and Thursdays. The wait from
   payment request to payment is a median of 3.21 days, the longest median wait of any step.
2. **Approvals have long tails.** Most approvals are quick, but the slowest 10% wait 4.85 days
   (budget owner), 6.21 days (supervisor) and 6.83 days (before the payment request).
3. **Rework costs time.** Administration made 948 of the 1,229 rejections. Rejected claims take a
   median of 13.21 days to pay, against 7.34 days for claims never rejected. A supervisor
   rejection adds the most: +9.30 days (`data/outputs/rework_extra_days.csv`).
4. **Zero-amount claims are always rejected.** 253 of the 1,072 rejected claims (23.6%) had an
   amount of zero. All 253 were rejected; none was paid.
5. **Control exceptions.** Two claims (95149 and 90815, both 2017) were paid without final
   approval. They are flagged for review: either a control failure or a data issue, not
   determinable from this data. 7 payments had no payment request step.

### All three fixes together (S6): a what-if estimate, not a result

The three proposed fixes are daily payment runs (F1), a claim checklist with an "amount > 0" rule
(F2), and approval reminders after 3 days (F3). Modelled together on the 2018 data
(`data/outputs/scenarios.csv`, row S6):

| KPI | 2018 baseline | S6 estimate | Charter target | Target met? |
|---|---:|---:|---:|:---:|
| P90 days to payment | 20.25 | 8.74 | ≤ 14 | yes |
| Claims rejected at least once | 13.14% | 7.30%* | ≤ 8% | yes |
| Median payment wait (days) | 3.21 | 1.00 | ≤ 1 | yes |

\* Over the 7,907 submitted claims left after zero-amount claims are blocked; 7.07% over all 8,160.

**These are estimates.** None of the fixes was implemented. The 40% cut in Administration
rejections is an assumption; the zero-amount effect is observed in the data.

## Deliverables

| # | Deliverable | Tool | File or screenshot |
|---|---|---|---|
| D1 | Project charter | GitHub | [`docs/charter.md`](docs/charter.md) |
| D2 | Stakeholder map and RACI | Miro | [stakeholders](docs/Screenshots/miro-1-overview-stakeholders.png) · [RACI](docs/Screenshots/miro-2-raci.png) |
| D3 | Baseline KPI report | Python, Tableau | [`docs/baseline-kpi-report.md`](docs/baseline-kpi-report.md) · [dashboard](docs/Screenshots/tableau-6-dashboard.png) |
| D4 | As-is process map | Miro | [map](docs/Screenshots/miro-3-asis-map.png) · [rework loops](docs/Screenshots/miro-4-asis-loops.png) |
| D5 | Root-cause analysis (fishbone) | Miro | [fishbone](docs/Screenshots/miro-5-fishbon.png) |
| D6 | To-be process and prioritized fixes | Miro, Python | [impact/effort](docs/Screenshots/miro-6-impact-effort.png) · [to-be](docs/Screenshots/miro-7-tobe.png) · [`docs/findings-and-business-case.md`](docs/findings-and-business-case.md) |
| D7 | Implementation roadmap and control plan | Smartsheet | [roadmap](docs/Screenshots/smartsheet-5-roadmap.png) · [control plan](docs/Screenshots/smartsheet-6-control-plan.png) |
| D8 | Final presentation | PowerPoint | [PDF](docs/approval-workflow-final-presentation.pdf) · [PPTX](docs/approval-workflow-final-presentation.pptx) |

## How the project was run

### Smartsheet: schedule, RAID log, dashboard, roadmap, control plan

![Smartsheet Gantt schedule](docs/Screenshots/smartsheet-1-gantt.png)
![Smartsheet RAID log](docs/Screenshots/smartsheet-2-raid.png)
![Smartsheet dashboard](docs/Screenshots/smartsheet-3-dashboard.png)
![Smartsheet progress by phase](docs/Screenshots/smartsheet-4-progress.png)
![Smartsheet roadmap](docs/Screenshots/smartsheet-5-roadmap.png)
![Smartsheet control plan](docs/Screenshots/smartsheet-6-control-plan.png)

### Asana: tasks, change requests, automation, status

![Asana task list](docs/Screenshots/asana-1-list.png)
![Asana board](docs/Screenshots/asana-2-board.png)
![Asana change request form](docs/Screenshots/asana-3-form.png)
![Asana automation rule](docs/Screenshots/asana-4-automation.png)
![Asana change request](docs/Screenshots/asana-5-change-request.png)
![Asana status update](docs/Screenshots/asana-6-status.png)
![Asana task list with completed Miro deliverables](docs/Screenshots/asana-7-miro-done.png)

### Miro: stakeholder map, RACI and process maps

![Miro overview and stakeholder map](docs/Screenshots/miro-1-overview-stakeholders.png)
![Miro RACI](docs/Screenshots/miro-2-raci.png)
![Miro as-is process map](docs/Screenshots/miro-3-asis-map.png)
![Miro as-is rework loops](docs/Screenshots/miro-4-asis-loops.png)
![Miro fishbone](docs/Screenshots/miro-5-fishbon.png)
![Miro impact/effort matrix](docs/Screenshots/miro-6-impact-effort.png)
![Miro to-be process](docs/Screenshots/miro-7-tobe.png)

### Tableau: baseline dashboard

[Open the live dashboard](https://public.tableau.com/app/profile/vimlesh.vilas.sonawane/viz/ApprovalWorkflowBaselineBPI2020realdata/Baselinedashboard)

![Tableau dashboard](docs/Screenshots/tableau-6-dashboard.png)
![Tableau cycle time](docs/Screenshots/tableau-1-cycle-time.png)
![Tableau wait by step](docs/Screenshots/tableau-2-wait-by-step.png)
![Tableau rejections by role](docs/Screenshots/tableau-3-rejections.png)
![Tableau monthly volume](docs/Screenshots/tableau-4-monthly.png)
![Tableau KPIs](docs/Screenshots/tableau-5-kpis.png)

## Data and reproducibility

- **Source:** BPI Challenge 2020, Domestic Declarations: the travel-expense approval log of a
  university, 2017–2018. 10,500 claims and 56,437 events.
- **DOI:** https://doi.org/10.4121/uuid:3f422315-ed9d-4882-891f-e180b5b4feb5
- **License:** CC BY-NC 4.0 (attribution, non-commercial use only). Citation: van Dongen,
  Boudewijn (2020): BPI Challenge 2020: Domestic Declarations. 4TU.ResearchData.
- **Checksum verification:** the GitHub Actions workflow
  [`.github/workflows/fetch-bpi2020.yml`](.github/workflows/fetch-bpi2020.yml) downloaded the raw
  file. Its size (933,930 bytes) and MD5 (`6a78c39491498363ce4788e0e8ca75ef`) match the
  publisher's values. The result is recorded in
  [`data/raw/bpi2020/SOURCE.md`](data/raw/bpi2020/SOURCE.md).

To rebuild every output from the raw file, run these three scripts. They use only the Python 3
standard library, and each run gives byte-identical files.

```bash
python3 analysis/01_clean.py
```
Cleans the log into `data/processed/` and writes `docs/data-cleaning-log.md`.

```bash
python3 analysis/02_baseline.py
```
Writes the baseline KPIs to `data/outputs/tableau/` and `docs/baseline-kpi-report.md`.

```bash
python3 analysis/03_scenarios.py
```
Writes the what-if scenarios to `data/outputs/scenarios.csv` and `data/outputs/rework_extra_days.csv`.

Every analysis decision is recorded in [`docs/decisions.md`](docs/decisions.md).

## What is real and what is not

- **Real:** the data. It is a published event log, verified against the publisher's checksum,
  and every number traces to a script in `analysis/`.
- **Role-played:** the stakeholders (sponsor, process owner, approvers, payments team). There was
  no access to the real organisation.
- **Proposed, not implemented:** the fixes F1–F3 and the roadmap.
- **Estimates, not results:** the scenarios S1–S6 are what-if models on 2018 data. Causes that the
  data can't show (such as why a claim was rejected) are labelled as hypotheses.

## Repository structure

```
analysis/        01_clean.py, 02_baseline.py, 03_scenarios.py
data/raw/        the original event log and SOURCE.md (never modified)
data/processed/  events.csv and cases.csv (cleaned)
data/outputs/    scenarios.csv, rework_extra_days.csv; tableau/ holds the dashboard tables
docs/            charter, KPI report, findings and business case, decisions, cleaning log,
                 final presentation (PDF, PPTX), Screenshots/
demo/            index.html, the demo page (business-flow-improvement-demo.vercel.app)
.github/         the workflow that downloads and verifies the raw data
tools/           legacy files from an earlier version of this project (not used)
```

Some files in `docs/` and `tools/` come from earlier versions of this project (a simulated
pipeline and a Boston 311 analysis). They are kept for history and are not part of these results.
