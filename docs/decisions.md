# Decisions — BPI Challenge 2020, Domestic Declarations

Decisions that shape the analysis. Each one is applied in `analysis/02_baseline.py` and its results in
[`baseline-kpi-report.md`](baseline-kpi-report.md). Cleaning decisions are in
[`data-cleaning-log.md`](data-cleaning-log.md).

1. **2026-10-29 — Years.** Keep 2017 and 2018. Use 2018 as the main view for process-wide KPIs.
   Never present 2017 vs 2018 as a trend: 2017 covers two departments only. A case's year is the
   year it started (first event, Dutch local time).

2. **2026-10-29 — Complete cases and cycle time.** "Complete" means paid (last event
   `Payment Handled`), or closed by the employee after a rejection (last event
   `Declaration REJECTED by EMPLOYEE`). Cycle time is measured on paid cases only, from the first
   `Declaration SUBMITTED by EMPLOYEE` to `Payment Handled`.

3. **2026-10-29 — Zero amounts.** Cases with amount 0 stay in the process analysis and are
   excluded from money-based figures. Money is labelled "Amount (units as in source)" because the
   source states no currency.

4. **2026-10-29 — Incomplete cases.** Cases without a clear end are excluded from duration
   measures (cycle time, transitions, wait times) and are reported as a finding, including the
   drafts that were saved and never submitted.
