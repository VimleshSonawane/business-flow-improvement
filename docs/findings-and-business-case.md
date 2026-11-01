# Findings and business case — Approval Workflow Improvement

BPI Challenge 2020, Domestic Declarations. The findings use real 2018 data from
[`baseline-kpi-report.md`](baseline-kpi-report.md). The scenarios are what-if estimates from
`analysis/03_scenarios.py` (outputs in `data/outputs/scenarios.csv` and
`data/outputs/rework_extra_days.csv`). Decisions are in [`decisions.md`](decisions.md).

Dashboard (Tableau Public):
[Approval workflow baseline, BPI 2020 real data](https://public.tableau.com/app/profile/vimlesh.vilas.sonawane/viz/ApprovalWorkflowBaselineBPI2020realdata/Baselinedashboard)

## Findings (real data, 2018)

### 1. Payments are released in batches
- 99.66% of `Payment Handled` events fall on a Monday or Thursday (7,876 of 7,903 events in
  2018 cases, Dutch time).
- The wait from `Request Payment` to `Payment Handled` has a median of 3.21 days (P90 4.41;
  7,896 events, complete 2018 cases). It is the longest median wait of any step.

### 2. Approvals have long tails
Most approvals are quick, but a minority wait several days. P90 wait before each step,
complete 2018 cases:
- before a BUDGET OWNER action: 4.85 days (median 0.86; 2,874 events);
- before a SUPERVISOR action: 6.21 days (median 1.02; 8,121 events);
- before `Request Payment`: 6.83 days (median 1.06; 7,896 events).

### 3. Rework costs time, and Administration makes most rejections
- ADMINISTRATION made 948 of the 1,229 approver rejections in 2018 (11.62 per 100 of the 8,160
  submitted cases it handled).
- 13.14% of submitted claims were rejected at least once (1,072 of 8,160).
- Rejected claims take longer to pay: median cycle time 13.21 days for paid cases rejected at
  least once (815 cases) against 7.34 days for paid cases never rejected (7,088 cases).
- Supervisor rejections add the most time. Compared with paid cases never rejected (median 7.34
  days, 7,088 cases), the median cycle time of paid cases rejected by:
  - SUPERVISOR is 16.64 days, +9.30 days (168 cases);
  - BUDGET OWNER is 13.18 days, +5.85 days (44 cases);
  - ADMINISTRATION is 13.12 days, +5.78 days (632 cases).

  A case rejected by more than one role appears in each of its groups, so these are not additive
  (`data/outputs/rework_extra_days.csv`).

### 4. Control exceptions
- Cases 95149 and 90815 (both 2017) were paid without final approval. They are control
  exceptions flagged for review: either a control failure or a data issue, not determinable from
  this data (decision 6).
- 7 payments (all 2018) have no `Request Payment` event. They took a median of 48.37 days from
  final approval to payment (range 37.37 to 284.27), which may indicate a separate or manual
  payment route (decision 9).

Denominators for exceptions: 10,044 cases with a `Payment Handled` event, both years.

## Business case

All owners are role-played (charter: Sponsor Head of Finance; Process owner Travel
Administration lead; approvers; employees; Payments team).

### F1 — Daily payment runs
- **Cause targeted:** payment batching (finding 1). Payments run on Mondays and Thursdays, so an
  approved claim waits a median 3.21 days for the next run.
- **Expected effect (S1):** median cycle time 8.05 → 5.97 days; P90 20.25 → 16.91 days; share of
  paid cases over 14 days 20.99% → 14.22%; median payment wait 3.21 → 1.00 day.
- **Assumptions:** a daily run brings every `Request Payment` → `Payment Handled` wait down to at
  most 1 day; no other step changes.
- **Risks:** more payment runs may cost more in bank or processing fees and staff time; finance
  may batch on purpose (cash management, controls).
- **Cost/effort:** medium (process and scheduling change in the payment system; no new tool).
- **Owner:** Payments team, with the Head of Finance as sponsor.

### F2 — Claim checklist at submission
- **Cause targeted:** rework from ADMINISTRATION rejections (finding 3: 948 of 1,229 rejections).
- **Expected effect (S4):** rejection rate 13.14% → 10.17%; median cycle time 8.05 → 7.99 days;
  P90 20.25 → 20.04 days; share over 14 days 20.99% → 20.19%.
- **Assumptions:** the checklist prevents 40% of ADMINISTRATION rejections in paid cases
  (253 of 632, chosen at random with seed 42). This 40% is an assumption, not a measurement: the
  log does not record why a claim was rejected.
- **Risks:** the reasons for rejection are unknown, so a checklist may target the wrong errors;
  it adds a small step for every employee.
- **Cost/effort:** low (a form or checklist at submission).
- **Owner:** Travel Administration lead (process owner).

### F3 — Approval reminders after 3 days
- **Cause targeted:** approval tails (finding 2).
- **Expected effect (S2):** median cycle time 8.05 → 6.93 days; P90 20.25 → 12.59 days; share
  over 14 days 20.99% → 8.33%.
- **Assumptions:** a reminder after 3 days brings every wait before a BUDGET OWNER approval,
  SUPERVISOR approval and `Request Payment` down to at most 3 days; rejections keep their wait.
- **Risks:** reminder fatigue; approvers may approve faster with less care; approvers on leave
  need a delegate.
- **Cost/effort:** low to medium (automated reminder in the workflow system; delegation rules).
- **Owner:** Travel Administration lead, with budget owners and supervisors as approvers.

## Scenarios against the charter targets

2018 paid cases (7,903); rejection rate over 8,160 submitted 2018 cases. Source:
`data/outputs/scenarios.csv`.

| Scenario | Median cycle (d) | P90 cycle (d) | Paid cases over 14 d | Median payment wait (d) | Rejection rate | P90 ≤ 14 d | Rejections ≤ 8% | Payment wait ≤ 1 d |
|---|---:|---:|---:|---:|---:|:---:|:---:|:---:|
| Baseline (2018 as measured) | 8.05 | 20.25 | 20.99% (1,659) | 3.21 | 13.14% | no | no | no |
| S1 Daily payment runs (F1) | 5.97 | 16.91 | 14.22% (1,124) | 1.00 | 13.14% | no | no | **yes** |
| S2 Approval reminders (F3) | 6.93 | 12.59 | 8.33% (658) | 3.21 | 13.14% | **yes** | no | no |
| S3 = S1 + S2 | 4.75 | 9.01 | 5.62% (444) | 1.00 | 13.14% | **yes** | no | **yes** |
| S4 Fewer rejections (F2) | 7.99 | 20.04 | 20.19% (1,596) | 3.21 | 10.17% | no | no | no |

- **S3 meets two of three targets** (P90 and payment wait). No scenario meets the rejection
  target.
- **S1 meets the payment-wait target by construction:** the cap is 1 day, so the median becomes
  1.00 day.
- **The rejection target needs more than S4.** S4 leaves 830 of 8,160 submitted cases rejected
  (10.17%). Reaching 8% means at most 652 rejected cases, so about 178 more would have to be
  avoided. Rejections in cases that were never paid (for example the 253 zero-amount cases, all
  rejected) are outside S4's sample.

## What these numbers are and are not

- **They are what-if estimates on 2018 data.** Each scenario recomputes cycle times after
  changing only the stated waits and leaving every other step as recorded.
- **They are not results.** None of the fixes was implemented, and no before-and-after data
  exists.
- **They assume the fix fully works on the waits it targets** (caps of 1 and 3 days, a 40% cut in
  ADMINISTRATION rejections), and that nothing else changes. In practice, effects may be smaller,
  and fixes may interact.
- **Waits are recorded step completions.** They include queue time and working time, and the
  ADMINISTRATION step is system-recorded (decision 5).
