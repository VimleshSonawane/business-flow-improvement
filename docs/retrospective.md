# Retrospective

## What worked

- Splitting lead time into waiting and working time. That one split changed the whole project: it turned a vague "we are slow" problem into a specific "we wait too long between stages" problem, with a fix for each wait.
- Phasing by Pareto order. Fixing intake and ownership first gave the largest early movement, which made the later, smaller fixes easier to justify.
- Moving quality earlier. The scoping gate and mid-build check did more for rework than any amount of final checking could, because they caught problems where they were created.

## What did not work, or was hard

- WIP limits are easy to write and hard to hold. When demand is high, the pressure is always to start more work, not to finish work first. The daily flow review is the routine that holds the limit, and without it the limit would drift.
- A pipeline with five stages and five owners can become five silos. The daily review and the shared definition of done are what keep it one pipeline, not five queues.
- Lead time range is a better planning tool than lead time average, but it is harder to explain. The average is what people ask for first, and the range is what they actually need.

## What to do next, in a real version

- Run control for longer than four weeks, and add a capacity and hours view before any staffing or financial decision.
- Add a real cost view, so the business-model analysis can move from direction to figures.
- Test the intake gate and WIP limits under a demand surge, not only under stable demand, because surge behaviour is where flow systems usually break.
- Keep the playbook as a living document: every escape and every recovery should add or change a runbook step, or the playbook will go stale.
