# Decisions — BPI Challenge 2020, Domestic Declarations

Decisions that shape the analysis. Each one is applied in `analysis/02_baseline.py` and its results in
[`baseline-kpi-report.md`](baseline-kpi-report.md). Cleaning decisions are in
[`data-cleaning-log.md`](data-cleaning-log.md).

1. **2026-10-29 — Years.** Keep 2017 and 2018. Use 2018 as the main view for process-wide KPIs.
   Never present 2017 vs 2018 as a trend: 2017 covers two departments only. A case's year is the
   year of its first `Declaration SUBMITTED by EMPLOYEE` event; for never-submitted drafts, the
   year of its first event (Dutch local time). A case spanning New Year counts once, in that year.
   *Rationale (added 2026-10-29):* 2017 is structurally different, not just smaller. Counting
   submitted cases with at least one event by the role:
   - PRE_APPROVER: 681 cases in 2017, none in 2018.
   - "REJECTED by MISSING": 91 rejection events in 87 cases in 2017, none in 2018.
   - ADMINISTRATION: 18 cases in 2017, against 8,160 in 2018.
   - BUDGET OWNER: 4 cases in 2017, against 2,832 in 2018.

   Role-level KPIs are therefore 2018 only (decision 7).

2. **2026-10-29 — Complete cases and cycle time.** "Complete" means paid, or closed by the
   employee after a rejection. **Paid** means the case has a `Payment Handled` event, regardless
   of its submission path or of any event after the payment. **Closed by the employee after a
   rejection** means the case is not paid and its last event is
   `Declaration REJECTED by EMPLOYEE`, with no later submission. Cases whose last event is a
   rejection by another role, with no employee response, are incomplete. Cycle time is measured
   on paid cases only, from the first `Declaration SUBMITTED by EMPLOYEE` to `Payment Handled`.

3. **2026-10-29 — Zero amounts.** Cases with amount 0 stay in the process analysis and are
   excluded from money-based figures. Money is labelled "Amount (units as in source)" because the
   source states no currency. *Added 2026-10-29:* rejection rates by amount use **submitted**
   cases as the base, because zero-amount cases include never-submitted drafts. In 2018:
   - 253 of 253 submitted zero-amount cases (100%) were rejected at least once.
   - 819 of 7,907 submitted non-zero cases (10.36%) were.

   This is reported as "rejected at a higher rate; reason not established from the log alone".
   The log can't show whether a zero was entered on purpose or written as a default.

4. **2026-10-29 — Incomplete cases.** Cases without a clear end are excluded from duration
   measures (cycle time, transitions, wait times) and are reported as a finding, including the
   drafts that were saved and never submitted.

5. **2026-10-29 — ADMINISTRATION timing.** ADMINISTRATION's first step comes a median of 41
   seconds after submission. Treat it as a data limitation (system-recorded), not review time.
   *Added 2026-10-29 (2018 only, complete cases):*
   - 4,921 of 9,123 submission-to-ADMINISTRATION waits (53.94%) are under a minute.
   - The interquartile range is 6 to 259 seconds.
   - Timestamps are precise to the second: milliseconds are always .000 and the seconds field
     takes all 60 values, so the 41-second median is measured to the second.

   The report describes it as "ADMINISTRATION's approval is typically logged within a minute of
   submission, which suggests it's recorded automatically or in batches; it shouldn't be read as
   review effort", and keeps it in the limitations.

6. **2026-10-29 — Payments without final approval.** Cases 95149 and 90815 (paid without final
   approval) are reported as "control exceptions flagged for review: either a control failure or a
   data issue, not determinable from this data." *Added 2026-10-29:*
   - **A new check, `paid_without_submission`,** lists every paid case with no
     `Declaration SUBMITTED by EMPLOYEE` event. 95149 (2017) is the only one, and it was already
     flagged as `payment_without_final_approval`.
   - **Compliance is reported both ways:** 11 flag events (checks) in 9 distinct cases, out of
     10,044 cases with a `Payment Handled` event.
   - **Overlaps are counted once per table:**
     - 95149 is both a 2017 never-submitted draft and paid. Its status is paid; it is also one of
       the 35 drafts.
     - 90815 (2017) was paid and then ends with `Declaration REJECTED by EMPLOYEE`. Its status is
       paid, not closed by the employee.
     - No status total counts either case twice.

7. **2026-10-29 — Roles across years.** Roles differ between 2017 and 2018; never compare roles
   across years. *Added 2026-10-29:* role-level KPIs (wait times and rejections by role) are
   **2018 only**, and every table and CSV that uses roles says "2018 only" in its header.

8. **2026-10-29 — MISSING role.** Leave the "MISSING" role out of role charts, with a footnote
   explaining that it only ever rejects. *Added 2026-10-29:*
   - Report the total MISSING rejection events and the distinct cases rejected by MISSING, with
     "rate not meaningful" instead of a per-100 rate: the role only appears on rejections, so
     every case that reaches it is a rejection.
   - In 2018 it has 0 events. 2017's 91 events in 87 cases are given as data-quality context,
     not as a role KPI.

9. **2026-10-29 — Payments with no `Request Payment` step.** Report them next to the cycle-time
   median, with:
   - their count (n = 7, all 2018);
   - the median and range of days from final approval to payment (48.37; 37.37 to 284.27);
   - each case's year and amount.

   Describe them as something that "may indicate a separate or manual payment route", with no
   recommendation.

## Definitions (2026-10-29)

- **Year of a case:** the year of its first "Declaration SUBMITTED by EMPLOYEE" event; for
  never-submitted drafts, the year of the first event. A case spanning New Year counts once, in
  that year.
- **Paid:** the case has a "Payment Handled" event (at most one per case in this data). Cycle
  time ends at it.
- **Closed by the employee after a rejection:** the case's LAST event is
  "Declaration REJECTED by EMPLOYEE", with no later submission.
- **Rejected at least once:** one or more rejections by ADMINISTRATION, PRE_APPROVER, BUDGET
  OWNER, SUPERVISOR or MISSING. "Declaration REJECTED by EMPLOYEE" is the employee's response and
  is not counted as a rejection.
- **Final approval:** "Declaration FINAL_APPROVED by SUPERVISOR".
- **Durations:** fractional days from the timestamps, which carry their own time-zone offsets.
- **Percentiles:** linear interpolation (numpy's default method, the same as Excel
  `PERCENTILE.INC`). Round only in the report, not in the CSVs.
- **Money:** the case-level Amount column, "Amount (units as in source)". Report how many cases
  have a zero amount.
- **Reproducibility:** no randomness, fixed sort orders, and versions recorded. Two runs give
  byte-identical outputs.
