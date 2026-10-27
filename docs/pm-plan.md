# Project management plan — this is a PM project, not a technology build

This project has no software to build, no code to write, and no tool to buy. Its work is project management work: planning, aligning stakeholders, governing scope and change, managing risk, and measuring whether the change held.

## What the PM owns here

- **Scope:** what is in the pipeline improvement, what is out, and what counts as done at each stage.
- **Stakeholders:** requesters, stage owners, quality reviewer, operations lead, and sponsor — who decides what, and when they are consulted.
- **Schedule:** a 12-week phased plan — 4 weeks baseline, 4 weeks improve, 4 weeks control — with a go / no-go decision at the move from Improve to Control.
- **Risk:** a risk log for the improvement itself, not only for the pipeline.
- **Communication:** a daily flow review, a weekly review, and a monthly business review, each with a fixed agenda.
- **Change control:** any change to a definition of done, a WIP limit, or a KPI definition goes through the sponsor, so the improvement stays measurable.
- **Quality:** gates, an escape log, and a control plan with triggers.
- **Business value:** time to value, capacity, cost to serve, and predictability, as set out in `docs/business-model.md`.

## Risk log for the improvement

| Risk | Impact if it happens | Mitigation in this plan |
|---|---|---|
| WIP limits are ignored under pressure | Queues grow again, lead time rises | Daily flow review holds the limit; deferral is a visible decision, not a silent queue |
| Intake gate is bypassed for urgent requests | Incomplete work re-enters the flow | P1 triage same day, so urgency is handled by priority, not by skipping the gate |
| Quality gates are skipped to meet a date | Escapes rise after release | Escapes are logged separately and reviewed weekly; a rising escape rate triggers a review before the next release |
| Improvement fades after the project ends | Old habits return | Control plan with triggers, and playbook ownership by the pipeline lead |

## Governance

- The sponsor approves scope changes and the move from Improve to Control.
- Stage owners approve work leaving their stage, against its definition of done.
- The pipeline lead owns the daily review and the control plan.
- No KPI definition, WIP limit, or definition of done changes without a recorded decision, so baseline, improve, and control remain comparable.

## Language used in this project, deliberately

Stages are business stages, not technology stages: intake, scoping, preparation, quality review, and delivery. "Build" in earlier drafts meant preparation of the work, not software engineering, and "release" meant delivery to members, guests, or partners, not a software deployment. The demo is a visual aid for the pipeline, not the deliverable itself. The deliverables are the charter, the flow analysis, the playbook, the reporting routine, and the control plan.
