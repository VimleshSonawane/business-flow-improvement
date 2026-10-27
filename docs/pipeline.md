# Pipeline — stages, WIP, lead time, and the 12-week table

## The five stages

1. **Intake and triage** — a request enters, is checked for completeness, and is given a priority tier.
2. **Scoping** — scope, owner, and definition of done are agreed before build starts.
3. **Build and preparation** — the work is produced or prepared.
4. **Quality review** — quality is checked against the definition of done, with an early gate at scoping and a mid-build check added in the improvement phase.
5. **Release and delivery** — the work is released under a checklist, with a freeze window and a rollback plan.

Post-release review is a sixth step, not a stage: every release is reviewed in the weekly business review, and escapes are logged.

## WIP limits, after improvement

WIP limits are the control that stops everything being open at once.

| Stage | WIP limit |
|---|---:|
| Intake and triage | 10 |
| Scoping | 8 |
| Build and preparation | 12 |
| Quality review | 8 |
| Release and delivery | 5 |

No new work enters a stage that is at its limit. That rule forces the conversation about priority, instead of letting a queue grow silently.

## Stage times, baseline vs. control (days, simulated)

| Stage | Baseline waiting + working | Control waiting + working |
|---|---|---|
| Intake and triage | 3.2 + 0.5 | 0.8 + 0.5 |
| Scoping | 2.8 + 1.5 | 1.0 + 1.5 |
| Build and preparation | 3.1 + 3.0 | 1.8 + 3.0 |
| Quality review | 3.4 + 1.2 | 0.9 + 1.2 |
| Release and delivery | 1.5 + 0.8 | 0.5 + 0.8 |
| **Total** | **14 + 7 = 21** | **5 + 7 = 12** |

Working time is unchanged in every stage. Waiting time falls in every stage. That is the flow improvement, stated as plainly as possible.

## Weekly pipeline table (simulated)

Backlog each week = previous backlog + demand − completed. Starting backlog before Week 1 is 84.

| Week | Phase | Demand | Completed | Backlog | Lead (days) | Rework | Escapes |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | Baseline | 34 | 27 | 91 | 22 | 24% | 15% |
| 2 | Baseline | 36 | 28 | 99 | 21 | 22% | 14% |
| 3 | Baseline | 33 | 29 | 103 | 20 | 21% | 13% |
| 4 | Baseline | 35 | 28 | 110 | 21 | 21% | 14% |
| 5 | Improve | 34 | 36 | 108 | 18 | 18% | 11% |
| 6 | Improve | 35 | 37 | 106 | 16 | 15% | 9% |
| 7 | Improve | 33 | 36 | 103 | 15 | 13% | 8% |
| 8 | Improve | 36 | 38 | 101 | 14 | 11% | 7% |
| 9 | Control | 34 | 38 | 97 | 13 | 10% | 6% |
| 10 | Control | 35 | 39 | 93 | 12 | 9% | 5% |
| 11 | Control | 33 | 38 | 88 | 12 | 9% | 5% |
| 12 | Control | 36 | 40 | 84 | 11 | 8% | 4% |

Phase averages: baseline lead about 21 days, rework 22%, escapes 14%, throughput about 28 a week; improve lead about 16 days, rework about 14%, escapes about 9%, throughput about 37 a week; control lead about 12 days, rework 9%, escapes 5%, throughput about 39 a week. Lead time range narrows from about 18–24 days in baseline to about 10–14 days in control.

## Definitions

- **Lead time:** days from intake accepted to release, including waiting.
- **Throughput:** requests completed per week.
- **Rework:** share of completed requests that return to an earlier stage after quality review or after release.
- **Quality escape:** a request released with a defect or error found after release, as a share of releases.
- **First-pass yield:** 100% minus rework. Baseline 78%, control 91%.
- **Flow efficiency:** working time divided by lead time. Baseline about 33% (7 of 21 days), control about 58% (7 of 12 days).
