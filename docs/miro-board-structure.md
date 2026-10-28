# Miro board structure — Boston 311 real flow

Build this board in Miro, in this order. Copy the numbers exactly; they are
from docs/real-data-analysis.md, not from the simulated pipeline.

## Frame 1 — The real headline

- Total 2024: 306,756 requests
- On time: 76.5% (234,564). Overdue: 23.5% (72,192)
- Closed in extract: 83.7%. Still open in extract: 16.3%
- Sticky note: "The headline hides a split. Two case types break the SLA."

## Frame 2 — Intake (where work comes from)

- Employee Generated: 129,573 (42.2%)
- Citizens Connect App: 79,749 (26.0%)
- Constituent Call: 54,474 (17.8%)
- City Worker App: 31,617 (10.3%)
- Self Service: 11,343 (3.7%)
- Sticky note: "Intake is not one channel. Fixing only the resident app
  misses the largest intake source."

## Frame 3 — Triage by department

- Public Works Department: 165,199 (53.9%)
- Transportation - Traffic Division: 81,063 (26.4%)
- Parks & Recreation: 19,715 (6.4%)
- Inspectional Services: 19,185 (6.3%)
- Mayor's 24 Hour Hotline: 13,114 (4.3%)
- Sticky note: "Public Works + Transportation = 80.3% of all work."

## Frame 4 — The flow, with the bottleneck highlighted

Boxes, left to right, with arrows:

Intake -> Triage by department -> Assignment / owner -> Work ->
SLA check -> Closure

Highlight in red, on the Work / SLA step:

- Parking Enforcement: 63,112 requests, 48.2% on time, 32,704 overdue
  (45.3% of ALL overdue cases)
- Request for Pothole Repair: 10,620 requests, 40.8% on time, 6,286 overdue
- Together: 54.0% of all overdue, from 24.0% of volume

In green, on the same step, for contrast:

- Requests for Street Cleaning: 90.7% on time
- Missed Trash/Recycling: 97.7% on time
- Improper Storage of Trash (Barrels): 99.4% on time

## Frame 5 — Monthly pressure

- Peak: August 30,713, September 29,852
- Low: December 20,594, February 21,265
- Sticky note: "Late summer is the pressure point, not winter."

## Frame 6 — What to do next (proposed, not claimed as done)

1. Measure stage times for Parking Enforcement and Pothole Repair.
2. Map their actual handoff paths.
3. Define SLA and a named owner per case type.
4. Propose one fix per cause found in the map.
5. Control with monthly volume and on-time reporting.

Sticky note, on every frame that proposes work: "Proposed next steps.
No improvement result is claimed from the 2024 diagnostic data."
