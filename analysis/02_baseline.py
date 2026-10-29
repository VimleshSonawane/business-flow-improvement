"""Baseline KPIs for BPI Challenge 2020 Domestic Declarations.

Reads data/processed/events.csv and data/processed/cases.csv (built by
analysis/01_clean.py) and writes:
  data/outputs/tableau/*.csv     tables for Tableau
  docs/baseline-kpi-report.md    deliverable D3

Measures only; no recommendations. Decisions applied are in docs/decisions.md.
Standard library only. Outputs are deterministic.

Run from anywhere:  python3 analysis/02_baseline.py
"""

import collections
import csv
import os
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

SUBMIT = "Declaration SUBMITTED by EMPLOYEE"
SAVED = "Declaration SAVED by EMPLOYEE"
FINAL = "Declaration FINAL_APPROVED by SUPERVISOR"
REQUEST = "Request Payment"
PAID = "Payment Handled"
EMP_REJECT = "Declaration REJECTED by EMPLOYEE"
APPROVER_ROLES = ["ADMINISTRATION", "PRE_APPROVER", "BUDGET OWNER", "SUPERVISOR"]
REJECT_ROLES = APPROVER_ROLES + ["MISSING"]
MONEY = "Amount (units as in source)"


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def days(a, b):
    return (b - a).total_seconds() / 86400


def pct_point(values, p):
    """Percentile with linear interpolation between closest ranks (Excel PERCENTILE.INC)."""
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
    return "" if x is None else f"{x:.2f}"


def pct(n, d):
    return None if not d else 100 * n / d


def write_csv(name, cols, rows):
    with open(os.path.join(OUT_DIR, name), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(cols)
        w.writerows(rows)


def load():
    cases = collections.OrderedDict()
    with open(CASES_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            cases[r["case_id"]] = r
    events = collections.defaultdict(list)
    with open(EVENTS_CSV, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            r["_t"] = ts(r["timestamp"])
            events[r["case_id"]].append(r)
    for evs in events.values():
        evs.sort(key=lambda r: int(r["event_order"]))
    return cases, events


def main():
    cases, events = load()
    os.makedirs(OUT_DIR, exist_ok=True)

    # Case sets.
    def in_year(cid, year):
        return year == "all" or cases[cid]["year"] == year

    submitted = {c for c, evs in events.items() if any(e["activity"] == SUBMIT for e in evs)}
    complete = {c for c, r in cases.items() if r["is_complete"] == "yes"}
    paid = {c for c, r in cases.items() if r["end_status"] == "paid"}
    drafts = {c for c, evs in events.items()
              if any(e["activity"] == SAVED for e in evs) and c not in submitted}

    kpis = []  # (id, kpi, year, case set, denominator text, denominator, value, unit)

    def add(kid, name, year, case_set, den_text, den, value, unit):
        if not den:
            return  # step or role absent in this year; the CSVs keep the empty row
        kpis.append((kid, name, year, case_set, den_text, den, value, unit))

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
        cycle[c] = days(min(subs), max(pays))
    for c in cases:
        if c in cycle:
            r = cases[c]
            cycle_rows.append([c, r["year"], f"{cycle[c]:.4f}", r["rejected_at_least_once"],
                               sum(1 for e in events[c] if e["activity"] == SUBMIT) - 1,
                               r["event_count"], r["amount"], r["amount_flag"]])
    write_csv("cycle_time_by_case.csv",
              ["case_id", "year", "cycle_days", "rejected_at_least_once", "resubmissions",
               "event_count", "amount_units_as_in_source", "amount_flag"], cycle_rows)
    paid_no_submit = [c for c in cases if c in paid and c not in cycle]

    for y in YEARS:
        vals = [v for c, v in cycle.items() if in_year(c, y)]
        cs = f"paid cases, start year {y}"
        den = "paid cases with a submission"
        add("1a", "Cycle time, median", y, cs, den, len(vals), f2(pct_point(vals, 50)), "days")
        add("1b", "Cycle time, mean", y, cs, den, len(vals), f2(mean(vals)), "days")
        add("1c", "Cycle time, P75", y, cs, den, len(vals), f2(pct_point(vals, 75)), "days")
        add("1d", "Cycle time, P90", y, cs, den, len(vals), f2(pct_point(vals, 90)), "days")

    # 2. Transitions (complete cases only, per decision 4).
    trans_rows = []
    trans = {}
    for y in YEARS + ["all"]:
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
                               f2(pct_point(k["d"], 50)), f2(pct_point(k["d"], 90))])
    write_csv("transitions.csv",
              ["year", "from_activity", "to_activity", "case_count", "transition_count",
               "median_days", "p90_days"], trans_rows)

    # 3. Time until each role acts (complete cases): previous event -> this event.
    steps = APPROVER_ROLES + [REQUEST, PAID]
    wait_rows = []
    waits = {}
    for y in YEARS:
        acc = collections.defaultdict(list)
        acc_cases = collections.defaultdict(set)
        for c in cases:
            if c not in complete or not in_year(c, y):
                continue
            evs = events[c]
            for prev, e in zip(evs, evs[1:]):
                step = e["activity"] if e["activity"] in (REQUEST, PAID) else e["org:role"]
                if step in steps:
                    acc[step].append(days(prev["_t"], e["_t"]))
                    acc_cases[step].add(c)
        waits[y] = acc
        for s in steps:
            d = acc[s]
            wait_rows.append([y, s, len(d), len(acc_cases[s]), f2(pct_point(d, 50)),
                              f2(pct_point(d, 90))])
            label = s if s in (REQUEST, PAID) else f"{s} acts"
            add("3", f"Wait before {label}, median / P90", y, f"complete cases, start year {y}",
                "events of this step", len(d),
                f"{f2(pct_point(d, 50))} / {f2(pct_point(d, 90))}", "days")
    write_csv("role_wait_times.csv",
              ["year", "step", "events", "cases", "median_days", "p90_days"], wait_rows)

    # 4. Rejections (submitted cases, all end statuses).
    rej_rows = []
    rej = {}
    for y in YEARS:
        sub_y = [c for c in cases if c in submitted and in_year(c, y)]
        n_rej = sum(1 for c in sub_y if cases[c]["rejected_at_least_once"] == "yes")
        rej[y] = (n_rej, len(sub_y))
        add("4a", "Cases rejected at least once", y, f"submitted cases, start year {y}",
            "submitted cases", len(sub_y), f2(pct(n_rej, len(sub_y))), "%")
        for role in REJECT_ROLES:
            reached = [c for c in sub_y if any(e["org:role"] == role for e in events[c])]
            n = sum(1 for c in sub_y for e in events[c]
                    if e["activity"] == f"Declaration REJECTED by {role}")
            ncases = sum(1 for c in sub_y if any(
                e["activity"] == f"Declaration REJECTED by {role}" for e in events[c]))
            rej_rows.append([y, role, n, ncases, len(reached), f2(pct(n, len(reached)))])
            add("4b", f"Rejections by {role} per 100 cases reaching {role}", y,
                f"submitted cases reaching {role}, start year {y}", f"cases with a {role} event",
                len(reached), f2(pct(n, len(reached))), f"per 100 cases ({n} rejections)")
    write_csv("rejections_by_role.csv",
              ["year", "role", "rejections", "cases_with_rejection", "cases_reaching_role",
               "rejections_per_100_cases_reaching_role"], rej_rows)

    # 5. Rework.
    rework = {}
    for y in YEARS:
        sub_y = [c for c in cases if c in submitted and in_year(c, y)]
        resub = {c: sum(1 for e in events[c] if e["activity"] == SUBMIT) - 1 for c in sub_y}
        n_resub = sum(resub.values())
        n_cases = sum(1 for v in resub.values() if v >= 1)
        with_r = [v for c, v in cycle.items() if in_year(c, y)
                  and cases[c]["rejected_at_least_once"] == "yes"]
        without_r = [v for c, v in cycle.items() if in_year(c, y)
                     and cases[c]["rejected_at_least_once"] == "no"]
        rework[y] = (n_resub, n_cases, len(sub_y), with_r, without_r)
        cs = f"submitted cases, start year {y}"
        add("5a", "Resubmissions (SUBMITTED events after the first)", y, cs,
            "submitted cases", len(sub_y), str(n_resub), "events")
        add("5b", "Cases with 1+ resubmission", y, cs, "submitted cases", len(sub_y),
            f2(pct(n_cases, len(sub_y))), "%")
        add("5c", "Cycle time median, paid WITH a rejection", y, f"paid cases rejected 1+, start year {y}",
            "paid cases rejected at least once", len(with_r), f2(pct_point(with_r, 50)), "days")
        add("5d", "Cycle time median, paid WITHOUT a rejection", y,
            f"paid cases never rejected, start year {y}", "paid cases never rejected",
            len(without_r), f2(pct_point(without_r, 50)), "days")

    # 6. Variants (all cases of the year, any end status).
    var_rows = []
    variants = {}
    for y in YEARS:
        cs_y = [c for c in cases if in_year(c, y)]
        cnt = collections.Counter(" > ".join(e["activity"] for e in events[c]) for c in cs_y)
        top = sorted(cnt.items(), key=lambda x: (-x[1], x[0]))[:10]
        variants[y] = (top, len(cs_y), len(cnt))
        for i, (v, n) in enumerate(top, 1):
            var_rows.append([y, i, n, f2(pct(n, len(cs_y))), len(v.split(" > ")), v])
        add("6", "Cases on the most common path", y, f"all cases, start year {y}", "all cases",
            len(cs_y), f2(pct(top[0][1], len(cs_y))), f"% ({len(cnt)} distinct paths)")
    write_csv("variants_top10.csv",
              ["year", "rank", "cases", "pct_of_cases", "steps", "variant"], var_rows)

    # 7. Compliance (all cases, both years).
    flags = []
    for c in cases:
        evs = events[c]
        acts = [e["activity"] for e in evs]
        if PAID not in acts:
            continue
        t_pay = min(e["_t"] for e in evs if e["activity"] == PAID)
        if REQUEST not in acts:
            flags.append([c, cases[c]["year"], "payment_without_request",
                          "Payment Handled with no Request Payment event"])
        finals = [e["_t"] for e in evs if e["activity"] == FINAL]
        if not finals:
            flags.append([c, cases[c]["year"], "payment_without_final_approval",
                          "Payment Handled with no FINAL_APPROVED by SUPERVISOR event"])
        elif t_pay < min(finals):
            flags.append([c, cases[c]["year"], "payment_before_final_approval",
                          "Payment Handled before the first FINAL_APPROVED by SUPERVISOR"])
        if acts.count(PAID) > 1:
            flags.append([c, cases[c]["year"], "paid_more_than_once",
                          f"{acts.count(PAID)} Payment Handled events"])
        if acts[-1] != PAID:
            flags.append([c, cases[c]["year"], "events_after_payment",
                          "Payment Handled is not the last event; last is " + acts[-1]])
    write_csv("compliance_flags.csv", ["case_id", "year", "check", "detail"], flags)
    checks = ["payment_without_request", "payment_without_final_approval",
              "payment_before_final_approval", "paid_more_than_once", "events_after_payment"]
    with_pay = sum(1 for c in cases if any(e["activity"] == PAID for e in events[c]))
    flag_by = {k: [f for f in flags if f[2] == k] for k in checks}
    for k in checks:
        add("7", f"Compliance: {k}", "all", "cases with a Payment Handled event, both years",
            "cases with a Payment Handled event", with_pay, str(len(flag_by[k])), "cases")

    # 8. Abandoned drafts and incomplete cases.
    for y in YEARS:
        cs_y = [c for c in cases if in_year(c, y)]
        d = sum(1 for c in drafts if in_year(c, y))
        inc = sum(1 for c in cs_y if c not in complete)
        add("8a", "Drafts saved, never submitted", y, f"all cases, start year {y}", "all cases",
            len(cs_y), str(d), "cases")
        add("8b", "Incomplete cases (no clear end)", y, f"all cases, start year {y}", "all cases",
            len(cs_y), str(inc), "cases")
    incomplete_last = collections.Counter(
        (cases[c]["year"], cases[c]["last_activity"]) for c in cases if c not in complete)

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
        f2(pct_point([month[m] for m in months], 50)), "events per month")

    # 10. Money (zero amounts excluded).
    money = {}
    for y in YEARS:
        cs_y = [c for c in cases if in_year(c, y) and cases[c]["amount_flag"] == ""]
        amts = [float(cases[c]["amount"]) for c in cs_y]
        rej_amt = sum(float(cases[c]["amount"]) for c in cs_y
                      if cases[c]["rejected_at_least_once"] == "yes")
        tot = sum(amts)
        money[y] = (len(cs_y), pct_point(amts, 50), rej_amt, tot)
        cs = f"cases with amount > 0, start year {y}"
        add("10a", f"Median amount, {MONEY}", y, cs, "cases with amount > 0", len(cs_y),
            f2(pct_point(amts, 50)), "units as in source")
        add("10b", f"Total amount in cases rejected 1+, {MONEY}", y, cs,
            "cases with amount > 0", len(cs_y), f2(rej_amt),
            f"units as in source ({f2(pct(rej_amt, tot))}% of total {f2(tot)})")

    # Payment weekday and speed of the first ADMINISTRATION step (2018, complete cases).
    wd_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pay_wd = collections.Counter(
        e["_t"].astimezone(LOCAL_TZ).weekday() for c in cases if in_year(c, MAIN_YEAR)
        for e in events[c] if e["activity"] == PAID)
    n_pay = sum(pay_wd.values())
    mon_thu = pay_wd[0] + pay_wd[3]
    add("3b", "Payment Handled events on a Monday or Thursday", MAIN_YEAR,
        f"Payment Handled events, cases starting {MAIN_YEAR} (Dutch time)", "Payment Handled events",
        n_pay, f2(pct(mon_thu, n_pay)), "%")
    admin_sec = [(e["_t"] - prev["_t"]).total_seconds()
                 for c in cases if c in complete and in_year(c, MAIN_YEAR)
                 for prev, e in zip(events[c], events[c][1:])
                 if prev["activity"] == SUBMIT and e["org:role"] == "ADMINISTRATION"]
    add("3c", "Submission to ADMINISTRATION action, median", MAIN_YEAR,
        f"complete cases, start year {MAIN_YEAR}", "SUBMITTED then ADMINISTRATION transitions",
        len(admin_sec), f2(pct_point(admin_sec, 50)), "seconds")
    kpis.sort(key=lambda k: (k[2] != MAIN_YEAR, k[2]))  # stable: 2018, then 2017, then all
    write_csv("kpi_summary.csv",
              ["kpi_id", "kpi", "year", "case_set", "denominator_description", "denominator",
               "value", "unit"], kpis)

    # Report.
    Y = MAIN_YEAR
    ct = {y: [v for c, v in cycle.items() if in_year(c, y)] for y in YEARS}
    nr, nrc, nsub, wr, wor = rework[Y]
    top, ncs, nvar = variants[Y]
    rj = {r[1]: r for r in rej_rows if r[0] == Y}
    t18 = trans[Y]
    slowest = sorted(((a, b, k) for (a, b), k in t18.items()
                      if len(k["cases"]) >= 100 and k["d"]),
                     key=lambda x: (-pct_point(x[2]["d"], 50), x[0], x[1]))[:3]
    w18 = waits[Y]

    md = ["# Baseline KPI report — BPI Challenge 2020, Domestic Declarations (D3)", "",
          "Generated by `analysis/02_baseline.py` from `data/processed/`. Do not edit by hand; "
          "re-run the script. Measures only, no recommendations. Decisions applied: "
          "[`docs/decisions.md`](decisions.md).", "",
          "**Main view: cases that started in 2018.** 2017 is shown separately and labelled; it "
          "covers two departments only, so 2017 vs 2018 is not a trend.", "",
          "## Definitions", "",
          "- **Year**: the start year of the case (first event, Dutch local time).",
          "- **Submitted case**: has at least one `Declaration SUBMITTED by EMPLOYEE`.",
          "- **Complete case**: last event is `Payment Handled` (paid) or "
          "`Declaration REJECTED by EMPLOYEE` (closed after rejection).",
          "- **Paid case**: last event is `Payment Handled`.",
          "- **Cycle time**: first `Declaration SUBMITTED by EMPLOYEE` to `Payment Handled`, "
          "paid cases only, in days.",
          "- **Rejected at least once**: one or more rejections by ADMINISTRATION, PRE_APPROVER, "
          "BUDGET OWNER, SUPERVISOR or MISSING (the employee's own `REJECTED by EMPLOYEE` step "
          "is not counted as a rejection).",
          "- **Resubmission**: any `SUBMITTED` event after the first in a case.",
          "- **Wait before a step**: time from the previous event in the case to that step; "
          "for approver roles, any event by that role (approve or reject).",
          "- **Percentiles**: linear interpolation (same as Excel `PERCENTILE.INC`).",
          f"- **Money**: `{MONEY}`. The source states no currency. Cases with amount 0 are "
          "excluded from money figures only.", "",
          "## KPI table", "",
          "| ID | KPI | Year | Filter (case set) | Denominator | Value | Unit |",
          "|---|---|---|---|---:|---:|---|"]
    for k in kpis:
        md.append(f"| {k[0]} | {k[1]} | {k[2]} | {k[3]} | {k[5]:,} ({k[4]}) | {k[6]} | {k[7]} |")

    md += ["", "## Findings (2018 main view unless labelled)", ""]
    find = []
    find.append(
        f"**Paid cases take a median of {f2(pct_point(ct[Y], 50))} days from first submission "
        f"to payment, but 1 in 10 takes more than {f2(pct_point(ct[Y], 90))} days** "
        f"(P75 {f2(pct_point(ct[Y], 75))}, mean {f2(mean(ct[Y]))}; "
        f"denominator: {len(ct[Y]):,} paid 2018 cases).")
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
        f"**ADMINISTRATION does most of the rejecting**: {a[2]:,} rejections, "
        f"{a[5]} per 100 of the {a[4]:,} 2018 cases it handled. Other roles: "
        + "; ".join(f"{r} {rj[r][5]} per 100 ({rj[r][2]:,} rejections, {rj[r][4]:,} cases)"
                    for r in ["SUPERVISOR", "PRE_APPROVER", "BUDGET OWNER", "MISSING"]
                    if rj[r][4]) + ". PRE_APPROVER and MISSING do not appear in 2018 cases.")
    find.append(
        f"**Among the steps, the longest median wait is before `Payment Handled`.** Median wait before "
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
        f"**ADMINISTRATION acts within seconds of submission**: median "
        f"{f2(pct_point(admin_sec, 50))} seconds from `SUBMITTED` to the next ADMINISTRATION "
        f"event ({len(admin_sec):,} transitions, complete 2018 cases); P90 "
        f"{f2(pct_point(admin_sec, 90) / 60)} minutes. This looks like when the step was "
        "recorded rather than real review time; see limitations.")
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
    find.append(
        "**Compliance flags** (cases with a payment, both years, denominator "
        f"{with_pay:,}): " + "; ".join(f"{k.replace('_', ' ')} {len(flag_by[k])}" for k in checks)
        + ". Case ids are listed below and in `compliance_flags.csv`.")
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
        + ", ".join(drafts_done) + "). By start year and last activity: "
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

    md += ["", "### Compliance case ids", ""]
    for k in checks:
        ids = [f[0] for f in flag_by[k]]
        md.append(f"- **{k}** ({len(ids)}): " + (", ".join(ids) if ids else "none"))

    md += ["", "### Top 10 paths, 2018", "", "| Rank | Cases | % of 2018 cases | Path |",
           "|---:|---:|---:|---|"]
    for i, (v, n) in enumerate(top, 1):
        md.append(f"| {i} | {n:,} | {f2(pct(n, ncs))} | {v} |")

    md += ["", "## Limitations", "",
           "- 2017 covers two departments only (dataset description). It cannot be checked "
           "from the log, which has no department field. 2017 vs 2018 is not a trend.",
           "- Cases are assigned to the year they started. Cases started late in 2018 may be "
           "cut off by the end of the extract (last event 2019-06-17) and appear incomplete.",
           f"- {len(paid_no_submit)} paid case(s) have no SUBMITTED event and so no cycle time: "
           + ", ".join(paid_no_submit) + ".",
           "- `Declaration REJECTED by MISSING` is the only event with role MISSING, so its "
           "\"per 100 cases reaching the role\" can exceed 100 and is not comparable with the "
           "other roles.",
           "- Timestamps record when a step was completed, not when work on it started, so a "
           "\"wait\" includes both queue time and working time.",
           "- The first approval step often follows submission within seconds, which suggests "
           "the SUBMITTED timestamp may be recorded late (close to the first approval). Time "
           "spent before that is not visible in the log.",
           "- `org:resource` is anonymised (STAFF MEMBER / SYSTEM only), so workload per person "
           "cannot be measured.",
           "- Amounts were anonymised by the publisher and no currency is given.",
           "- Durations use calendar days, including weekends and holidays.",
           "- 10 events share an exact timestamp with another event in the same case; their "
           "order follows the raw file (see `docs/data-cleaning-log.md`).",
           ""]
    with open(REPORT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md))
    print("\n".join(md[md.index("## KPI table"):]))


if __name__ == "__main__":
    main()
