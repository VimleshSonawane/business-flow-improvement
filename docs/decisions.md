# Decisions

Decisions for the baseline KPIs ([baseline-kpi-report.md](baseline-kpi-report.md), built by `analysis/02_baseline.py`).

1. **2026-10-29: Keep 2017 and 2018.** Use 2018 as the main view for process-wide KPIs. Never present 2017 vs 2018 as a trend (2017 covers two departments only).
2. **2026-10-29: "Complete" = paid, or closed by the employee after a rejection.** Cycle time is measured on PAID cases only, from the first "Declaration SUBMITTED by EMPLOYEE" to "Payment Handled".
3. **2026-10-29: Zero-amount cases stay in process analysis** and are excluded from money-based figures.
4. **2026-10-29: Incomplete cases are excluded from duration measures** but reported as a finding, including the drafts saved and never submitted.

## Definitions

- **Year of a case:** the year of its first "Declaration SUBMITTED by EMPLOYEE" event; for never-submitted drafts, the year of the first event. A case spanning New Year counts once, in that year.
- **Paid:** the case has a "Payment Handled" event (at most one per case in this data). Cycle time ends at it.
- **Closed by the employee after a rejection:** the case's LAST event is "Declaration REJECTED by EMPLOYEE", with no later submission. Most "REJECTED by EMPLOYEE" events are followed by a resubmission, so an earlier one doesn't close the case.
- **Cases whose last event is a rejection by another role, with no employee response,** are incomplete, and are reported as their own finding.
- **Final approval:** "Declaration FINAL_APPROVED by SUPERVISOR".
- **Paid more than once:** more than one "Payment Handled" event in a case. Report the result even if it's 0.
- **Rejections by role:** one count per rejection event, including "REJECTED by MISSING" as its own row. "Reached that role" means the role has at least one event in the case.
- **Variants:** the raw activity sequence, without merging repeated activities. For events with identical timestamps, keep the file order.
- **Durations:** fractional days from the timestamps, which carry their own time-zone offsets.
- **Percentiles:** numpy's default linear method. Round only in the report, not in the CSVs.
- **Money:** the case-level Amount column. Report how many cases have a zero amount.
- **Reproducibility:** no randomness, fixed sort orders, and package versions recorded. At the end, run the script twice and report a checksum of each output file from both runs.

## How the script applies these

- **Year** uses the local time written in the source (each timestamp's own offset). It agrees with the `year` column in `data/processed/cases.csv` for all 10,500 cases.
- **A paid case is complete even if its last event is something else.** One case (declaration 90815, 2017) was paid and then ends with "Declaration REJECTED by EMPLOYEE"; it counts as paid.
- **Rejection rates count approver rejections only:** ADMINISTRATION, PRE_APPROVER, BUDGET OWNER, SUPERVISOR and MISSING. "Declaration REJECTED by EMPLOYEE" is the employee's response to a rejection, as in `analysis/01_clean.py`. It is shown as its own row in `rejections_by_role.csv`, marked as not counted.
- **Paid cases with no submission event** have no cycle time and are named in the report (1 case: declaration 95149, 2017).
