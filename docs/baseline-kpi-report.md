# Baseline KPI report (deliverable D3)

BPI Challenge 2020, Domestic Declarations (travel expense declarations at a university). This report **measures only**; it makes no recommendations. Decisions and definitions are in [decisions.md](decisions.md). Every number states its denominator and filter. **2018 is the main view.** 2017 is shown separately where useful and is **never a trend comparison**: 2017 covers two departments only (decision 1).

Built by `analysis/02_baseline.py` from `data/processed/events.csv` and `data/processed/cases.csv`. Python 3.13.17, pandas 3.0.5, numpy 2.5.3. Percentiles use numpy's default (linear) method. Durations are fractional days between timestamps; each timestamp carries its own UTC offset (+01:00 or +02:00, Dutch winter and summer time), so durations are exact across clock changes. Year and month use the local time written in the source.

**Input check:** 10,500 cases and 56,437 events, with 2,240 cases in 2017 and 8,260 in 2018 by the year definition. All match the raw log.

Money is **Amount (units as in source)**: the data states no currency.

## 1. KPI table (2018 main view)

| # | KPI | 2018 | Denominator and filter (2018) | 2017, separately (not a trend) |
|---|---|---|---|---|
| 0 | Cases paid | 95.7% (7,903) | 8,260 cases in 2018 | 95.6% of 2,240 |
| 0 | Cases closed by the employee after a rejection | 3.0% (248) | 8,260 cases in 2018 | 1.6% of 2,240 |
| 0 | Incomplete cases (excluded from durations) | 1.3% (109) | 8,260 cases in 2018 | 2.9% of 2,240 |
| 1 | Cycle time, first submission to Payment Handled: median | 8.0 d | 7,903 paid cases in 2018 with a submission | 7.1 d (n = 2,140) |
| 1 | Cycle time, first submission to Payment Handled: mean | 11.6 d | 7,903 paid cases in 2018 with a submission | 11.6 d (n = 2,140) |
| 1 | Cycle time, first submission to Payment Handled: P75 | 13.0 d | 7,903 paid cases in 2018 with a submission | 11.0 d (n = 2,140) |
| 1 | Cycle time, first submission to Payment Handled: P90 | 20.3 d | 7,903 paid cases in 2018 with a submission | 19.2 d (n = 2,140) |
| 2 | Stage timing (process map) | see section 2 | consecutive activity pairs in 2018 cases | `transitions.csv` |
| 3 | Wait until ADMINISTRATION acts: median / P90 | 0.0005 d (about 41 s) / 0.0221 d (about 32 min) | 9,133 events by this actor in 2018 cases, from the previous event | 27.1 d / 104.0 d (22 events) |
| 3 | Wait until BUDGET OWNER acts: median / P90 | 0.9 d / 4.9 d | 2,875 events by this actor in 2018 cases, from the previous event | 1.8 d / 6.2 d (4 events) |
| 3 | Wait until SUPERVISOR acts: median / P90 | 1.0 d / 6.2 d | 8,125 events by this actor in 2018 cases, from the previous event | 0.0018 d (about 3 min) / 3.1 d (2,300 events) |
| 3 | Wait until Request Payment (system) acts: median / P90 | 1.1 d / 6.8 d | 7,896 events by this actor in 2018 cases, from the previous event | 2.0 d / 7.8 d (2,144 events) |
| 3 | Wait until Payment Handled (system) acts: median / P90 | 3.2 d / 4.4 d | 7,903 events by this actor in 2018 cases, from the previous event | 3.3 d / 6.1 d (2,141 events) |
| 3 | Wait until PRE_APPROVER acts: median / P90 | no events | 0 events by this actor in 2018 cases, from the previous event | 0.0003 d (about 27 s) / 0.0161 d (about 23 min) (772 events) |
| 4 | Submitted cases rejected at least once (by an approver) | 13.1% (1,072) | 8,160 submitted cases in 2018 (never-submitted drafts excluded) | 10.4% of 2,205 |
| 4 | Rejections by ADMINISTRATION | 948 rejections; 11.6 per 100 cases | 8,160 2018 cases that reached ADMINISTRATION | 4; 22.2 per 100 of 18 |
| 4 | Rejections by SUPERVISOR | 222 rejections; 2.8 per 100 cases | 7,952 2018 cases that reached SUPERVISOR | 71; 3.2 per 100 of 2,196 |
| 4 | Rejections by BUDGET OWNER | 59 rejections; 2.1 per 100 cases | 2,832 2018 cases that reached BUDGET OWNER | 0; 0.0 per 100 of 4 |
| 4 | Rejections by PRE_APPROVER | role not present | 0 2018 cases that reached PRE_APPROVER | 86; 12.6 per 100 of 681 |
| 4 | Rejections by MISSING | role not present | 0 2018 cases that reached MISSING | 91; 104.6 per 100 of 87 |
| 4 | “REJECTED by EMPLOYEE” events (the employee's response, not counted as a rejection) | 1,204 | all 8,260 2018 cases | 161 |
| 5 | Resubmissions | 979 events | 8,160 submitted cases in 2018 | 187 events |
| 5 | Cases with 1 or more resubmissions | 10.4% (848) | 8,160 submitted cases in 2018 | 7.8% |
| 5 | Median cycle time, paid with / without an approver rejection | 13.2 d / 7.3 d | 815 / 7,088 paid cases in 2018 | 13.3 d / 7.0 d |
| 6 | Cases on the most common path | 55.8% (4,610) | 8,260 cases in 2018 | 62.1% |
| 6 | Cases on the top 10 paths / distinct paths | 97.8% / 63 paths | 8,260 cases in 2018 | 97.1% / 41 |
| 7 | Payments handled with no Request Payment | 7 | 7,903 2018 cases (paid) | 0 of 2,141 |
| 7 | Payments before final approval | 0 | 7,903 2018 cases (paid) | 2 of 2,141 |
| 7 | Requests for payment with no approval before them | 0 | 7,896 2018 cases (with a Request Payment) | 2 of 2,144 |
| 7 | Cases paid more than once | 0 | 7,903 2018 cases (paid) | 0 of 2,141 |
| 8 | Drafts saved and never submitted | 100 | 8,260 cases in 2018 | 35 of 2,240 |
| 9 | Submissions per month | 348 to 1,014 (see section 9) | submission events dated in 2018 | — |
| 10 | Median amount | 43.75 | 7,907 2018 cases with a non-zero amount (353 zero-amount cases excluded) | 41.52 (n = 2,147) |
| 10 | Total amount in cases rejected at least once | 134,645.22 of 721,736.60 (18.7%) | 819 of 7,907 2018 cases with a non-zero amount | 26,533.25 of 185,669.57 |

Notes: amounts are in units as in the source. “Reached a role” means the role has at least one event in the case. Waits are measured from the case's previous event to the event by that actor; a case's first event has no wait. PRE_APPROVER and the “MISSING” role occur only in 2017 cases; BUDGET OWNER occurs in 4 2017 cases. The “MISSING” role appears only on rejection events, so its rate per 100 cases reached can exceed 100. Cycle time excludes 1 paid case with no submission event (declaration 95149, year 2017).

## 2. Stage timing on the paths cases take (2018, top 15 by cases)

| From | To | Cases | Times it happened | Median | P90 |
|---|---|---|---|---|---|
| Declaration SUBMITTED by EMPLOYEE | Declaration APPROVED by ADMINISTRATION | 7,965 | 8,184 | 0.0004 d (about 37 s) | 0.0159 d (about 23 min) |
| Declaration FINAL_APPROVED by SUPERVISOR | Request Payment | 7,896 | 7,896 | 1.1 d | 6.8 d |
| Request Payment | Payment Handled | 7,896 | 7,896 | 3.2 d | 4.4 d |
| Declaration APPROVED by ADMINISTRATION | Declaration FINAL_APPROVED by SUPERVISOR | 5,119 | 5,119 | 0.9 d | 4.8 d |
| Declaration APPROVED by ADMINISTRATION | Declaration APPROVED by BUDGET OWNER | 2,803 | 2,816 | 0.9 d | 4.9 d |
| Declaration APPROVED by BUDGET OWNER | Declaration FINAL_APPROVED by SUPERVISOR | 2,784 | 2,784 | 1.9 d | 6.7 d |
| Declaration REJECTED by EMPLOYEE | Declaration SUBMITTED by EMPLOYEE | 842 | 956 | 0.2 d | 11.3 d |
| Declaration SUBMITTED by EMPLOYEE | Declaration REJECTED by ADMINISTRATION | 842 | 948 | 0.0011 d (about 2 min) | 1.0 d |
| Declaration REJECTED by ADMINISTRATION | Declaration REJECTED by EMPLOYEE | 833 | 924 | 0.9 d | 5.0 d |
| Declaration REJECTED by SUPERVISOR | Declaration REJECTED by EMPLOYEE | 211 | 216 | 1.0 d | 7.6 d |
| Declaration APPROVED by ADMINISTRATION | Declaration REJECTED by SUPERVISOR | 186 | 190 | 0.9 d | 4.9 d |
| Declaration APPROVED by ADMINISTRATION | Declaration REJECTED by BUDGET OWNER | 58 | 59 | 0.4 d | 3.3 d |
| Declaration REJECTED by BUDGET OWNER | Declaration REJECTED by EMPLOYEE | 57 | 58 | 1.0 d | 4.9 d |
| Declaration APPROVED by BUDGET OWNER | Declaration REJECTED by SUPERVISOR | 32 | 32 | 4.0 d | 6.8 d |
| Declaration REJECTED by ADMINISTRATION | Declaration SUBMITTED by EMPLOYEE | 14 | 19 | 0.9 d | 6.2 d |

Denominator: cases in 2018 that took that step. All pairs, for both years, are in `transitions.csv` (the process-map table).

## 6. Top paths (2018)

| Rank | Cases | % of cases | Steps | Path |
|---|---|---|---|---|
| 1 | 4,610 | 55.8% | 5 | Declaration SUBMITTED by EMPLOYEE > Declaration APPROVED by ADMINISTRATION > Declaration FINAL_APPROVED by SUPERVISOR > Request Payment > Payment Handled |
| 2 | 2,472 | 29.9% | 6 | Declaration SUBMITTED by EMPLOYEE > Declaration APPROVED by ADMINISTRATION > Declaration APPROVED by BUDGET OWNER > Declaration FINAL_APPROVED by SUPERVISOR > Request Payment > Payment Handled |
| 3 | 344 | 4.2% | 8 | Declaration SUBMITTED by EMPLOYEE > Declaration REJECTED by ADMINISTRATION > Declaration REJECTED by EMPLOYEE > Declaration SUBMITTED by EMPLOYEE > Declaration APPROVED by ADMINISTRATION > Declaration FINAL_APPROVED by SUPERVISOR > Request Payment > Payment Handled |
| 4 | 186 | 2.3% | 9 | Declaration SUBMITTED by EMPLOYEE > Declaration REJECTED by ADMINISTRATION > Declaration REJECTED by EMPLOYEE > Declaration SUBMITTED by EMPLOYEE > Declaration APPROVED by ADMINISTRATION > Declaration APPROVED by BUDGET OWNER > Declaration FINAL_APPROVED by SUPERVISOR > Request Payment > Payment Handled |
| 5 | 174 | 2.1% | 3 | Declaration SUBMITTED by EMPLOYEE > Declaration REJECTED by ADMINISTRATION > Declaration REJECTED by EMPLOYEE |
| 6 | 100 | 1.2% | 1 | Declaration SAVED by EMPLOYEE |
| 7 | 77 | 0.9% | 9 | Declaration SUBMITTED by EMPLOYEE > Declaration APPROVED by ADMINISTRATION > Declaration REJECTED by SUPERVISOR > Declaration REJECTED by EMPLOYEE > Declaration SUBMITTED by EMPLOYEE > Declaration APPROVED by ADMINISTRATION > Declaration FINAL_APPROVED by SUPERVISOR > Request Payment > Payment Handled |
| 8 | 49 | 0.6% | 10 | Declaration SUBMITTED by EMPLOYEE > Declaration APPROVED by ADMINISTRATION > Declaration REJECTED by SUPERVISOR > Declaration REJECTED by EMPLOYEE > Declaration SUBMITTED by EMPLOYEE > Declaration APPROVED by ADMINISTRATION > Declaration APPROVED by BUDGET OWNER > Declaration FINAL_APPROVED by SUPERVISOR > Request Payment > Payment Handled |
| 9 | 36 | 0.4% | 11 | Declaration SUBMITTED by EMPLOYEE > Declaration REJECTED by ADMINISTRATION > Declaration REJECTED by EMPLOYEE > Declaration SUBMITTED by EMPLOYEE > Declaration REJECTED by ADMINISTRATION > Declaration REJECTED by EMPLOYEE > Declaration SUBMITTED by EMPLOYEE > Declaration APPROVED by ADMINISTRATION > Declaration FINAL_APPROVED by SUPERVISOR > Request Payment > Payment Handled |
| 10 | 31 | 0.4% | 4 | Declaration SUBMITTED by EMPLOYEE > Declaration APPROVED by ADMINISTRATION > Declaration REJECTED by SUPERVISOR > Declaration REJECTED by EMPLOYEE |

Denominator: all 8,260 cases in 2018, including drafts and incomplete cases. 2017's top 10 is in `variants_top10.csv`.

## 7. Compliance checks (both years; case ids)

| Check | Cases | Case ids |
|---|---|---|
| Payment Handled with no Request Payment | 7 of 10,044 | declaration 115669, declaration 124535, declaration 136996, declaration 138147, declaration 138710, declaration 141310, declaration 142992 |
| Payment before final approval | 2 of 10,044 | declaration 90815, declaration 95149 |
| Request Payment with no approval before it | 2 of 10,040 | declaration 90815, declaration 95149 |
| Paid more than once | 0 of 10,044 | none |

## 9. Submissions per month (2018, local time)

| Month | Submission events | First submissions | Resubmissions |
|---|---|---|---|
| 2018-01 | 593 | 551 | 42 |
| 2018-02 | 717 | 658 | 59 |
| 2018-03 | 743 | 681 | 62 |
| 2018-04 | 814 | 747 | 67 |
| 2018-05 | 716 | 629 | 87 |
| 2018-06 | 1,014 | 904 | 110 |
| 2018-07 | 819 | 672 | 147 |
| 2018-08 | 348 | 294 | 54 |
| 2018-09 | 716 | 635 | 81 |
| 2018-10 | 879 | 791 | 88 |
| 2018-11 | 921 | 840 | 81 |
| 2018-12 | 869 | 758 | 111 |

Workload context only. Filter: “Declaration SUBMITTED by EMPLOYEE” events dated in 2018 (some belong to 2017 cases that were resubmitted).

## Findings

1. **A paid declaration takes a median of 8.0 d from first submission to payment, and 1 in 10 takes more than 20.3 d.** The mean (11.6 d) is well above the median because of a long tail: 108 of the 7,903 paid 2018 cases took over 60 days. Denominator: 7,903 paid 2018 cases with a submission.
2. **About 1 in 8 submitted declarations is rejected at least once (13.1%, 1,072 of 8,160 submitted 2018 cases), and ADMINISTRATION makes most of the rejections:** 948 of 1,229 approver rejections, 11.6 per 100 cases it handled, against 2.8 for SUPERVISOR and 2.1 for BUDGET OWNER.
3. **Paid cases with a rejection took longer:** paid 2018 cases with an approver rejection took a median of 13.2 d from first submission to payment, against 7.3 d for those without one (815 and 7,088 paid cases). The rejected cases also hold 18.7% of the 2018 amount (134,645.22 of 721,736.60 units as in source, zero amounts excluded).
4. **ADMINISTRATION's step is almost instant; the waits are at the supervisor, budget owner and payment steps.** In 2018, ADMINISTRATION acted a median of 0.0005 d (about 41 s) after the previous event (P90 0.0221 d (about 32 min)). SUPERVISOR waited a median of 1.0 d (P90 6.2 d), BUDGET OWNER 0.9 d (P90 4.9 d), Request Payment came 1.1 d after the previous step (P90 6.8 d), and Payment Handled 3.2 d after that (P90 4.4 d).
5. **The process is highly standard.** 55.8% of 8,260 2018 cases follow one 5-step path (submitted, approved by administration, final approval by supervisor, payment requested, paid); the top two paths cover 85.7% and the top 10 cover 97.8%.
6. **About 1 in 10 submitted declarations was resubmitted:** 10.4% of submitted 2018 cases (848 of 8,160) were resubmitted at least once, with 979 resubmissions in total.
7. **Compliance checks flagged 9 of 10,044 paid cases (both years), and found no double payments:** 7 paid 2018 cases went straight from final approval to payment with no Request Payment event (median 48.4 d between them); in 2017, 2 cases were paid with no final approval at all (declaration 90815, declaration 95149). No case was paid more than once (0 of 10,044 paid cases).
8. **Incomplete cases are few, and mostly unsubmitted drafts.** In 2018, 109 of 8,260 cases (1.3%) are incomplete: 100 drafts saved and never submitted, and 9 whose last event is a rejection by another role with no employee response. In 2017, 30 cases end on a rejection with no response, all “REJECTED by MISSING” (the approver's role wasn't recorded).

## Limitations

- **2017 is not comparable with 2018.** 2017 covers two departments only, and its roles differ: PRE_APPROVER and the “MISSING” role appear only in 2017, ADMINISTRATION appears in only 18 2017 cases, and BUDGET OWNER in 4. Side-by-side numbers are context, not a trend.
- **The log has no department, employee or approver identity.** Resources are only “STAFF MEMBER” or “SYSTEM”, so waits and rejections can't be broken down by person or team, and workload per approver can't be measured.
- **Waits are measured between recorded events.** Time spent before the first submission, and any work that isn't logged, is invisible. A near-zero wait (as for ADMINISTRATION) may reflect how events are recorded rather than how long people take.
- **“REJECTED by EMPLOYEE” is read as the employee's response to a rejection,** not a rejection: in most cases it directly follows an approver rejection. It is shown separately and not counted in rejection rates.
- **End of the log:** the log runs until 2019-06-17, months after the last 2018 submission, so few 2018 cases are cut off by the end of the data. The 9 2018 cases that end on a rejection with no employee response last moved between 2018-12-19 and 2019-04-22; the never-submitted drafts are spread across the year.
- **Amounts were anonymised by the publisher** and carry no currency. They are used only for medians and totals, never converted.
- **The data is from a public benchmark (BPI Challenge 2020)**; findings describe this log, not any current process.

## Files

`data/outputs/tableau/`: `kpi_summary.csv` (every KPI with year, filter, denominator, numerator and unrounded value), `cycle_time_by_case.csv`, `transitions.csv` (process map), `role_wait_times.csv`, `rejections_by_role.csv`, `variants_top10.csv`, `monthly_volume.csv`, `compliance_flags.csv`. Values in the CSVs are not rounded.
