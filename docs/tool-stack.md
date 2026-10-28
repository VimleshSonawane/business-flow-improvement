# Tool stack — how this project is shown, not just written

This project is presented in the tools a PM actually uses, not only in documents. Each tool has a distinct job, so they do not duplicate each other.

## The stack

| Tool | Job in this project | What a recruiter sees |
|---|---|---|
| Tableau Public | Interactive dashboard | Real Boston 311, 2024: monthly volume, volume by type, and on-time vs. overdue, filterable by month, type, and department |
| Miro | Process mapping | Real 311 flow: intake channels, triage by department, assignment, SLA check, closure, with Parking Enforcement and Pothole Repair highlighted as the overdue-heavy paths |
| Asana | Execution plan | Diagnostic and mapping plan for Parking Enforcement and Pothole Repair first, with owners, dependencies, and milestones |
| Smartsheet | Schedule, risk, and reporting | Gantt schedule for the same diagnostic and mapping plan, risk register, and a report view rolling up monthly volume and on-time rate |
| GitHub (this repo) | Source of truth | Real-data analysis, charter, flow analysis, playbook, quality, reporting, roadmap, risk mitigations, and PM plan |
| Portfolio demo | Hub | Links to the Tableau dashboard, Miro board, Asana project, and Smartsheet plan, plus the docs |

## Why Smartsheet is in, alongside Asana

Asana and Smartsheet are not doing the same job here, even though both show a schedule:

- **Asana** is for running the work: tasks, who owns them, what depends on what, and the Timeline view the team works from day to day.
- **Smartsheet** is for managing the plan: the Gantt with predecessors and durations, the risk register with owners and triggers, and a report view that rolls the project up for a sponsor or a business review.

In short: Asana shows how the team executes, Smartsheet shows how the PM controls schedule, risk, and reporting. Together with Tableau for measurement and Miro for mapping, that covers the full PM picture: map it, measure it, plan it, control it, and report it.

## Import files — real data version

- `tools/tableau-311-2024-by-month.csv` — requests by month, 2024 (total 306,756, reconciles exactly).
- `tools/tableau-311-2024-by-type.csv` — top 20 types by volume, 2024.
- `tools/tableau-311-2024-ontime.csv` — on-time vs. overdue for the five types where that split was verified, plus the all-types total (76.5% on time).
- `tools/asana-tasks.csv` — diagnostic and mapping plan, tasks, sections, owner roles, relative weeks, and dependencies. Steps are proposed, not completed work, except the diagnostic itself.
- `tools/smartsheet-plan.csv` — the same plan as a Smartsheet sheet, with durations, predecessors, owner roles, and status (Proposed, except the completed diagnostic). The risk register in `docs/risk-mitigation.md` can be imported as a second sheet.
- `docs/miro-board-structure.md` — Miro board frames to build, with the real 311 numbers to copy in. Miro has no CSV import for this; build it from this outline.

Weeks are relative (Week 1 to Week 12) in the Asana and Smartsheet files, so no calendar date is claimed. Set the start date when you import, and the durations and predecessors will place the rest of the plan.

Legacy file: `tools/tableau-pipeline-data.csv` is the earlier simulated 12-week pipeline. It is retained only for the simulated framework in the other docs, and is superseded for Tableau by the three 311 files above. Do not mix the simulated and real files in one dashboard.
