"""What-if scenarios for BPI Challenge 2020 Domestic Declarations (2018 paid cases).

Reads data/processed/events.csv and data/processed/cases.csv and writes:
  data/outputs/scenarios.csv            baseline and scenarios S1-S4
  data/outputs/rework_extra_days.csv    extra cycle time of paid cases by rejecting role

Definitions are the same as analysis/02_baseline.py: a case's year is the year of its first
"Declaration SUBMITTED by EMPLOYEE" (local time as written in the source); paid means the case
has a "Payment Handled" event; cycle time runs from the first SUBMITTED to Payment Handled.

Each scenario recomputes per-case cycle time as the sum of the waits between consecutive
events from the first SUBMITTED to Payment Handled, after changing only the stated waits:
  S1 Daily payment runs (F1): Request Payment -> Payment Handled capped at 1.0 day.
  S2 Approval reminders (F3): the wait before each BUDGET OWNER approval, SUPERVISOR approval
     and Request Payment capped at 3.0 days.
  S3 S1 and S2 together.
  S4 Fewer rejections (F2): for a random 40% (assumption; seed 42) of paid cases rejected by
     ADMINISTRATION, the time from each ADMINISTRATION rejection to the next SUBMITTED is removed.

Scenarios are what-if estimates on 2018 data, not results. Standard library only; the random
sample uses a fixed seed and a fixed case order, so two runs give byte-identical outputs.

Run from anywhere:  python3 analysis/03_scenarios.py
"""

import collections
import csv
import os
import random
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS_CSV = os.path.join(ROOT, "data", "processed", "events.csv")
CASES_CSV = os.path.join(ROOT, "data", "processed", "cases.csv")
OUT_DIR = os.path.join(ROOT, "data", "outputs")

YEAR = "2018"
EXPECT_PAID, EXPECT_SUBMITTED = 7903, 8160  # docs/baseline-kpi-report.md, 2018

SUBMIT = "Declaration SUBMITTED by EMPLOYEE"
REQUEST = "Request Payment"
PAID = "Payment Handled"
EMP_REJECT = "Declaration REJECTED by EMPLOYEE"
ADMIN_REJECT = "Declaration REJECTED by ADMINISTRATION"

PAYMENT_CAP = 1.0     # S1: days from Request Payment to Payment Handled
REMINDER_CAP = 3.0    # S2: days before a BUDGET OWNER / SUPERVISOR approval or Request Payment
S4_SHARE = 0.40       # S4 assumption: share of ADMINISTRATION-rejected paid cases avoided
SEED = 42
OVER_DAYS = 14.0      # charter target: P90 cycle time <= 14 days


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def pct_point(values, p):
    """Linear interpolation between closest ranks, as in analysis/02_baseline.py."""
    v = sorted(values)
    if not v:
        return None
    k = (len(v) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


# S2 caps the wait before these steps. Rejections are not approvals and keep their wait.
REMINDER_STEPS = {"Declaration APPROVED by BUDGET OWNER", "Declaration FINAL_APPROVED by SUPERVISOR",
                  REQUEST}


def main():
    cases = []
    with open(CASES_CSV, encoding="utf-8") as fh:
        cases = [r["case_id"] for r in csv.DictReader(fh)]  # fixed case order
    events = collections.defaultdict(list)
    with open(EVENTS_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            r["_t"] = ts(r["timestamp"])
            events[r["case_id"]].append(r)
    for evs in events.values():
        evs.sort(key=lambda r: int(r["event_order"]))

    def year(c):
        subs = [e for e in events[c] if e["activity"] == SUBMIT]
        return (subs[0] if subs else events[c][0])["timestamp_original"][:4]

    def approver_rejected(c, removed=()):
        return any(e["activity"].startswith("Declaration REJECTED by ")
                   and e["activity"] != EMP_REJECT and e["activity"] not in removed
                   for e in events[c])

    submitted = [c for c in cases if year(c) == YEAR and any(e["activity"] == SUBMIT for e in events[c])]
    paid = [c for c in submitted if any(e["activity"] == PAID for e in events[c])]
    if (len(paid), len(submitted)) != (EXPECT_PAID, EXPECT_SUBMITTED):
        sys.exit(f"STOP: {len(paid)} paid / {len(submitted)} submitted 2018 cases, expected "
                 f"{EXPECT_PAID} / {EXPECT_SUBMITTED}.")

    # Per case, the waits (days) between consecutive events from the first SUBMITTED to Payment
    # Handled, each tagged with the event it leads to and the event it starts from.
    waits = {}
    for c in paid:
        evs = events[c]
        i0 = next(i for i, e in enumerate(evs) if e["activity"] == SUBMIT)
        i1 = next(i for i, e in enumerate(evs) if e["activity"] == PAID)
        waits[c] = [(evs[i - 1], evs[i], (evs[i]["_t"] - evs[i - 1]["_t"]).total_seconds() / 86400)
                    for i in range(i0 + 1, i1 + 1)]

    # S4 sample: paid cases rejected by ADMINISTRATION, in case order, seed 42.
    admin_rej = [c for c in paid if any(e["activity"] == ADMIN_REJECT for e in events[c])]
    n_pick = round(S4_SHARE * len(admin_rej))
    picked = set(random.Random(SEED).sample(admin_rej, n_pick))

    def s4_removed_waits(c):
        """Indexes of waits that lie between an ADMINISTRATION rejection and the next SUBMITTED."""
        out, inside = set(), False
        for i, (prev, e, _) in enumerate(waits[c]):
            if prev["activity"] == ADMIN_REJECT:
                inside = True
            if inside:
                out.add(i)
            if e["activity"] == SUBMIT:
                inside = False
        return out

    def cycle(c, s1=False, s2=False, s4=False):
        removed = s4_removed_waits(c) if s4 and c in picked else set()
        total = 0.0
        for i, (prev, e, d) in enumerate(waits[c]):
            if i in removed:
                continue
            if s1 and prev["activity"] == REQUEST and e["activity"] == PAID:
                d = min(d, PAYMENT_CAP)
            if s2 and e["activity"] in REMINDER_STEPS:
                d = min(d, REMINDER_CAP)
            total += d
        return total

    def payment_waits(s1=False, s2=False):
        out = []
        for c in paid:
            for prev, e, d in waits[c]:
                if prev["activity"] == REQUEST and e["activity"] == PAID:
                    out.append(min(d, PAYMENT_CAP) if s1 else d)
        return out

    n_rej_base = sum(1 for c in submitted if approver_rejected(c))
    # S4: a picked case loses its ADMINISTRATION rejections; it still counts as rejected if
    # another approver rejected it.
    n_rej_s4 = sum(1 for c in submitted
                   if approver_rejected(c, removed=(ADMIN_REJECT,) if c in picked else ()))

    scenarios = [
        ("Baseline", "2018 as measured", {}, n_rej_base, 0),
        ("S1", f"Daily payment runs (F1): Request Payment to Payment Handled capped at "
               f"{PAYMENT_CAP} day", {"s1": True}, n_rej_base, None),
        ("S2", f"Approval reminders (F3): wait before BUDGET OWNER approval, SUPERVISOR approval "
               f"and Request Payment capped at {REMINDER_CAP} days", {"s2": True}, n_rej_base, None),
        ("S3", "S1 and S2 together", {"s1": True, "s2": True}, n_rej_base, None),
        ("S4", f"Fewer rejections (F2): ADMINISTRATION rejection-to-resubmission time removed for "
               f"{n_pick} of {len(admin_rej)} paid cases rejected by ADMINISTRATION "
               f"({S4_SHARE:.0%} assumption, seed {SEED})", {"s4": True}, n_rej_s4, None),
    ]
    base = {c: cycle(c) for c in paid}
    rows = []
    for name, desc, kw, n_rej, _ in scenarios:
        ct = {c: cycle(c, **kw) for c in paid}
        changed = sum(1 for c in paid if abs(ct[c] - base[c]) > 1e-9)
        vals = [ct[c] for c in paid]
        over = sum(1 for v in vals if v > OVER_DAYS)
        pw = payment_waits(s1=kw.get("s1", False))
        rows.append([name, desc, len(paid), changed, pct_point(vals, 50), pct_point(vals, 90),
                     over, 100 * over / len(paid), pct_point(pw, 50), len(pw), n_rej,
                     len(submitted), 100 * n_rej / len(submitted)])

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "scenarios.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["scenario", "description", "paid_cases_2018", "cases_changed",
                    "cycle_median_days", "cycle_p90_days", "cases_over_14_days",
                    "share_over_14_days_pct", "payment_wait_median_days", "payment_wait_events",
                    "approver_rejected_cases", "submitted_cases_2018", "rejection_rate_pct"])
        w.writerows(rows)

    # Extra cycle time of paid cases rejected by each role, against paid cases never rejected.
    never = [base[c] for c in paid if not approver_rejected(c)]
    extra = []
    for role in ["ADMINISTRATION", "BUDGET OWNER", "SUPERVISOR"]:
        act = f"Declaration REJECTED by {role}"
        v = [base[c] for c in paid if any(e["activity"] == act for e in events[c])]
        extra.append([YEAR, role, len(v), pct_point(v, 50), len(never), pct_point(never, 50),
                      pct_point(v, 50) - pct_point(never, 50)])
    with open(os.path.join(OUT_DIR, "rework_extra_days.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["year", "rejecting_role", "paid_cases_rejected_by_role", "cycle_median_days",
                    "paid_cases_never_rejected", "never_rejected_cycle_median_days",
                    "extra_median_days"])
        w.writerows(extra)

    for r in rows:
        print(f"{r[0]:8} changed {r[3]:5}  median {r[4]:6.2f}  P90 {r[5]:6.2f}  over 14 d "
              f"{r[7]:5.2f}% ({r[6]})  payment wait median {r[8]:.2f}  rejection rate {r[12]:.2f}%")
    for r in extra:
        print(f"rejected by {r[1]}: {r[2]} paid cases, median {r[3]:.2f} d, extra {r[6]:+.2f} d")


if __name__ == "__main__":
    main()
