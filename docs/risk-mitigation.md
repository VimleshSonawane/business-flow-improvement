# Risk mitigations

Risk mitigation in this project is not a list at the back of a document. Each risk has a level, a mitigation that is already in the plan, an owner, and a trigger that starts the mitigation. If there is no trigger, the mitigation is just a hope.

## Risk matrix

| Risk | Likelihood | Impact | Level | Mitigation | Owner | Trigger |
|---|---|---|---|---|---|---|
| WIP limits ignored under pressure | High | High | High | Daily flow review holds the limit; deferral is a visible decision, not a silent queue | Pipeline lead | Any stage over its WIP limit for 2 days |
| Intake gate bypassed for urgent work | High | High | High | P1 triage same day, so urgency is handled by priority, not by skipping the gate | Pipeline lead | Incomplete request enters scoping |
| Quality gates skipped to meet a date | Medium | High | Medium | Escapes logged separately and reviewed weekly; a rising escape rate triggers a review before the next delivery | Quality reviewer | Escapes rise for 2 consecutive weeks |
| Improvement fades after the project ends | Medium | High | Medium | Control plan with triggers; playbook owned by the pipeline lead | Pipeline lead | Lead time over 14 days or rework over 10% for 2 weeks |
| Demand surge breaks the flow | Low | High | Low | Priority tiers and WIP limits force a deferral decision instead of silent queue growth | Operations lead | Demand over 40 a week for 2 weeks |
| Scope creep re-enters after scoping | Medium | Medium | Medium | Definition of done and out-of-scope agreed in writing; changes go through the sponsor | Sponsor | Scope change requested after scoping gate |

## How mitigations are reviewed

- Risks are reviewed in the weekly review, not only at project start.
- A triggered risk is logged with the date, the action taken, and whether the playbook changed as a result.
- A mitigation that was never triggered is still kept in the plan, because the absence of a trigger in 12 simulated weeks does not mean the risk is gone.
- New risks found in control are added to this matrix, with the same columns, so the matrix stays the single risk record for the project.
