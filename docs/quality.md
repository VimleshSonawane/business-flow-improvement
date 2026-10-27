# Quality — gates, escapes, and why early quality wins

## The core quality problem

In baseline, quality was checked only at the end. A defect created in scoping or build was found in quality review, sent back, fixed, and re-checked. That loop is rework, and it is also delay: every loop adds waiting time in two stages.

Baseline quality numbers (simulated): rework 22%, escapes 14%, first-pass yield 78%.

## The fix: move quality earlier

Three gates, not one:

1. **Gate at scoping:** scope, definition of done, and dependencies are checked before build starts. A vague scope cannot enter build.
2. **Mid-build check:** a short check halfway through build, against the definition of done, so a wrong direction is caught early.
3. **Final quality review:** the full check before release, against the same definition of done.

Control quality numbers (simulated): rework 9%, escapes 5%, first-pass yield 91%.

## What counts as what

- **Rework:** work returned to an earlier stage before release.
- **Escape:** a defect found after release. Escapes are logged separately, because they affect members, guests, or partners directly, and because a falling rework rate with a rising escape rate would mean quality review is being skipped, not improved.
- **Root cause:** every escape is logged with the stage where the defect was created, not only the stage where it was found. That is how the early gates are judged.

## Quality and the business model

Fewer escapes means fewer fixes after release, fewer repeat contacts, and less rework eating into capacity. Quality is not a separate department in this project. It is a stage in the flow, with a gate, a log, and a review, like every other stage.
