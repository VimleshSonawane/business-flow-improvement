"""Baseline KPIs for BPI Challenge 2020 Domestic Declarations.

Reads data/processed/events.csv and data/processed/cases.csv (built by
analysis/01_clean.py) and writes:
  data/outputs/tableau/*.csv     tables for Tableau (values unrounded)
  docs/baseline-kpi-report.md    deliverable D3 (rounding happens only here)

Measures only; no recommendations. Decisions applied are in docs/decisions.md.
Standard library only. Outputs are deterministic: no randomness, fixed sort orders,
no run timestamps; running it twice gives byte-identical files.

Run from anywhere:  python3 analysis/02_baseline.py
"""

import collections
import csv
import os
import platform
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS_CSV = os.path.join(ROOT, "data", "processed", "events.csv")
CASES_CSV = os.path.join(ROOT, "data", "processed", "cases.csv")
OUT_DIR = os.path.join(ROOT, "data", "outputs", "tableau")
REPORT_MD = os.path.join(ROOT, "docs", "baseline-kpi-report.md")

LOCAL_TZ = ZoneInfo("Europe/Amsterdam")
MAIN_YEAR = "2018"
YEARS = ["2018", "2017"]
ONLY = "2018 only"  # role-level KPIs are 2018 only (decisions 1 and 7)

# Checks against the raw log (docs/data-cleaning-log.md).
EXPECT_CASES, EXPECT_EVENTS, EXPECT_YEARS = 10500, 56437, {"2017": 2240, "2018": 8260}

SUBMIT = "Declaration SUBMITTED by EMPLOYEE"
SAVED = "Declaration SAVED by EMPLOYEE"
FINAL = "Declaration FINAL_APPROVED by SUPERVISOR"
REQUEST = "Request Payment"
PAID = "Payment Handled"
EMP_REJECT = "Declaration REJECTED by EMPLOYEE"
APPROVER_ROLES = ["ADMINISTRATION", "PRE_APPROVER", "BUDGET OWNER", "SUPERVISOR"]
REJECT_ROLES = APPROVER_ROLES + ["MISSING"]
MONEY = "Amount (units as in source)"
ADMIN_WORDING = ("ADMINISTRATION's approval is typically logged within a minute of submission, "
                 "which suggests it's recorded automatically or in batches; it shouldn't be read "
                 "as review effort")
ROUTE_WORDING = "may indicate a separate or manual payment route"
ZERO_WORDING = "rejected at a higher rate; reason not established from the log alone"


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def days(a, b):
    return (b - a).total_seconds() / 86400


def pct_point(values, p):
    """Percentile with linear interpolation between closest ranks: numpy's default (linear)
    method, the same as Excel PERCENTILE.INC."""
    v = sorted(values)
    if not v:
        return None
    k = (len(v) - 1) * p / 100
    lo = int(k)
    hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def mean(values):
    return sum(values) / len(values) if values else None


def f2(x):
    """Report rounding only. CSVs get unrounded values."""
    return "" if x is None else f"{x:,.2f}"


def pct(n, d):
    return None if not d else 100 * n / d


def fv(x):
    """A KPI value for the report table."""
    if x is None:
        return ""
    if isinstance(x, bool):
        return str(x)
    if isinstance(x, int):
        return f"{x:,}"
    if isinstance(x, float):
        return f"{x:,.2f}"
    return str(x)


def write_csv(name, cols, rows):
    with open(os.path.join(OUT_DIR, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(cols)
        w.writerows([["" if v is None else v for v in r] for r in rows])


def load():
    cases = collections.OrderedDict()
    with open(CASES_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cases[r["case_id"]] = r
    events = collections.defaultdict(list)
    n_events = 0
    with open(EVENTS_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            r["_t"] = ts(r["timestamp"])
            events[r["case_id"]].append(r)
            n_events += 1
    for evs in events.values():
        evs.sort(key=lambda r: int(r["event_order"]))  # timestamp order, ties in file order
    return cases, events, n_events


def case_year(evs):
    """Year of the first SUBMITTED event; for never-submitted drafts, of the first event.
    Local time as written in the source (each timestamp's own offset)."""
    subs = [e for e in evs if e["activity"] == SUBMIT]
    return (subs[0] if subs else evs[0])["timestamp_original"][:4]


def main():
    cases, events, n_events = load()
    os.makedirs(OUT_DIR, exist_ok=True)
    year = {c: case_year(events[c]) for c in cases}
    found_years = dict(sorted(collections.Counter(year.values()).items()))
    if (len(cases), n_events, found_years) != (EXPECT_CASES, EXPECT_EVENTS, EXPECT_YEARS) \
            or set(cases) != set(events):
        sys.exit(f"STOP: processed files don't match the raw log: {len(cases)} cases, "
                 f"{n_events} events, {found_years} per year.")
    year_agrees = sum(1 for c in cases if cases[c]["year"] == year[c])

    # Case sets.
    def in_year(cid, y):
        return y == "all" or year[cid] == y

    submitted = {c for c, evs in events.items() if any(e["activity"] == SUBMIT for e in evs)}
    # Paid: the case has a Payment Handled event, regardless of its submission path or of
    # what comes after the payment. Closed by the employee: last event REJECTED by EMPLOYEE.
    paid = {c for c, evs in events.items() if any(e["activity"] == PAID for e in evs)}
    closed = {c for c, evs in events.items() if evs[-1]["activity"] == EMP_REJECT and c not in paid}
    complete = paid | closed
    drafts = {c for c, evs in events.items()
              if any(e["activity"] == SAVED for e in evs) and c not in submitted}

    def status(c):
        return "paid" if c in paid else "closed by employee" if c in closed else "incomplete"

    # Rejected at least once: an approver rejection (ADMINISTRATION, PRE_APPROVER, BUDGET OWNER,
    # SUPERVISOR or MISSING). REJECTED by EMPLOYEE is the employee's response, not a rejection.
    approver_rejected = {c for c, evs in events.items() if any(
        e["activity"].startswith("Declaration REJECTED by ") and e["activity"] != EMP_REJECT
        for e in evs)}
    rej_flag_agrees = sum(1 for c in cases
                          if (cases[c]["rejected_at_least_once"] == "yes") == (c in approver_rejected))

    def rejected(c):
        return c in approver_rejected

    kpis = []  # (id, kpi, year, case set, denominator text, denominator, value, unit)

    def add(kid, name, y, case_set, den_text, den, value, unit):
        if not den:
            return  # step or role absent in this year; the CSVs keep the empty row
        kpis.append((kid, name, y, case_set, den_text, den, value, unit))

    # 0. Case status (every case is exactly one of paid, closed by employee, incomplete).
    for y in YEARS:
        cs_y = [c for c in cases if in_year(c, y)]
        for kid, s in [("0a", "paid"), ("0b", "closed by employee"), ("0c", "incomplete")]:
            add(kid, f"Cases {s}" + (" (has a Payment Handled event)" if s == "paid" else ""), y,
                f"all cases, year {y}", "all cases", len(cs_y),
                sum(1 for c in cs_y if status(c) == s), "cases")

    # 1. Cycle time, paid cases: first SUBMITTED -> Payment Handled.
    cycle = {}
    cycle_rows = []
    for c in cases:
        if c not in paid:
            continue
        evs = events[c]
        subs = [e["_t"] for e in evs if e["activity"] == SUBMIT]
        pays = [e["_t"] for e in evs if e["activity"] == PAID]
        if not subs or not pays:
            continue
        cycle[c] = days(min(subs), min(pays))
    for c in cases:
        if c in cycle:
            r = cases[c]
            cycle_rows.append([c, year[c], cycle[c], "yes" if rejected(c) else "no",
                               sum(1 for e in events[c] if e["activity"] == SUBMIT) - 1,
                               r["event_count"], r["amount"], r["amount_flag"]])
    write_csv("cycle_time_by_case.csv",
              ["case_id", "year", "cycle_days", "rejected_at_least_once", "resubmissions",
               "event_count", "amount_units_as_in_source", "amount_flag"], cycle_rows)
    paid_no_submit = [c for c in cases if c in paid and c not in submitted]

    for y in YEARS:
        vals = [v for c, v in cycle.items() if in_year(c, y)]
        cs = f"paid cases, year {y}"
        den = "paid cases with a submission"
        add("1a", "Cycle time, median", y, cs, den, len(vals), pct_point(vals, 50), "days")
        add("1b", "Cycle time, mean", y, cs, den, len(vals), mean(vals), "days")
        add("1c", "Cycle time, P75", y, cs, den, len(vals), pct_point(vals, 75), "days")
        add("1d", "Cycle time, P90", y, cs, den, len(vals), pct_point(vals, 90), "days")

    # 2. Transitions (complete cases only, per decision 4).
    trans_rows = []
    trans = {}
    for y in YEARS:  # one set of rows per year; the process map defaults to 2018
        acc = collections.defaultdict(lambda: {"cases": set(), "d": []})
        for c in cases:
            if c not in complete or not in_year(c, y):
                continue
            evs = events[c]
            seq = [("START", None)] + [(e["activity"], e["_t"]) for e in evs] + [("END", None)]
            for (a, ta), (b, tb) in zip(seq, seq[1:]):
                k = acc[(a, b)]
                k["cases"].add(c)
                if ta and tb:
                    k["d"].append(days(ta, tb))
        trans[y] = acc
        for (a, b), k in sorted(acc.items(), key=lambda x: (-len(x[1]["cases"]), x[0])):
            trans_rows.append([y, a, b, len(k["cases"]), len(k["d"]) or len(k["cases"]),
                               pct_point(k["d"], 50), pct_point(k["d"], 90)])
    write_csv("transitions.csv",
              ["year", "from_activity", "to_activity", "case_count", "transition_count",
               "median_days", "p90_days"], trans_rows)

    # 3. Time until each role acts (complete cases, 2018 only): previous event -> this event.
    Y = MAIN_YEAR
    steps = APPROVER_ROLES + [REQUEST, PAID]
    wait_rows = []
    acc = collections.defaultdict(list)
    acc_cases = collections.defaultdict(set)
    for c in cases:
        if c not in complete or not in_year(c, Y):
            continue
        evs = events[c]
        for prev, e in zip(evs, evs[1:]):
            step = e["activity"] if e["activity"] in (REQUEST, PAID) else e["org:role"]
            if step in steps:
                acc[step].append(days(prev["_t"], e["_t"]))
                acc_cases[step].add(c)
    w18 = acc
    for s in steps:
        d = acc[s]
        wait_rows.append([Y, s, len(d), len(acc_cases[s]), pct_point(d, 50), pct_point(d, 90)])
        label = s if s in (REQUEST, PAID) else f"{s} acts"
        add("3", f"Wait before {label}, median ({ONLY})", Y, f"complete cases, year {Y}",
            "events of this step", len(d), pct_point(d, 50), "days")
        add("3", f"Wait before {label}, P90 ({ONLY})", Y, f"complete cases, year {Y}",
            "events of this step", len(d), pct_point(d, 90), "days")
    write_csv("role_wait_times.csv",
              [f"year ({ONLY})", "step", "events", "cases", "median_days", "p90_days"], wait_rows)

    # 4. Rejections (submitted cases, all end statuses). Rates by role: 2018 only.
    rej_rows = []
    rej = {}
    for y in YEARS:
        sub_y = [c for c in cases if c in submitted and in_year(c, y)]
        n_rej = sum(1 for c in sub_y if rejected(c))
        rej[y] = (n_rej, len(sub_y))
        add("4a", "Cases rejected at least once (approver rejections; REJECTED by EMPLOYEE not counted)",
            y, f"submitted cases, year {y}", "submitted cases", len(sub_y), pct(n_rej, len(sub_y)),
            f"% ({n_rej} of {len(sub_y)} cases)")
        sub_nz = [c for c in sub_y if cases[c]["amount_flag"] == ""]
        n_rej_nz = sum(1 for c in sub_nz if rejected(c))
        add("4a", "Rejected at least once, non-zero amounts only", y,
            f"submitted cases with amount > 0, year {y}", "submitted cases with amount > 0",
            len(sub_nz), pct(n_rej_nz, len(sub_nz)), f"% ({n_rej_nz} of {len(sub_nz)} cases)")
    sub_18 = [c for c in cases if c in submitted and in_year(c, Y)]
    for role in REJECT_ROLES:
        reached = [c for c in sub_18 if any(e["org:role"] == role for e in events[c])]
        n = sum(1 for c in sub_18 for e in events[c] if e["activity"] == f"Declaration REJECTED by {role}")
        ncases = sum(1 for c in sub_18 if any(
            e["activity"] == f"Declaration REJECTED by {role}" for e in events[c]))
        if role == "MISSING":
            rate, note = None, ("rate not meaningful: MISSING appears only on rejection events, "
                                "so every case that reaches it is a rejection")
        else:
            rate, note = pct(n, len(reached)), ""
        rej_rows.append([Y, role, n, ncases, len(reached), rate, note])
        if role != "MISSING":
            add("4b", f"Rejections by {role} per 100 cases reaching {role} ({ONLY})", Y,
                f"submitted cases reaching {role}, year {Y}", f"cases with a {role} event",
                len(reached), rate, f"per 100 cases ({n} rejections)")
    write_csv("rejections_by_role.csv",
              [f"year ({ONLY})", "role", "rejections", "cases_with_rejection", "cases_reaching_role",
               "rejections_per_100_cases_reaching_role", "note"], rej_rows)
    # MISSING, 2017 (data-quality context; MISSING doesn't occur in 2018).
    missing17_events = sum(1 for c in cases if in_year(c, "2017") for e in events[c]
                           if e["activity"] == "Declaration REJECTED by MISSING")
    missing17_cases = sum(1 for c in cases if in_year(c, "2017") and any(
        e["activity"] == "Declaration REJECTED by MISSING" for e in events[c]))

    # 5. Rework.
    rework = {}
    for y in YEARS:
        sub_y = [c for c in cases if c in submitted and in_year(c, y)]
        resub = {c: sum(1 for e in events[c] if e["activity"] == SUBMIT) - 1 for c in sub_y}
        n_resub = sum(resub.values())
        n_cases = sum(1 for v in resub.values() if v >= 1)
        with_r = [v for c, v in cycle.items() if in_year(c, y) and rejected(c)]
        without_r = [v for c, v in cycle.items() if in_year(c, y) and not rejected(c)]
        rework[y] = (n_resub, n_cases, len(sub_y), with_r, without_r)
        cs = f"submitted cases, year {y}"
        add("5a", "Resubmissions (SUBMITTED events after the first)", y, cs,
            "submitted cases", len(sub_y), n_resub, "events")
        add("5b", "Cases with 1+ resubmission", y, cs, "submitted cases", len(sub_y),
            pct(n_cases, len(sub_y)), "%")
        add("5c", "Cycle time median, paid WITH a rejection", y, f"paid cases rejected 1+, year {y}",
            "paid cases rejected at least once", len(with_r), pct_point(with_r, 50), "days")
        add("5d", "Cycle time median, paid WITHOUT a rejection", y,
            f"paid cases never rejected, year {y}", "paid cases never rejected",
            len(without_r), pct_point(without_r, 50), "days")

    # 6. Variants (all cases of the year, any end status).
    var_rows = []
    variants = {}
    for y in YEARS:
        cs_y = [c for c in cases if in_year(c, y)]
        cnt = collections.Counter(" > ".join(e["activity"] for e in events[c]) for c in cs_y)
        top = sorted(cnt.items(), key=lambda x: (-x[1], x[0]))[:10]
        variants[y] = (top, len(cs_y), len(cnt))
        for i, (v, n) in enumerate(top, 1):
            var_rows.append([y, i, n, pct(n, len(cs_y)), len(v.split(" > ")), v])
        add("6", "Cases on the most common path", y, f"all cases, year {y}", "all cases",
            len(cs_y), pct(top[0][1], len(cs_y)), f"% ({len(cnt)} distinct paths)")
    write_csv("variants_top10.csv",
              ["year", "rank", "cases", "pct_of_cases", "steps", "variant"], var_rows)

    # 7. Compliance (all cases with a Payment Handled event, both years).
    flags = []
    no_request = []  # (case, year, amount, days from final approval to payment)
    for c in cases:
        evs = events[c]
        acts = [e["activity"] for e in evs]
        if PAID not in acts:
            continue
        t_pay = min(e["_t"] for e in evs if e["activity"] == PAID)
        finals = [e["_t"] for e in evs if e["activity"] == FINAL]
        if REQUEST not in acts:
            flags.append([c, year[c], "payment_without_request",
                          "Payment Handled with no Request Payment event"])
            no_request.append((c, year[c], cases[c]["amount"],
                               days(max(t for t in finals if t <= t_pay), t_pay)
                               if any(t <= t_pay for t in finals) else None))
        if not finals:
            flags.append([c, year[c], "payment_without_final_approval",
                          "Payment Handled with no FINAL_APPROVED by SUPERVISOR event"])
        elif t_pay < min(finals):
            flags.append([c, year[c], "payment_before_final_approval",
                          "Payment Handled before the first FINAL_APPROVED by SUPERVISOR"])
        if acts.count(PAID) > 1:
            flags.append([c, year[c], "paid_more_than_once",
                          f"{acts.count(PAID)} Payment Handled events"])
        if acts[-1] != PAID:
            flags.append([c, year[c], "events_after_payment",
                          "Payment Handled is not the last event; last is " + acts[-1]])
        if SUBMIT not in acts:
            flags.append([c, year[c], "paid_without_submission",
                          "Payment Handled with no Declaration SUBMITTED by EMPLOYEE event"])
    write_csv("compliance_flags.csv", ["case_id", "year", "check", "detail"], flags)
    checks = ["payment_without_request", "payment_without_final_approval",
              "payment_before_final_approval", "paid_more_than_once", "events_after_payment",
              "paid_without_submission"]
    with_pay = len(paid)
    flag_by = {k: [f for f in flags if f[2] == k] for k in checks}
    flagged_cases = sorted({f[0] for f in flags})
    for k in checks:
        add("7", f"Compliance: {k}", "all", "cases with a Payment Handled event, both years",
            "cases with a Payment Handled event", with_pay, len(flag_by[k]), "cases")
    add("7", "Compliance: flag events (all checks)", "all", "cases with a Payment Handled event, both years",
        "cases with a Payment Handled event", with_pay, len(flags), "flag events")
    add("7", "Compliance: distinct cases flagged (any check)", "all",
        "cases with a Payment Handled event, both years", "cases with a Payment Handled event",
        with_pay, len(flagged_cases), "cases")
    nr_days = [d for *_, d in no_request if d is not None]
    add("7b", "Payments without Request Payment: final approval to payment, median", "all",
        "cases flagged payment_without_request", "cases", len(nr_days), pct_point(nr_days, 50), "days")
    add("7b", "Payments without Request Payment: final approval to payment, minimum", "all",
        "cases flagged payment_without_request", "cases", len(nr_days), min(nr_days) if nr_days else None, "days")
    add("7b", "Payments without Request Payment: final approval to payment, maximum", "all",
        "cases flagged payment_without_request", "cases", len(nr_days), max(nr_days) if nr_days else None, "days")

    # 8. Abandoned drafts and incomplete cases.
    for y in YEARS:
        cs_y = [c for c in cases if in_year(c, y)]
        d = sum(1 for c in drafts if in_year(c, y))
        inc = sum(1 for c in cs_y if c not in complete)
        add("8a", "Drafts saved, never submitted", y, f"all cases, year {y}", "all cases",
            len(cs_y), d, "cases")
        add("8b", "Incomplete cases (no clear end)", y, f"all cases, year {y}", "all cases",
            len(cs_y), inc, "cases")
    incomplete_last = collections.Counter(
        (year[c], events[c][-1]["activity"]) for c in cases if c not in complete)

    # 9. Monthly submissions (events in 2018, local time, any case).
    month = collections.Counter()
    first_month = collections.Counter()
    for c, evs in events.items():
        first_seen = False
        for e in evs:
            if e["activity"] != SUBMIT:
                continue
            m = e["_t"].astimezone(LOCAL_TZ).strftime("%Y-%m")
            if m.startswith(MAIN_YEAR):
                month[m] += 1
                if not first_seen:
                    first_month[m] += 1
            first_seen = True
    months = [f"{MAIN_YEAR}-{i:02d}" for i in range(1, 13)]
    write_csv("monthly_volume.csv", ["month", "submissions_all", "first_submissions",
                                     "resubmissions"],
              [[m, month[m], first_month[m], month[m] - first_month[m]] for m in months])
    peak = max(months, key=lambda m: (month[m], m))
    low = min(months, key=lambda m: (month[m], m))
    add("9", "Submissions per month, median", MAIN_YEAR,
        "SUBMITTED events dated 2018 (Dutch time), any case", "months", 12,
        pct_point([month[m] for m in months], 50), "events per month")

    # 10. Money (zero amounts excluded).
    money = {}
    for y in YEARS:
        cs_all = [c for c in cases if in_year(c, y)]
        cs_y = [c for c in cs_all if cases[c]["amount_flag"] == ""]
        amts = [float(cases[c]["amount"]) for c in cs_y]
        rej_amt = sum(float(cases[c]["amount"]) for c in cs_y if rejected(c))
        tot = sum(amts)
        money[y] = (len(cs_y), pct_point(amts, 50), rej_amt, tot)
        cs = f"cases with amount > 0, year {y}"
        add("10z", "Cases with a zero amount (excluded from money figures)", y, f"all cases, year {y}",
            "all cases", len(cs_all), sum(1 for c in cs_all if cases[c]["amount_flag"] == "zero"), "cases")
        add("10a", f"Median amount, {MONEY}", y, cs, "cases with amount > 0", len(cs_y),
            pct_point(amts, 50), "units as in source")
        add("10b", f"Total amount in cases rejected 1+, {MONEY}", y, cs,
            "cases with amount > 0", len(cs_y), rej_amt, "units as in source")
        add("10b", f"Total amount, {MONEY}", y, cs, "cases with amount > 0", len(cs_y), tot,
            "units as in source")
        add("10b", "Share of the total amount in cases rejected 1+", y, cs, "cases with amount > 0",
            len(cs_y), pct(rej_amt, tot), "%")

    # 10c. Zero amounts and rejection, submitted 2018 cases (drafts excluded).
    sub_zero = [c for c in sub_18 if cases[c]["amount_flag"] == "zero"]
    sub_nonzero = [c for c in sub_18 if cases[c]["amount_flag"] == ""]
    rz = [c for c in sub_zero if rejected(c)]
    rn = [c for c in sub_nonzero if rejected(c)]
    add("10c", "Rejected at least once, zero-amount submitted cases", Y,
        f"submitted cases with amount 0, year {Y}", "submitted zero-amount cases", len(sub_zero),
        pct(len(rz), len(sub_zero)), f"% ({len(rz)} cases)")
    add("10c", "Rejected at least once, non-zero submitted cases", Y,
        f"submitted cases with amount > 0, year {Y}", "submitted non-zero cases", len(sub_nonzero),
        pct(len(rn), len(sub_nonzero)), f"% ({len(rn)} cases)")
    add("10c", "Share of rejected cases that have a zero amount", Y,
        f"submitted cases rejected at least once, year {Y}", "rejected submitted cases",
        rej[Y][0], pct(len(rz), rej[Y][0]), f"% ({len(rz)} cases)")
    zero_outcome = collections.Counter(status(c) for c in rz)
    for s in ["paid", "closed by employee", "incomplete"]:
        add("10d", f"Rejected zero-amount cases by outcome: {s}", Y,
            f"submitted zero-amount cases rejected at least once, year {Y}",
            "rejected zero-amount cases", len(rz), zero_outcome[s], "cases")
    zero_role = {}
    for role in REJECT_ROLES:
        act = f"Declaration REJECTED by {role}"
        n_ev = sum(1 for c in rz for e in events[c] if e["activity"] == act)
        n_cs = sum(1 for c in rz if any(e["activity"] == act for e in events[c]))
        zero_role[role] = (n_ev, n_cs)
        if n_ev:
            add("10e", f"Rejected zero-amount cases, rejections by {role} ({ONLY})", Y,
                f"submitted zero-amount cases rejected at least once, year {Y}",
                "rejected zero-amount cases", len(rz), n_ev, f"rejection events ({n_cs} cases)")

    # Payment weekday and speed of the first ADMINISTRATION step (2018, complete cases).
    wd_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pay_wd = collections.Counter(
        e["_t"].astimezone(LOCAL_TZ).weekday() for c in cases if in_year(c, MAIN_YEAR)
        for e in events[c] if e["activity"] == PAID)
    n_pay = sum(pay_wd.values())
    mon_thu = pay_wd[0] + pay_wd[3]
    add("3b", "Payment Handled events on a Monday or Thursday", MAIN_YEAR,
        f"Payment Handled events, cases of {MAIN_YEAR} (Dutch time)", "Payment Handled events",
        n_pay, pct(mon_thu, n_pay), "%")
    admin_sec = [(e["_t"] - prev["_t"]).total_seconds()
                 for c in cases if c in complete and in_year(c, MAIN_YEAR)
                 for prev, e in zip(events[c], events[c][1:])
                 if prev["activity"] == SUBMIT and e["org:role"] == "ADMINISTRATION"]
    admin_under_min = sum(1 for s in admin_sec if s < 60)
    cs3 = f"complete cases, year {MAIN_YEAR}"
    den3 = "SUBMITTED then ADMINISTRATION transitions"
    add("3c", f"Submission to ADMINISTRATION action, median ({ONLY})", MAIN_YEAR, cs3, den3,
        len(admin_sec), pct_point(admin_sec, 50), "seconds")
    add("3c", f"Submission to ADMINISTRATION action, under 1 minute ({ONLY})", MAIN_YEAR, cs3, den3,
        len(admin_sec), pct(admin_under_min, len(admin_sec)), f"% ({admin_under_min} transitions)")
    add("3c", f"Submission to ADMINISTRATION action, Q1 (P25) ({ONLY})", MAIN_YEAR, cs3, den3,
        len(admin_sec), pct_point(admin_sec, 25), "seconds")
    add("3c", f"Submission to ADMINISTRATION action, Q3 (P75) ({ONLY})", MAIN_YEAR, cs3, den3,
        len(admin_sec), pct_point(admin_sec, 75), "seconds")
    # Timestamp precision in the log: milliseconds and the seconds field.
    all_ts = [e["timestamp_original"] for evs in events.values() for e in evs]
    frac = collections.Counter(t[19:23] for t in all_ts)
    secs = {t[17:19] for t in all_ts}
    to_second = len(secs) > 1 and set(frac) == {".000"}
    precision = ("to the second: milliseconds are always .000 and the seconds field takes "
                 f"{len(secs)} different values" if to_second else
                 "to the minute or coarser, so second-level waits can't be interpreted")

    kpis.sort(key=lambda k: (k[2] != MAIN_YEAR, k[2]))  # stable: 2018, then 2017, then all
    write_csv("kpi_summary.csv",
              ["kpi_id", "kpi", "year", "case_set", "denominator_description", "denominator",
               "value", "unit"], kpis)

    # Report.
    ct = {y: [v for c, v in cycle.items() if in_year(c, y)] for y in YEARS}
    nr, nrc, nsub, wr, wor = rework[Y]
    top, ncs, nvar = variants[Y]
    rj = {r[1]: r for r in rej_rows}
    t18 = trans[Y]
    slowest = sorted(((a, b, k) for (a, b), k in t18.items()
                      if len(k["cases"]) >= 100 and k["d"]),
                     key=lambda x: (-pct_point(x[2]["d"], 50), x[0], x[1]))[:3]

    md = ["# Baseline KPI report — BPI Challenge 2020, Domestic Declarations (D3)", "",
          "Generated by `analysis/02_baseline.py` from `data/processed/`. Do not edit by hand; "
          "re-run the script. Measures only, no recommendations. Decisions applied: "
          "[`docs/decisions.md`](decisions.md).", "",
          "**Main view: cases of 2018.** 2017 is shown separately and labelled; it "
          "covers two departments only and its roles differ, so 2017 vs 2018 is not a trend. "
          "**Role-level KPIs (wait times and rejections by role) are 2018 only** (decisions 1 and 7).", "",
          f"Input check: {len(cases):,} cases and {n_events:,} events; "
          + ", ".join(f"{n:,} cases in {y}" for y, n in found_years.items())
          + f" by the year definition below (it agrees with `cases.csv` `year` for {year_agrees:,} "
          f"of {len(cases):,} cases). Python {platform.python_version()}, standard library only.", "",
          "## Definitions", "",
          "- **Year**: the year of the case's first `Declaration SUBMITTED by EMPLOYEE` event; for "
          "never-submitted drafts, the year of its first event (Dutch local time, as written in the "
          "source). A case spanning New Year counts once, in that year.",
          "- **Submitted case**: has at least one `Declaration SUBMITTED by EMPLOYEE`.",
          "- **Paid case**: the case has a `Payment Handled` event, regardless of its submission "
          "path or of any event after the payment.",
          "- **Closed by the employee after a rejection**: not paid, and the case's last event is "
          "`Declaration REJECTED by EMPLOYEE` (so no later submission).",
          "- **Complete case**: paid or closed by the employee. Everything else is incomplete, "
          "including cases whose last event is a rejection by another role with no employee response.",
          "- **Cycle time**: first `Declaration SUBMITTED by EMPLOYEE` to `Payment Handled`, "
          "paid cases with a submission only, in fractional days from the timestamps (each "
          "carries its own UTC offset).",
          "- **Rejected at least once**: one or more rejections by ADMINISTRATION, PRE_APPROVER, "
          "BUDGET OWNER, SUPERVISOR or MISSING (the employee's own `REJECTED by EMPLOYEE` step "
          f"is not counted as a rejection; checked against `cases.csv`, agreeing for {rej_flag_agrees:,} "
          f"of {len(cases):,} cases).",
          "- **Resubmission**: any `SUBMITTED` event after the first in a case.",
          "- **Process map** (`transitions.csv`): one set of rows per year, in the `year` column "
          "(2018 and 2017, never combined). The process map defaults to 2018; filter on `year` for 2017.",
          "- **Wait before a step**: time from the previous event in the case to that step; "
          "for approver roles, any event by that role (approve or reject). 2018 only.",
          "- **Percentiles**: linear interpolation (numpy's default method, the same as Excel "
          "`PERCENTILE.INC`). Values are rounded only in this report; the CSVs are unrounded.",
          f"- **Money**: `{MONEY}`. The source states no currency. Cases with amount 0 are "
          "excluded from money figures only; for rejection rates by amount, the base is "
          "submitted cases.", "",
          "## KPI table", "",
          "| ID | KPI | Year | Filter (case set) | Denominator | Value | Unit |",
          "|---|---|---|---|---:|---:|---|"]
    missing_note = (f"MISSING only ever rejects (its only event is `Declaration REJECTED by "
                    f"MISSING`), so a rate per 100 cases reaching the role is not meaningful and is "
                    f"not shown. It does not occur in 2018 (0 rejection events, 0 cases). In 2017 "
                    f"(data-quality context, not a role KPI) it has {missing17_events} rejection "
                    f"events in {missing17_cases} distinct cases. It is left out of role charts "
                    f"(decision 8).")
    for k in kpis:
        md.append(f"| {k[0]} | {k[1]} | {k[2]} | {k[3]} | {k[5]:,} ({k[4]}) | {fv(k[6])} | {k[7]} |")
    md += ["", f"[note 1] {missing_note}"]

    md += ["", "## Findings (2018 main view unless labelled)", ""]
    find = []
    nr_sorted = sorted(no_request, key=lambda x: x[0])
    find.append(
        f"**Paid cases take a median of {f2(pct_point(ct[Y], 50))} days from first submission "
        f"to payment, but 1 in 10 takes more than {f2(pct_point(ct[Y], 90))} days** "
        f"(P75 {f2(pct_point(ct[Y], 75))}, mean {f2(mean(ct[Y]))}; "
        f"denominator: {len(ct[Y]):,} paid 2018 cases). By comparison, payments with "
        f"no `Request Payment` step (n = {len(nr_days)}) took a median of {f2(pct_point(nr_days, 50))} days "
        f"from final approval to payment (range {f2(min(nr_days))} to {f2(max(nr_days))} days), which "
        f"{ROUTE_WORDING}.")
    find.append(
        f"**Paid cases with a rejection take {pct_point(wr, 50) / pct_point(wor, 50):.1f} times "
        f"as long (median).** Median cycle time is "
        f"{f2(pct_point(wr, 50))} days for paid cases rejected at least once "
        f"({len(wr):,} cases) vs {f2(pct_point(wor, 50))} days for paid cases never rejected "
        f"({len(wor):,} cases), 2018.")
    find.append(
        f"**{f2(pct(rej[Y][0], rej[Y][1]))}% of submitted cases are rejected at least once** "
        f"({rej[Y][0]:,} of {rej[Y][1]:,} submitted 2018 cases). "
        f"{nr:,} resubmissions in {nrc:,} cases ({f2(pct(nrc, nsub))}% of submitted cases).")
    a = rj["ADMINISTRATION"]
    find.append(
        f"**ADMINISTRATION does most of the rejecting** (2018 only): {a[2]:,} rejections, "
        f"{f2(a[5])} per 100 of the {a[4]:,} 2018 cases it handled. Other roles: "
        + "; ".join(f"{r} {f2(rj[r][5])} per 100 ({rj[r][2]:,} rejections, {rj[r][4]:,} cases)"
                    for r in ["SUPERVISOR", "PRE_APPROVER", "BUDGET OWNER"]
                    if rj[r][4]) + ". PRE_APPROVER and MISSING do not appear in 2018 cases.")
    find.append(
        f"**Zero-amount cases are {ZERO_WORDING}.** Of {len(sub_zero):,} submitted 2018 cases with "
        f"amount 0, {len(rz):,} ({f2(pct(len(rz), len(sub_zero)))}%) were rejected at least once, "
        f"against {len(rn):,} of {len(sub_nonzero):,} submitted cases with amount > 0 "
        f"({f2(pct(len(rn), len(sub_nonzero)))}%). Zero-amount cases are "
        f"{f2(pct(len(rz), rej[Y][0]))}% of all {rej[Y][0]:,} rejected submitted 2018 cases. "
        f"Final outcome of the {len(rz):,} rejected zero-amount cases: "
        + ", ".join(f"{s} {zero_outcome[s]:,}" for s in ["paid", "closed by employee", "incomplete"])
        + ". Rejections in them by role (2018 only): "
        + "; ".join(f"{r} {zero_role[r][0]:,} events in {zero_role[r][1]:,} cases"
                    for r in REJECT_ROLES if zero_role[r][0]) + ".")
    zero18 = [c for c in cases if in_year(c, Y) and cases[c]["amount_flag"] == "zero"]
    zero18_drafts = [c for c in zero18 if c not in submitted]
    zero18_rej = [c for c in zero18 if c in submitted and rejected(c)]
    closed18 = [c for c in closed if in_year(c, Y)]
    if (not any(c in paid for c in zero18) and len(zero18_drafts) + len(zero18_rej) == len(zero18)
            and all(c in zero18_rej for c in closed18)):
        find.append(
            f"**No zero-amount case was paid. Every {Y} zero-amount case is either a never-submitted "
            f"draft ({len(zero18_drafts)}) or was rejected ({len(zero18_rej)}), and those rejections "
            f"account for all {len(closed18)} cases closed by the employee.** Denominator: "
            f"{len(zero18)} zero-amount {Y} cases; {len(closed18)} cases closed by the employee in {Y}.")
    find.append(
        f"**Among the steps, the longest median wait is before `Payment Handled`** (2018 only). Median wait before "
        f"`Request Payment`: {f2(pct_point(w18[REQUEST], 50))} days (P90 "
        f"{f2(pct_point(w18[REQUEST], 90))}; {len(w18[REQUEST]):,} events). Before `Payment "
        f"Handled`: {f2(pct_point(w18[PAID], 50))} days (P90 {f2(pct_point(w18[PAID], 90))}). "
        "Approver waits: " + "; ".join(
            f"{r} {f2(pct_point(w18[r], 50))} (P90 {f2(pct_point(w18[r], 90))})"
            for r in APPROVER_ROLES if w18[r]) + " days; complete 2018 cases.")
    find.append(
        f"**Payments run in batches**: {f2(pct(mon_thu, n_pay))}% of `Payment Handled` events "
        f"fall on a Monday or Thursday ({mon_thu:,} of {n_pay:,} events in 2018 cases, Dutch "
        "time): " + ", ".join(f"{wd_names[d]} {pay_wd[d]:,}" for d in range(7) if pay_wd[d])
        + ".")
    find.append(
        f"**{ADMIN_WORDING}** (2018 only). Of {len(admin_sec):,} submission-to-ADMINISTRATION "
        f"transitions in complete 2018 cases, {admin_under_min:,} ({f2(pct(admin_under_min, len(admin_sec)))}%) "
        f"took under a minute; median {f2(pct_point(admin_sec, 50))} seconds, interquartile range "
        f"{f2(pct_point(admin_sec, 25))} to {f2(pct_point(admin_sec, 75))} seconds. Timestamps are "
        f"precise {precision}" + (", so the median is measured to the second." if to_second else ".")
        + " Treated as a data limitation, not review time (decision 5).")
    find.append(
        "**Slowest common transitions** (median days, transitions seen in 100+ complete 2018 "
        "cases): " + "; ".join(
            f"{a_} → {b_} {f2(pct_point(k['d'], 50))} days ({len(k['cases']):,} cases)"
            for a_, b_, k in slowest) + ".")
    find.append(
        f"**The process is fairly standardised**: the most common path covers "
        f"{f2(pct(top[0][1], ncs))}% of 2018 cases ({top[0][1]:,} of {ncs:,}) and the top 10 "
        f"cover {f2(pct(sum(n for _, n in top), ncs))}%; {nvar:,} distinct paths in total. "
        f"Most common path: `{top[0][0]}`.")
    pns = ", ".join(f"{c} ({year[c]}, amount {f2(float(cases[c]['amount']))})" for c in paid_no_submit)
    already = [c for c in paid_no_submit
               if any(f[0] == c and f[2] != "paid_without_submission" for f in flags)]
    find.append(
        "**Compliance flags** (cases with a payment, both years, denominator "
        f"{with_pay:,}): " + "; ".join(f"{k.replace('_', ' ')} {len(flag_by[k])}" for k in checks)
        + f". In total {len(flags)} flag events in {len(flagged_cases)} distinct cases. "
        f"Paid without a submission: {len(paid_no_submit)} case(s), {pns}"
        + (f"; {paid_no_submit[0]} is the only one" if len(paid_no_submit) == 1 else "")
        + (f", and was already flagged for another check ({', '.join(f[2] for f in flags if f[0] in already and f[2] != 'paid_without_submission')})"
           if already else "")
        + ". Case ids are listed below and in `compliance_flags.csv`. Cases paid without "
        "final approval are control exceptions flagged for review: either a control failure "
        "or a data issue, not determinable from this data (decision 6).")
    d17 = sum(1 for c in drafts if in_year(c, "2017"))
    d18 = sum(1 for c in drafts if in_year(c, "2018"))
    inc_total = len(cases) - len(complete)
    drafts_inc = [c for c in cases if c in drafts and c not in complete]
    drafts_done = [c for c in cases if c in drafts and c in complete]
    find.append(
        f"**{inc_total} cases ({f2(pct(inc_total, len(cases)))}% of all {len(cases):,}) have no "
        f"clear end** and are excluded from durations. {len(drafts)} cases were saved and never "
        f"submitted (2017: {d17}, 2018: {d18}); {len(drafts_inc)} of them are among the "
        f"incomplete cases and {len(drafts_done)} was paid anyway ("
        + ", ".join(drafts_done) + "). By year and last activity: "
        + "; ".join(f"{y} {a_} {n}" for (y, a_), n in sorted(incomplete_last.items())) + ".")
    m_n, m_med, m_rej, m_tot = money[Y]
    find.append(
        f"**Money**: median amount {f2(m_med)} ({MONEY}); cases rejected at least once hold "
        f"{f2(m_rej)} of {f2(m_tot)} total ({f2(pct(m_rej, m_tot))}%); denominator "
        f"{m_n:,} 2018 cases with amount > 0.")
    find.append(
        f"**Workload**: 2018 submissions peak in {peak} ({month[peak]:,} SUBMITTED events) and "
        f"are lowest in {low} ({month[low]:,}); see `monthly_volume.csv`.")
    c17 = ct["2017"]
    find.append(
        f"*2017, two departments only, not comparable as a trend:* median cycle time "
        f"{f2(pct_point(c17, 50))} days ({len(c17):,} paid cases); "
        f"{f2(pct(rej['2017'][0], rej['2017'][1]))}% rejected at least once "
        f"({rej['2017'][0]:,} of {rej['2017'][1]:,} submitted cases).")
    md += [f"{i}. {t}" for i, t in enumerate(find, 1)]

    # Reconciliation: every case is exactly one status; drafts and compliance overlap stated.
    md += ["", "### Case status reconciliation", "",
           "Every case has exactly one status. Drafts, compliance flags and statuses overlap; "
           "each case is counted once per table below.", "",
           "| Year | Paid | Closed by employee | Incomplete | Total | Drafts (saved, never submitted) |",
           "|---|---:|---:|---:|---:|---|"]
    for y in YEARS:
        cs_y = [c for c in cases if in_year(c, y)]
        sc = collections.Counter(status(c) for c in cs_y)
        dy = [c for c in drafts if in_year(c, y)]
        dsplit = collections.Counter(status(c) for c in dy)
        md.append(f"| {y} | {sc['paid']:,} | {sc['closed by employee']:,} | {sc['incomplete']:,} | "
                  f"{len(cs_y):,} | {len(dy)} ({', '.join(f'{n} {s}' for s, n in sorted(dsplit.items()))}) |")
    for c in sorted(set(paid_no_submit) | {c for c in paid if events[c][-1]["activity"] != PAID}):
        f_c = sorted({f[2] for f in flags if f[0] == c})
        md.append("")
        md.append(f"- **{c}** ({year[c]}): status {status(c)}; in drafts: "
                  f"{'yes' if c in drafts else 'no'}; compliance checks: {', '.join(f_c) or 'none'}. "
                  "Counted once as paid in the status table, and once per check in "
                  "`compliance_flags.csv`.")

    md += ["", "### Compliance case ids", ""]
    for k in checks:
        ids = [f[0] for f in flag_by[k]]
        note = (" — control exceptions flagged for review: either a control failure or a "
                "data issue, not determinable from this data (decision 6)"
                if k == "payment_without_final_approval" and ids else "")
        md.append(f"- **{k}** ({len(ids)}): " + (", ".join(ids) if ids else "none") + note)

    md += ["", f"### Payments with no `Request Payment` step (n = {len(no_request)})", "",
           f"These {ROUTE_WORDING}. Median {f2(pct_point(nr_days, 50))} days from final approval to "
           f"payment (range {f2(min(nr_days))} to {f2(max(nr_days))}), against a median cycle time "
           f"of {f2(pct_point(ct[Y], 50))} days for all paid 2018 cases.", "",
           f"| Case | Year | {MONEY} | Final approval to payment (days) |", "|---|---|---:|---:|"]
    for c, y, amt, d in nr_sorted:
        md.append(f"| {c} | {y} | {f2(float(amt))} | {f2(d)} |")

    md += ["", f"### Rejections by role ({ONLY})", "",
           "| Role | Rejection events | Distinct cases rejected | Cases reaching role | Per 100 cases reaching role |",
           "|---|---:|---:|---:|---|"]
    for r in rej_rows:
        md.append(f"| {r[1]} | {r[2]:,} | {r[3]:,} | {r[4]:,} | "
                  + ("rate not meaningful [note 1]" if r[1] == "MISSING" else f2(r[5]) or "role absent") + " |")

    md += ["", f"MISSING, 2017 (data-quality context, not a role KPI): {missing17_events} rejection "
           f"events in {missing17_cases} distinct cases. See [note 1]."]
    md += ["", f"### Wait before each step ({ONLY}, complete cases)", "",
           "| Step | Events | Cases | Median days | P90 days |", "|---|---:|---:|---:|---:|"]
    for r in wait_rows:
        md.append(f"| {r[1]} | {r[2]:,} | {r[3]:,} | {f2(r[4])} | {f2(r[5])} |")

    md += ["", "### Top 10 paths, 2018", "", "| Rank | Cases | % of 2018 cases | Path |",
           "|---:|---:|---:|---|"]
    for i, (v, n) in enumerate(top, 1):
        md.append(f"| {i} | {n:,} | {f2(pct(n, ncs))} | {v} |")

    log_end = max(e["timestamp"] for evs in events.values() for e in evs)[:10]
    inc18 = [c for c in cases if in_year(c, Y) and c not in complete]
    inc18_open = [c for c in inc18 if c in submitted]
    inc18_open_first = min(events[c][-1]["timestamp"] for c in inc18_open)[:10]
    inc18_open_last = max(events[c][-1]["timestamp"] for c in inc18_open)[:10]
    md += ["", "## Limitations", "",
           "- 2017 covers two departments only (dataset description), and its roles differ from "
           "2018's (decision 1). It cannot be checked from the log, which has no department field. "
           "2017 vs 2018 is not a trend, and role-level KPIs are 2018 only.",
           f"- Cases are assigned to the year of their first submission. The log runs to {log_end}. "
           f"The {len(inc18_open)} incomplete {Y} cases that aren't drafts last moved between "
           f"{inc18_open_first} and {inc18_open_last}; the other {len(inc18) - len(inc18_open)} "
           f"incomplete {Y} cases are never-submitted drafts.",
           f"- {len(paid_no_submit)} paid case(s) have no SUBMITTED event and so no cycle time: "
           + ", ".join(paid_no_submit) + ".",
           f"- {missing_note}",
           "- Timestamps record when a step was completed, not when work on it started, so a "
           "\"wait\" includes both queue time and working time.",
           f"- {ADMIN_WORDING}. Timestamps are precise {precision}. This is treated as a "
           "data limitation (system-recorded), not review time (decision 5); time spent before "
           "that step is not visible in the log.",
           "- The log can't show whether a zero amount was entered on purpose or written as a "
           "default, so the reason zero-amount cases are rejected more often is not established. "
           "The pattern (no zero-amount case paid; every one a draft or rejected) suggests a zero "
           "amount may be a placeholder for a declaration without a real amount, which the log "
           "can't confirm.",
           "- `org:resource` is anonymised (STAFF MEMBER / SYSTEM only), so workload per person "
           "cannot be measured.",
           "- Amounts were anonymised by the publisher and no currency is given.",
           "- Durations use calendar days, including weekends and holidays.",
           "- 10 events share an exact timestamp with another event in the same case; their "
           "order follows the raw file (see `docs/data-cleaning-log.md`).",
           ""]
    with open(REPORT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md))


if __name__ == "__main__":
    main()
