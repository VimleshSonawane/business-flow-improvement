# Playbook — runbooks and definition of done

A playbook is what makes a process repeatable. Without it, every request is handled a different way, quality depends on who happens to pick it up, and improvement cannot be measured because the process keeps changing.

## Definition of done, by stage

- **Intake done:** form complete, tier assigned, owner named.
- **Scoping done:** scope, out-of-scope, dependencies, and success check agreed and written down.
- **Build done:** work produced, self-checked against scope, and ready for quality review.
- **Quality done:** checked against the definition of done, defects logged, and either passed or returned with the reason named.
- **Release done:** release checklist complete, freeze respected, rollback plan ready, and release note written.

Work that does not meet its stage definition of done does not move to the next stage. That rule is what stops late rework.

## Runbook 1 — Launch

1. Confirm scope and definition of done from scoping.
2. Confirm assets, dependencies, and owners are ready.
3. Run the quality gate, including the early gate at scoping and the mid-build check.
4. Complete the release checklist.
5. Release, then log any escape the same day.

## Runbook 2 — Quality check

1. Check against the written definition of done, not against memory.
2. Log every defect with stage, cause, and fix.
3. Return work to the stage where the defect was created, with the reason, not just to the previous stage.
4. Track escapes separately from rework: rework is caught before release, an escape is caught after.

## Runbook 3 — Downtime and recovery

1. Name the owner and the impact: who is affected, and for how long.
2. Stop new work entering the affected stage until the block is cleared or worked around.
3. Communicate the status, the workaround, and the next update time to requesters.
4. After recovery, log the cause and add the fix to the playbook, so the same failure is handled faster next time.

## Runbook 4 — Daily flow review

Every day, the pipeline lead and stage owners review:

- What is aging: anything open more than 5 days in any stage.
- What is at a WIP limit, and what must be deferred or finished first.
- What is blocked, and who owns unblocking it.
- What was released yesterday, and whether any escape was logged.

The review is 15 minutes, from the pipeline data, not from status anecdotes.
