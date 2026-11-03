# Retrospective

## What went well
- Real data, verified: the BPI 2020 log matched the publisher's checksum, and every figure in the analysis traces to a script (analysis/01–03).
- Facts were kept separate from hypotheses on every map, slide and document, so every claim is defensible.
- The data changed the recommendation: I expected daily payment runs to fix the P90, but the scenarios showed approval reminders do.
- Checking a coincidence (two counts of 253) uncovered the zero-amount finding: 253 of 1,072 rejected claims had an amount of zero.

## What didn't go well
- Tool imports needed rework: a Smartsheet import lost columns, and another shifted every predecessor by one row.
- The map's arrow count (836 cases) and the report's total (948 Administration rejections, in 842 cases) looked like the same metric until a review caught it.
- Some Miro labels landed on the wrong arrows the first time.

## What I'd do differently
- Write a metric glossary (definition and denominator for every count) on day one.
- Check every import field by field before building on it.
- Interview real approvers to test the hypotheses the data can't answer, such as why claims are rejected.
- Model F4 (backup approver), which was left out of the scenarios.
