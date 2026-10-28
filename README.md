# Business Flow Improvement

**Author:** Vimlesh Sonawane, Project Manager
**Status:** Self-initiated project — real public-data diagnostic, plus a proposed improvement framework.
**What it is:** An end-to-end improvement of a business pipeline, from request intake to release, with the flow, the quality, and the reporting built as one system.

## Real-data update — Boston 311, 2024

This project now has two layers, kept separate on purpose:

1. **Real diagnostic analysis** in `docs/real-data-analysis.md`: City of Boston
   311 Service Requests, 2024, 306,756 requests, from Analyze Boston.
   On time 76.5%, overdue 23.5%. Parking Enforcement (63,112 requests,
   48.2% on time) and Pothole Repair (10,620 requests, 40.8% on time)
   together account for 54.0% of all overdue cases, from 24.0% of volume.
   Monthly volume peaks in August (30,713) and September (29,852).
2. **Proposed improvement framework** in the other docs: the simulated
   pipeline, its 12-week plan, and its stage times are a proposal for how
   to measure and fix the flow found in layer 1. They are NOT results
   measured from the 311 data, and no improvement result is claimed
   from the diagnostic alone.

The tool files in `tools/` are built from layer 1: Tableau CSVs from the
real 2024 counts, a Smartsheet / Asana plan for diagnosing and mapping
Parking Enforcement and Pothole Repair first, and a Miro board structure
with the real numbers to copy in.

## What kind of project this is

This is a project management project, not a technology build. There is no software to build and no tool to buy here. The work is PM work: charter and scope, stakeholder alignment, a phased schedule, risk and change control, a playbook, quality gates, and a control plan that shows whether the improvement held. See `docs/pm-plan.md` for the full PM plan, including stakeholder roles, governance, and the risk log for the improvement itself. The demo is only a visual aid for the pipeline; the deliverables are the plan, the playbook, and the reporting routine.

## The problem I analysed

In the simulated scenario, a subscription product and live experience operation was receiving about 35 requests a week — new features, content and experience improvements, partner requests, and member and guest experience fixes — and completing about 28 a week.

Work was not failing because people were slow. It was failing because the flow was broken:

- Requests arrived incomplete, so work started, stopped, and started again.
- No one owned a stage, so work waited for a decision.
- Too much work was in progress at once, so everything moved slowly.
- Quality was checked only at the end, so problems were found late and sent back.
- Releases had last-minute changes, so delivery slipped.

The result in baseline (Weeks 1–4, simulated): lead time about **21 days**, rework **22%**, quality escapes **14%**, and a backlog that grew from 84 to 110.

## What I created

- A value-stream map of the pipeline, stage by stage, with waiting time separated from working time.
- An intake and prioritisation system: a completeness checklist, priority tiers, and a triage rule.
- A playbook: runbooks for intake, build, quality, release, and recovery, with a definition of done for each stage.
- A pipeline model: WIP limits, a daily flow review, and a quality gate moved earlier in the flow.
- A reporting system: weekly pipeline metrics, a stage bottleneck view, and a business review template.
- Proper process mapping: as-is and to-be flowcharts, a swimlane view, and a diagnostic order — measure, split waiting from working time, rank causes, map, plan, fix, control — in `docs/process-maps.md`.
- A roadmap and schedule: phased roadmap with milestones M1, M2, M3, a 12-week Gantt schedule, and dependencies, in `docs/roadmap.md`.
- Risk mitigations with level, owner, and trigger for each risk, in `docs/risk-mitigation.md`.
- A working demo in `demo/index.html`: an interactive pipeline — a visual flow map with the rework loop, charts for lead time, demand vs. completed, and rework/escapes, a roadmap, a Gantt schedule, a risk table, click a stage to see its problem, its fix, and its numbers, and filter by phase.

## The result, in the simulated case

| Metric | Baseline (W1–4) | Improve (W5–8) | Control (W9–12) |
|---|---|---|---|
| Lead time | about 21 days | about 16 days | about 12 days |
| Throughput | about 28 / week | about 37 / week | about 39 / week |
| Rework | 22% | about 14% | 9% |
| Quality escapes | 14% | about 9% | 5% |
| Backlog at phase end | 110 | 101 | 84 |
| Waiting time in lead time | 14 days | about 9 days | 5 days |
| Working time in lead time | about 7 days | about 7 days | about 7 days |

The working time did not change. The waiting time did. That is the whole point of a flow project: the work itself was not slow, the waiting between stages was.

## How this improves a business model

This is covered in full in `docs/business-model.md`. In short, a faster, cleaner pipeline means:

- **Faster time to value:** improvements reach members and guests in 12 days instead of 21.
- **More capacity without more headcount:** throughput rises from 28 to about 39 a week in the simulated case, at the same simulated team size.
- **Lower cost to serve:** rework falls from 22% to 9%, so less work is done twice.
- **Better quality at release:** escapes fall from 14% to 5%, so fewer fixes are needed after release.
- **Predictability:** lead time narrows from a baseline range of about 18–24 days to about 10–14 days in control, so planning and promises become reliable.

## How different roles use this project

`docs/role-angles.md` explains, for each role, which part of this project to lead with. The roles covered are Associate / Assistant Product Manager (APM), Product Manager, Product Operations, Business Operations, Process Improvement / Continuous Improvement, and Customer Experience. The data, the flow, and the limits are the same in every angle.

## Files

- `docs/charter.md` — improvement brief, goal, scope, stakeholders, success criteria
- `docs/flow-analysis.md` — as-is value-stream map, waste, Pareto, and the bottleneck
- `docs/pipeline.md` — stages, WIP, lead time, throughput, and the full 12-week table
- `docs/intake-and-prioritisation.md` — intake form, completeness checklist, priority tiers, triage
- `docs/playbook.md` — runbooks and definition of done for every stage
- `docs/quality.md` — quality gates, escapes, and the early-quality fix
- `docs/reporting.md` — KPI definitions, weekly review, and business review template
- `docs/improvement-plan.md` — phased plan, one change per cause
- `docs/business-model.md` — how flow improvement changes the business model
- `docs/process-maps.md` — as-is and to-be flowcharts, swimlane, diagnostic order
- `docs/roadmap.md` — roadmap, Gantt schedule, dependencies, milestone success criteria
- `docs/risk-mitigation.md` — risk matrix with mitigation, owner, and trigger
- `docs/pm-plan.md` — PM plan: scope, stakeholders, schedule, risk, change control, governance
- `docs/role-angles.md` — how APM, PM, Product Operations, Business Operations, Process Improvement, and Customer Experience roles use this work
- `docs/resume-bullets.md` — repo docs only, for resume use with a Project label
- `docs/retrospective.md` — what worked, what did not, and what to do next
- `docs/real-data-analysis.md` — Boston 311, 2024: real diagnostic, source, findings, and limits
- `docs/tool-stack.md` — Tableau, Miro, Asana, and Smartsheet: what each tool shows, and its import files
- `docs/miro-board-structure.md` — Miro board frames with the real 311 numbers to copy in
- `tools/tableau-311-2024-by-month.csv`, `tools/tableau-311-2024-by-type.csv`, `tools/tableau-311-2024-ontime.csv` — real 2024 counts for Tableau Public
- `tools/smartsheet-plan.csv`, `tools/asana-tasks.csv` — real-data diagnostic and mapping plan, proposed steps, not completed work
- `demo/index.html` — interactive pipeline demo

## Limits, stated plainly

- Simulated data. Twelve weeks, no holidays, no staffing changes, no seasonal variation.
- Phased interventions show a sequence and phase averages. They do not prove how much any single intervention caused on its own.
- Four control weeks show direction, not a proven new stable level. A real version would need a longer control period, a capacity and hours view, and a real cost view before any financial claim is made.
- This project does not cover physical safety operations, financial accounting, or content production craft. Those are out of scope.
