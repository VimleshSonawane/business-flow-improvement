# Flow analysis — understanding the problem before fixing it

## As-is value stream, baseline (simulated)

Lead time is split into waiting time and working time. This split is the key finding of the whole project.

| Stage | Waiting (days) | Working (days) | Total (days) |
|---|---:|---:|---:|
| 1. Intake and triage | 3.2 | 0.5 | 3.7 |
| 2. Scoping | 2.8 | 1.5 | 4.3 |
| 3. Build and preparation | 3.1 | 3.0 | 6.1 |
| 4. Quality review | 3.4 | 1.2 | 4.6 |
| 5. Release and delivery | 1.5 | 0.8 | 2.3 |
| **Total** | **14.0** | **7.0** | **21** |

Working time is about 7 days. Waiting time is about 14 days. The work was not slow. The waiting was.

## Where the waiting came from

- **Intake:** requests arrived without the information needed to start, so they waited for clarification, or started and stopped.
- **Scoping:** no priority rule, so urgent and low-value requests sat in the same queue, and decisions waited for whoever was available.
- **Build:** no WIP limit, so many items were open at once, and attention split across all of them.
- **Quality:** checked only at the end, so a problem found at Stage 4 sent work back to Stage 3, and sometimes to Stage 2.
- **Release:** last-minute changes with no freeze and no checklist, so release day became rework day.

## Pareto of flow problems (baseline, simulated)

These shares describe the causes of delay and rework in baseline, and they add to 100%.

| Cause | Share |
|---|---:|
| Incomplete intake information | 32% |
| Waiting for a decision, or unclear owner | 24% |
| Rework from late quality discovery | 21% |
| Too much work in progress, context switching | 13% |
| Last-minute release changes | 10% |

The top two causes together are 56%. That is why intake and ownership were fixed first, not last.

## The bottleneck

Build and preparation is the longest stage at 7.1 days, but it is not the only bottleneck. Quality review is the rework bottleneck: it is where late problems were discovered, and it is where work looped back. Intake is the entry bottleneck: a bad intake creates delay in every later stage.

A flow project that only speeds up build would not have fixed this pipeline. The fix had to cover intake, ownership, WIP, early quality, and release together, one change per cause, in phases.

## What was not assumed

- Demand was stable at about 35 a week, so this is a flow problem, not a demand surge problem.
- No staffing change was assumed. Throughput rises in the simulated case because waiting and rework fall, not because more people are added.
- No new tool was assumed. The fixes are checklists, owners, limits, gates, and a daily review — process changes, not software purchases.
