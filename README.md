# Business Flow Improvement

**Author:** Vimlesh Sonawane, Project Manager
**Status:** Self-initiated project — simulated scenario.
**What it is:** An end-to-end improvement of a business pipeline, from request intake to release, with the flow, the quality, and the reporting built as one system.

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
- A working demo in `demo/index.html`: an interactive pipeline — click a stage to see its problem, its fix, and its numbers; filter by phase; and see lead time, throughput, rework, and quality escapes move from baseline to control.

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
- `docs/role-angles.md` — how APM, PM, Product Operations, Business Operations, Process Improvement, and Customer Experience roles use this work
- `docs/resume-bullets.md` — repo docs only, for resume use with a Project label
- `docs/retrospective.md` — what worked, what did not, and what to do next
- `demo/index.html` — interactive pipeline demo

## Limits, stated plainly

- Simulated data. Twelve weeks, no holidays, no staffing changes, no seasonal variation.
- Phased interventions show a sequence and phase averages. They do not prove how much any single intervention caused on its own.
- Four control weeks show direction, not a proven new stable level. A real version would need a longer control period, a capacity and hours view, and a real cost view before any financial claim is made.
- This project does not cover physical safety operations, financial accounting, or content production craft. Those are out of scope.
