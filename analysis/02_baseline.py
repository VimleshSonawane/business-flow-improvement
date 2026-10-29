"""Baseline KPIs for the BPI Challenge 2020 Domestic Declarations log (deliverable D3).

Reads data/processed/events.csv and data/processed/cases.csv (written by analysis/01_clean.py) and writes:
  data/outputs/tableau/*.csv     tables for Tableau
  docs/baseline-kpi-report.md    KPI table, findings, limitations

Measures only: no recommendations. Decisions and definitions: docs/decisions.md.
Deterministic: no randomness, fixed sort orders, no run timestamps in any output.
Running it twice gives byte-identical files.

Run from anywhere:  python3 analysis/02_baseline.py
"""

import os
import platform
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVENTS_CSV = os.path.join(ROOT, "data", "processed", "events.csv")
CASES_CSV = os.path.join(ROOT, "data", "processed", "cases.csv")
OUT = os.path.join(ROOT, "data", "outputs", "tableau")
REPORT = os.path.join(ROOT, "docs", "baseline-kpi-report.md")

# Checks against the raw log (see docs/data-cleaning-log.md and the input check in the report).
EXPECT_CASES, EXPECT_EVENTS, EXPECT_YEARS = 10500, 56437, {2017: 2240, 2018: 8260}

SUBMIT = "Declaration SUBMITTED by EMPLOYEE"
SAVED = "Declaration SAVED by EMPLOYEE"
PAID = "Payment Handled"
REQUEST = "Request Payment"
FINAL = "Declaration FINAL_APPROVED by SUPERVISOR"
EMP_REJECT = "Declaration REJECTED by EMPLOYEE"
REJECT_PREFIX = "Declaration REJECTED by "
APPROVER_ROLES = ["ADMINISTRATION", "PRE_APPROVER", "BUDGET OWNER", "SUPERVISOR"]
MAIN_YEAR = 2018
MONEY = "Amount (units as in source)"
RESUB_KPI = "Resubmissions (submission events after a case's first)"


def days(delta):
    """Fractional days from a timedelta Series or scalar."""
    return delta / pd.Timedelta(days=1)


def stats(values):
    """n, median, mean, P75, P90 with numpy's default (linear) percentile method; no rounding."""
    a = np.asarray(values, dtype=float)
    if a.size == 0:
        return {"n": 0, "median": np.nan, "mean": np.nan, "p75": np.nan, "p90": np.nan}
    return {"n": int(a.size), "median": float(np.percentile(a, 50)), "mean": float(a.mean()),
            "p75": float(np.percentile(a, 75)), "p90": float(np.percentile(a, 90))}


def load():
    ev = pd.read_csv(EVENTS_CSV, dtype=str, keep_default_na=False)
    ca = pd.read_csv(CASES_CSV, dtype=str, keep_default_na=False)
    ev["event_order"] = ev["event_order"].astype(int)
    # event_order: timestamp order, ties kept in file order (analysis/01_clean.py)
    ev = ev.sort_values(["case_id", "event_order"], kind="mergesort").reset_index(drop=True)
    # Timestamps carry their own offset; durations come from the absolute (UTC) instant.
    ev["ts"] = pd.to_datetime(ev["timestamp"], utc=True, format="%Y-%m-%dT%H:%M:%SZ")
    # Calendar fields in the source's local time (the offset written with each timestamp).
    ev["local_year"] = ev["timestamp_original"].str[:4].astype(int)
    ev["local_month"] = ev["timestamp_original"].str[:7]
    return ev, ca


def check_inputs(ev, ca, year):
    found = {"cases": int(ca["case_id"].nunique()), "events": len(ev),
             "years": {int(y): int(n) for y, n in year.value_counts().sort_index().items()}}
    problems = []
    if found["cases"] != EXPECT_CASES or len(ca) != EXPECT_CASES:
        problems.append(f"cases {found['cases']} (cases.csv rows {len(ca)}), expected {EXPECT_CASES}")
    if found["events"] != EXPECT_EVENTS:
        problems.append(f"events {found['events']}, expected {EXPECT_EVENTS}")
    if found["years"] != EXPECT_YEARS:
        problems.append(f"cases per year {found['years']}, expected {EXPECT_YEARS}")
    if set(ev["case_id"]) != set(ca["case_id"]):
        problems.append("case ids in events.csv and cases.csv differ")
    if problems:
        sys.exit("STOP: processed files don't match the raw log: " + "; ".join(problems))
    return found


def build_cases(ev, ca):
    g = ev.groupby("case_id", sort=True)
    c = pd.DataFrame(index=sorted(ev["case_id"].unique()))
    c.index.name = "case_id"
    sub = ev[ev["activity"] == SUBMIT].groupby("case_id")
    first_sub = sub["ts"].min()
    first_sub_local_year = sub["local_year"].first()
    c["year"] = g["local_year"].first()
    c.loc[first_sub_local_year.index, "year"] = first_sub_local_year
    c["year"] = c["year"].astype(int)
    c["submitted"] = c.index.isin(first_sub.index)
    c["first_submission"] = first_sub.reindex(c.index)
    c["submissions"] = sub.size().reindex(c.index).fillna(0).astype(int)
    c["resubmissions"] = (c["submissions"] - 1).clip(lower=0)
    pay = ev[ev["activity"] == PAID].groupby("case_id")["ts"]
    c["payments_handled"] = pay.size().reindex(c.index).fillna(0).astype(int)
    c["paid"] = c["payments_handled"] > 0
    c["payment_handled"] = pay.min().reindex(c.index)
    c["last_activity"] = g["activity"].last()
    c["event_count"] = g.size()
    c["saved"] = c.index.isin(ev.loc[ev["activity"] == SAVED, "case_id"])
    rej = ev[ev["activity"].str.startswith(REJECT_PREFIX) & (ev["activity"] != EMP_REJECT)]
    c["approver_rejections"] = rej.groupby("case_id").size().reindex(c.index).fillna(0).astype(int)
    c["rejected_at_least_once"] = c["approver_rejections"] > 0
    # Status: paid first (a paid case is complete even if its last event is something else).
    last_is_other_reject = c["last_activity"].str.startswith(REJECT_PREFIX) & (c["last_activity"] != EMP_REJECT)
    c["status"] = np.select(
        [c["paid"], c["last_activity"] == EMP_REJECT, ~c["submitted"], last_is_other_reject],
        ["paid", "closed_by_employee_after_rejection", "incomplete_never_submitted",
         "incomplete_rejected_no_employee_response"],
        default="incomplete_other")
    c["complete"] = c["status"].isin(["paid", "closed_by_employee_after_rejection"])
    c["cycle_days"] = days(c["payment_handled"] - c["first_submission"]).where(c["paid"] & c["submitted"])
    c["variant"] = g["activity"].agg(" > ".join)
    amt = ca.set_index("case_id")["amount"].reindex(c.index)
    c["amount"] = pd.to_numeric(amt, errors="coerce")
    c["amount_is_zero"] = c["amount"] == 0
    return c


def main():
    ev, ca = load()
    cases = build_cases(ev, ca)
    found = check_inputs(ev, ca, cases["year"])
    ev = ev.join(cases[["year"]], on="case_id")
    os.makedirs(OUT, exist_ok=True)
    years = [MAIN_YEAR, 2017]
    rows = []  # kpi_summary

    def add(kpi_id, kpi, year, case_set, denom_label, denom, value, unit, numerator=""):
        rows.append({"kpi_id": kpi_id, "kpi": kpi, "year": year, "case_set": case_set,
                     "denominator_label": denom_label, "denominator": denom, "numerator": numerator,
                     "value": value, "unit": unit})

    # ---- completeness (context for every duration measure)
    for y in years:
        cy = cases[cases["year"] == y]
        for s, n in cy["status"].value_counts().sort_index().items():
            add("0", f"Cases by status: {s}", y, "all cases in year", "cases in year", len(cy), n / len(cy) * 100, "% of cases", n)

    # ---- 1 cycle time (paid cases with a submission)
    for y in years:
        cy = cases[(cases["year"] == y) & cases["paid"]]
        s = stats(cy["cycle_days"].dropna())
        for k in ["median", "mean", "p75", "p90"]:
            add("1", f"Cycle time, first submission to Payment Handled: {k}", y,
                "paid cases with a submission", "paid cases with a submission", s["n"], s[k], "days")

    # ---- 2 transitions (process map)
    ev["next_activity"] = ev.groupby("case_id")["activity"].shift(-1)
    ev["gap_days"] = days(ev.groupby("case_id")["ts"].shift(-1) - ev["ts"])
    pairs = ev.dropna(subset=["next_activity"])
    tr = []
    for (y, a, b), grp in pairs.groupby(["year", "activity", "next_activity"], sort=True):
        s = stats(grp["gap_days"])
        tr.append({"year": y, "from_activity": a, "to_activity": b, "cases": grp["case_id"].nunique(),
                   "transitions": len(grp), "median_days": s["median"], "p90_days": s["p90"], "mean_days": s["mean"]})
    tr = pd.DataFrame(tr).sort_values(["year", "cases", "from_activity", "to_activity"], ascending=[False, False, True, True], kind="mergesort")
    tr.to_csv(os.path.join(OUT, "transitions.csv"), index=False)

    # ---- 3 time until each role acts (from the previous event in the case)
    ev["wait_days"] = days(ev["ts"] - ev.groupby("case_id")["ts"].shift(1))
    acted = ev.dropna(subset=["wait_days"]).copy()
    acted["actor"] = np.where(acted["activity"] == REQUEST, "Request Payment (system)",
                     np.where(acted["activity"] == PAID, "Payment Handled (system)", acted["org:role"]))
    rw = []
    for y in years:
        for actor in APPROVER_ROLES + ["Request Payment (system)", "Payment Handled (system)"]:
            grp = acted[(acted["year"] == y) & (acted["actor"] == actor)]
            s = stats(grp["wait_days"])
            rw.append({"year": y, "actor": actor, "events": s["n"], "cases": grp["case_id"].nunique(),
                       "median_days": s["median"], "p90_days": s["p90"], "mean_days": s["mean"]})
    rw = pd.DataFrame(rw)
    rw.to_csv(os.path.join(OUT, "role_wait_times.csv"), index=False)
    for r in rw[rw["year"] == MAIN_YEAR].itertuples():
        add("3", f"Wait before {r.actor} acts: median", r.year, "events by that actor (not a case's first event)", "events", r.events, r.median_days, "days")
        add("3", f"Wait before {r.actor} acts: P90", r.year, "events by that actor (not a case's first event)", "events", r.events, r.p90_days, "days")

    # ---- 4 rejections
    rej_rows = []
    for y in years:
        cy = cases[cases["year"] == y]
        sub = cy[cy["submitted"]]
        add("4", "Submitted cases rejected at least once (by an approver)", y, "submitted cases (drafts never submitted excluded)",
            "submitted cases", len(sub), sub["rejected_at_least_once"].mean() * 100, "% of cases", int(sub["rejected_at_least_once"].sum()))
        ey = ev[ev["year"] == y]
        for role in ["ADMINISTRATION", "PRE_APPROVER", "BUDGET OWNER", "SUPERVISOR", "MISSING", "EMPLOYEE"]:
            r_ev = ey[ey["activity"] == REJECT_PREFIX + role]
            reached = ey.loc[ey["org:role"] == role, "case_id"].nunique()
            rej_rows.append({"year": y, "role": role,
                             "counted_as_approver_rejection": "no (employee response to a rejection)" if role == "EMPLOYEE" else "yes",
                             "rejection_events": len(r_ev), "cases_with_rejection": r_ev["case_id"].nunique(),
                             "cases_reached_role": reached,
                             "rejections_per_100_cases_reached": len(r_ev) / reached * 100 if reached else np.nan})
    rj = pd.DataFrame(rej_rows)
    rj.to_csv(os.path.join(OUT, "rejections_by_role.csv"), index=False)
    for r in rj[rj["year"] == MAIN_YEAR].itertuples():
        add("4", f"Rejections by {r.role} per 100 cases that reached that role", r.year, "cases with at least one event by that role",
            "cases that reached the role", r.cases_reached_role, r.rejections_per_100_cases_reached, "per 100 cases", r.rejection_events)

    # ---- 5 rework
    for y in years:
        sub = cases[(cases["year"] == y) & cases["submitted"]]
        add("5", RESUB_KPI, y, "submitted cases", "submitted cases", len(sub), int(sub["resubmissions"].sum()), "events")
        add("5", "Submitted cases with 1 or more resubmissions", y, "submitted cases", "submitted cases", len(sub),
            (sub["resubmissions"] > 0).mean() * 100, "% of cases", int((sub["resubmissions"] > 0).sum()))
        paid = cases[(cases["year"] == y) & cases["paid"] & cases["cycle_days"].notna()]
        for flag, label in [(True, "with"), (False, "without")]:
            grp = paid[paid["rejected_at_least_once"] == flag]
            s = stats(grp["cycle_days"])
            add("5", f"Median cycle time, paid cases {label} an approver rejection", y, f"paid cases {label} a rejection",
                f"paid cases {label} a rejection", s["n"], s["median"], "days")

    # ---- 6 variants
    vt = []
    for y in years:
        cy = cases[cases["year"] == y]
        counts = cy.groupby("variant").size().reset_index(name="cases")
        counts["steps"] = counts["variant"].str.count(" > ") + 1
        counts = counts.sort_values(["cases", "variant"], ascending=[False, True], kind="mergesort").head(10)
        counts.insert(0, "rank", range(1, len(counts) + 1))
        counts.insert(0, "year", y)
        counts["pct_of_cases"] = counts["cases"] / len(cy) * 100
        counts["cases_in_year"] = len(cy)
        counts["distinct_variants_in_year"] = cy["variant"].nunique()
        vt.append(counts)
        top = counts.iloc[0]
        add("6", "Cases on the most common path", y, "all cases in year", "cases in year", len(cy), top["pct_of_cases"], "% of cases", int(top["cases"]))
        add("6", "Cases on the top 10 paths", y, "all cases in year", "cases in year", len(cy), counts["cases"].sum() / len(cy) * 100, "% of cases", int(counts["cases"].sum()))
        add("6", "Distinct paths (variants)", y, "all cases in year", "cases in year", len(cy), cy["variant"].nunique(), "paths")
    vt = pd.concat(vt)[["year", "rank", "cases", "pct_of_cases", "cases_in_year", "distinct_variants_in_year", "steps", "variant"]]
    vt.to_csv(os.path.join(OUT, "variants_top10.csv"), index=False)

    # ---- 7 compliance
    flags = []
    for cid, grp in ev.groupby("case_id", sort=True):
        acts = grp["activity"].tolist()
        y = int(grp["year"].iloc[0])
        if PAID in acts:
            pay_i = acts.index(PAID)
            if REQUEST not in acts:
                flags.append({"check": "payment_without_request", "case_id": cid, "year": y, "detail": "Payment Handled with no Request Payment event in the case"})
            if FINAL not in acts[:pay_i]:
                flags.append({"check": "payment_before_final_approval", "case_id": cid, "year": y,
                              "detail": "no final approval anywhere in the case" if FINAL not in acts else "final approval only after Payment Handled"})
            if acts.count(PAID) > 1:
                flags.append({"check": "paid_more_than_once", "case_id": cid, "year": y, "detail": f"{acts.count(PAID)} Payment Handled events"})
        if REQUEST in acts:
            req_i = acts.index(REQUEST)
            if not any("APPROVED" in a for a in acts[:req_i]):
                flags.append({"check": "request_without_prior_approval", "case_id": cid, "year": y, "detail": "no approval event before the first Request Payment"})
    fl = pd.DataFrame(flags, columns=["check", "case_id", "year", "detail"]).sort_values(["check", "year", "case_id"], kind="mergesort")
    fl.to_csv(os.path.join(OUT, "compliance_flags.csv"), index=False)
    for chk, denom_label, base in [("payment_without_request", "paid cases", cases["paid"]),
                                   ("payment_before_final_approval", "paid cases", cases["paid"]),
                                   ("request_without_prior_approval", "cases with a Request Payment", cases.index.isin(ev.loc[ev["activity"] == REQUEST, "case_id"])),
                                   ("paid_more_than_once", "paid cases", cases["paid"])]:
        for y in years + ["all"]:
            sel = base & ((cases["year"] == y) if y != "all" else True)
            n = int((fl["check"] == chk).sum() if y == "all" else ((fl["check"] == chk) & (fl["year"] == y)).sum())
            add("7", f"Compliance: {chk}", y, denom_label, denom_label, int(sel.sum()), n, "cases", n)

    # ---- 8 abandoned drafts
    for y in years:
        cy = cases[cases["year"] == y]
        n = int((cy["saved"] & ~cy["submitted"]).sum())
        add("8", "Drafts saved and never submitted", y, "all cases in year", "cases in year", len(cy), n, "cases", n)

    # ---- 9 monthly volume (2018, local calendar months)
    s18 = ev[(ev["activity"] == SUBMIT) & (ev["local_year"] == MAIN_YEAR)].copy()
    s18["is_first"] = ~s18.duplicated("case_id")
    firsts = ev[ev["activity"] == SUBMIT].drop_duplicates("case_id")
    first_ids = set(zip(firsts["case_id"], firsts["event_order"]))
    s18["is_first"] = [(c, o) in first_ids for c, o in zip(s18["case_id"], s18["event_order"])]
    mv = s18.groupby("local_month").agg(submission_events=("case_id", "size"), first_submissions=("is_first", "sum")).reset_index()
    mv["resubmissions"] = mv["submission_events"] - mv["first_submissions"]
    mv = mv.rename(columns={"local_month": "month"}).sort_values("month")
    mv.to_csv(os.path.join(OUT, "monthly_volume.csv"), index=False)

    # ---- 10 money (zero amounts excluded)
    for y in years:
        cy = cases[cases["year"] == y]
        nz = cy[cy["amount"] > 0]
        add("10", "Cases with a zero amount (excluded from money figures)", y, "all cases in year", "cases in year", len(cy), int(cy["amount_is_zero"].sum()), "cases")
        add("10", f"Median {MONEY}", y, "cases with a non-zero amount", "cases with a non-zero amount", len(nz), float(np.percentile(nz["amount"], 50)), MONEY)
        add("10", f"Total {MONEY}, all cases", y, "cases with a non-zero amount", "cases with a non-zero amount", len(nz), float(nz["amount"].sum()), MONEY)
        rj_amt = float(nz.loc[nz["rejected_at_least_once"], "amount"].sum())
        add("10", f"Total {MONEY} in cases rejected at least once", y, "cases with a non-zero amount, rejected at least once",
            "cases with a non-zero amount", len(nz), rj_amt, MONEY, int(nz["rejected_at_least_once"].sum()))

    # ---- case-level table
    out = cases.reset_index()[["case_id", "year", "status", "complete", "submitted", "paid", "first_submission", "payment_handled",
                               "cycle_days", "submissions", "resubmissions", "approver_rejections", "rejected_at_least_once",
                               "event_count", "last_activity", "amount", "amount_is_zero"]].copy()
    for col in ["first_submission", "payment_handled"]:
        out[col] = out[col].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    out = out.rename(columns={"amount": "amount_units_as_in_source"})
    out.sort_values(["year", "case_id"], kind="mergesort").to_csv(os.path.join(OUT, "cycle_time_by_case.csv"), index=False)

    kpi = pd.DataFrame(rows)
    kpi.to_csv(os.path.join(OUT, "kpi_summary.csv"), index=False)
    write_report(found, cases, kpi, tr, rw, rj, vt, fl, mv, ev)


# ---------------------------------------------------------------- report (rounding happens only here)
def fd(x):
    """Days for the report: very short waits also shown in minutes or seconds."""
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    if x < 1 / 24:
        secs = x * 86400
        return f"{x:.4f} d (about {secs / 60:.0f} min)" if secs >= 90 else f"{x:.4f} d (about {secs:.0f} s)"
    return f"{x:.1f} d"


def fp(x):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.1f}%"


def fm(x):
    return f"{x:,.2f}"


def fn(x):
    return f"{int(x):,}"


def write_report(found, cases, kpi, tr, rw, rj, vt, fl, mv, ev):
    versions = {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__}

    def k(kpi_name, year, col="value"):
        r = kpi[(kpi["kpi"] == kpi_name) & (kpi["year"].astype(str) == str(year))]
        if len(r) != 1:
            raise KeyError(f"{kpi_name} / {year}")
        return r.iloc[0][col]

    Y, P = MAIN_YEAR, 2017
    c18, c17 = cases[cases["year"] == Y], cases[cases["year"] == P]
    sub18, sub17 = c18[c18["submitted"]], c17[c17["submitted"]]
    paid18 = c18[c18["paid"] & c18["cycle_days"].notna()]
    ct = lambda key, y: k(f"Cycle time, first submission to Payment Handled: {key}", y)
    n_ct18, n_ct17 = int(k("Cycle time, first submission to Payment Handled: median", Y, "denominator")), int(k("Cycle time, first submission to Payment Handled: median", P, "denominator"))
    st18 = c18["status"].value_counts()
    st17 = c17["status"].value_counts()
    nz18, nz17 = c18[c18["amount"] > 0], c17[c17["amount"] > 0]
    rej_amt18 = float(nz18.loc[nz18["rejected_at_least_once"], "amount"].sum())
    rej_amt17 = float(nz17.loc[nz17["rejected_at_least_once"], "amount"].sum())
    w = lambda actor, y, col: rw[(rw["actor"] == actor) & (rw["year"] == y)].iloc[0][col]
    r = lambda role, y, col: rj[(rj["role"] == role) & (rj["year"] == y)].iloc[0][col]
    with_r = paid18[paid18["rejected_at_least_once"]]["cycle_days"]
    without_r = paid18[~paid18["rejected_at_least_once"]]["cycle_days"]
    over60 = int((paid18["cycle_days"] > 60).sum())
    v18 = vt[vt["year"] == Y]
    v17 = vt[vt["year"] == P]
    flag_ids = lambda chk: ", ".join(fl.loc[fl["check"] == chk, "case_id"]) or "none"
    flag_n = lambda chk, y="all": int(k(f"Compliance: {chk}", y))
    drafts18, drafts17 = int(k("Drafts saved and never submitted", Y)), int(k("Drafts saved and never submitted", P))
    t18 = tr[tr["year"] == Y]
    direct_pay = t18[(t18["from_activity"] == FINAL) & (t18["to_activity"] == PAID)]
    quick_withdraw = t18[(t18["from_activity"] == SUBMIT) & (t18["to_activity"] == EMP_REJECT)]
    peak = mv.loc[mv["submission_events"].idxmax()]
    low = mv.loc[mv["submission_events"].idxmin()]
    no_resp18 = c18[c18["status"] == "incomplete_rejected_no_employee_response"]["last_activity"].value_counts()
    no_resp17 = c17[c17["status"] == "incomplete_rejected_no_employee_response"]["last_activity"].value_counts()
    last_ts = ev.groupby("case_id")["ts"].max()
    log_end = ev["ts"].max().strftime("%Y-%m-%d")
    open18 = last_ts.reindex(c18[c18["status"] == "incomplete_rejected_no_employee_response"].index)
    no_sub_paid = cases[cases["paid"] & ~cases["submitted"]]

    L = []
    a = L.append
    a("# Baseline KPI report (deliverable D3)")
    a("")
    a("BPI Challenge 2020, Domestic Declarations (travel expense declarations at a university). This report **measures only**; it makes no recommendations. "
      "Decisions and definitions are in [decisions.md](decisions.md). Every number states its denominator and filter. "
      f"**{Y} is the main view.** {P} is shown separately where useful and is **never a trend comparison**: {P} covers two departments only (decision 1).")
    a("")
    a("Built by `analysis/02_baseline.py` from `data/processed/events.csv` and `data/processed/cases.csv`. "
      f"Python {versions['python']}, pandas {versions['pandas']}, numpy {versions['numpy']}. Percentiles use numpy's default (linear) method. "
      "Durations are fractional days between timestamps; each timestamp carries its own UTC offset (+01:00 or +02:00, Dutch winter and summer time), "
      "so durations are exact across clock changes. Year and month use the local time written in the source.")
    a("")
    a(f"**Input check:** {fn(found['cases'])} cases and {fn(found['events'])} events, with {fn(found['years'][P])} cases in {P} and "
      f"{fn(found['years'][Y])} in {Y} by the year definition. All match the raw log.")
    a("")
    a("Money is **Amount (units as in source)**: the data states no currency.")
    a("")
    a(f"## 1. KPI table ({Y} main view)")
    a("")
    a(f"| # | KPI | {Y} | Denominator and filter ({Y}) | {P}, separately (not a trend) |")
    a("|---|---|---|---|---|")
    a(f"| 0 | Cases paid | {fp(st18.get('paid', 0) / len(c18) * 100)} ({fn(st18.get('paid', 0))}) | {fn(len(c18))} cases in {Y} | {fp(st17.get('paid', 0) / len(c17) * 100)} of {fn(len(c17))} |")
    a(f"| 0 | Cases closed by the employee after a rejection | {fp(st18.get('closed_by_employee_after_rejection', 0) / len(c18) * 100)} ({fn(st18.get('closed_by_employee_after_rejection', 0))}) | {fn(len(c18))} cases in {Y} | {fp(st17.get('closed_by_employee_after_rejection', 0) / len(c17) * 100)} of {fn(len(c17))} |")
    inc18 = len(c18) - int(c18["complete"].sum()); inc17 = len(c17) - int(c17["complete"].sum())
    a(f"| 0 | Incomplete cases (excluded from durations) | {fp(inc18 / len(c18) * 100)} ({fn(inc18)}) | {fn(len(c18))} cases in {Y} | {fp(inc17 / len(c17) * 100)} of {fn(len(c17))} |")
    for key, label in [("median", "median"), ("mean", "mean"), ("p75", "P75"), ("p90", "P90")]:
        a(f"| 1 | Cycle time, first submission to Payment Handled: {label} | {fd(ct(key, Y))} | {fn(n_ct18)} paid cases in {Y} with a submission | {fd(ct(key, P))} (n = {fn(n_ct17)}) |")
    a(f"| 2 | Stage timing (process map) | see section 2 | consecutive activity pairs in {Y} cases | `transitions.csv` |")
    for actor in ["ADMINISTRATION", "BUDGET OWNER", "SUPERVISOR", "Request Payment (system)", "Payment Handled (system)", "PRE_APPROVER"]:
        n = int(w(actor, Y, "events")); n17 = int(w(actor, P, "events"))
        a(f"| 3 | Wait until {actor} acts: median / P90 | {fd(w(actor, Y, 'median_days')) + ' / ' + fd(w(actor, Y, 'p90_days')) if n else 'no events'} | {fn(n)} events by this actor in {Y} cases, from the previous event | "
          + (f"{fd(w(actor, P, 'median_days'))} / {fd(w(actor, P, 'p90_days'))} ({fn(n17)} events)" if n17 else "no events") + " |")
    a(f"| 4 | Submitted cases rejected at least once (by an approver) | {fp(k('Submitted cases rejected at least once (by an approver)', Y))} ({fn(k('Submitted cases rejected at least once (by an approver)', Y, 'numerator'))}) | {fn(len(sub18))} submitted cases in {Y} (never-submitted drafts excluded) | {fp(k('Submitted cases rejected at least once (by an approver)', P))} of {fn(len(sub17))} |")
    for role in ["ADMINISTRATION", "SUPERVISOR", "BUDGET OWNER", "PRE_APPROVER", "MISSING"]:
        reached = int(r(role, Y, "cases_reached_role")); reached17 = int(r(role, P, "cases_reached_role"))
        v = f"{fn(r(role, Y, 'rejection_events'))} rejections; {r(role, Y, 'rejections_per_100_cases_reached'):.1f} per 100 cases" if reached else "role not present"
        v17 = f"{fn(r(role, P, 'rejection_events'))}; {r(role, P, 'rejections_per_100_cases_reached'):.1f} per 100 of {fn(reached17)}" if reached17 else "role not present"
        a(f"| 4 | Rejections by {role} | {v} | {fn(reached)} {Y} cases that reached {role} | {v17} |")
    a(f"| 4 | “REJECTED by EMPLOYEE” events (the employee's response, not counted as a rejection) | {fn(r('EMPLOYEE', Y, 'rejection_events'))} | all {fn(len(c18))} {Y} cases | {fn(r('EMPLOYEE', P, 'rejection_events'))} |")
    a(f"| 5 | Resubmissions | {fn(k(RESUB_KPI, Y))} events | {fn(len(sub18))} submitted cases in {Y} | {fn(k(RESUB_KPI, P))} events |")
    a(f"| 5 | Cases with 1 or more resubmissions | {fp(k('Submitted cases with 1 or more resubmissions', Y))} ({fn(k('Submitted cases with 1 or more resubmissions', Y, 'numerator'))}) | {fn(len(sub18))} submitted cases in {Y} | {fp(k('Submitted cases with 1 or more resubmissions', P))} |")
    a(f"| 5 | Median cycle time, paid with / without an approver rejection | {fd(np.percentile(with_r, 50))} / {fd(np.percentile(without_r, 50))} | {fn(len(with_r))} / {fn(len(without_r))} paid cases in {Y} | "
      f"{fd(k('Median cycle time, paid cases with an approver rejection', P))} / {fd(k('Median cycle time, paid cases without an approver rejection', P))} |")
    a(f"| 6 | Cases on the most common path | {fp(k('Cases on the most common path', Y))} ({fn(k('Cases on the most common path', Y, 'numerator'))}) | {fn(len(c18))} cases in {Y} | {fp(k('Cases on the most common path', P))} |")
    a(f"| 6 | Cases on the top 10 paths / distinct paths | {fp(k('Cases on the top 10 paths', Y))} / {fn(k('Distinct paths (variants)', Y))} paths | {fn(len(c18))} cases in {Y} | {fp(k('Cases on the top 10 paths', P))} / {fn(k('Distinct paths (variants)', P))} |")
    for chk, label in [("payment_without_request", "Payments handled with no Request Payment"), ("payment_before_final_approval", "Payments before final approval"),
                       ("request_without_prior_approval", "Requests for payment with no approval before them"), ("paid_more_than_once", "Cases paid more than once")]:
        a(f"| 7 | {label} | {fn(flag_n(chk, Y))} | {fn(k(f'Compliance: {chk}', Y, 'denominator'))} {Y} cases ({'with a Request Payment' if chk == 'request_without_prior_approval' else 'paid'}) | {fn(flag_n(chk, P))} of {fn(k(f'Compliance: {chk}', P, 'denominator'))} |")
    a(f"| 8 | Drafts saved and never submitted | {fn(drafts18)} | {fn(len(c18))} cases in {Y} | {fn(drafts17)} of {fn(len(c17))} |")
    a(f"| 9 | Submissions per month | {fn(low['submission_events'])} to {fn(peak['submission_events'])} (see section 9) | submission events dated in {Y} | — |")
    a(f"| 10 | Median amount | {fm(np.percentile(nz18['amount'], 50))} | {fn(len(nz18))} {Y} cases with a non-zero amount ({fn(int(c18['amount_is_zero'].sum()))} zero-amount cases excluded) | {fm(np.percentile(nz17['amount'], 50))} (n = {fn(len(nz17))}) |")
    a(f"| 10 | Total amount in cases rejected at least once | {fm(rej_amt18)} of {fm(nz18['amount'].sum())} ({fp(rej_amt18 / nz18['amount'].sum() * 100)}) | {fn(int(nz18['rejected_at_least_once'].sum()))} of {fn(len(nz18))} {Y} cases with a non-zero amount | {fm(rej_amt17)} of {fm(nz17['amount'].sum())} |")
    a("")
    a("Notes: amounts are in units as in the source. “Reached a role” means the role has at least one event in the case. "
      "Waits are measured from the case's previous event to the event by that actor; a case's first event has no wait. "
      f"PRE_APPROVER and the “MISSING” role occur only in {P} cases; BUDGET OWNER occurs in {fn(int(r('BUDGET OWNER', P, 'cases_reached_role')))} {P} cases. "
      "The “MISSING” role appears only on rejection events, so its rate per 100 cases reached can exceed 100. "
      f"Cycle time excludes {fn(len(no_sub_paid))} paid case{'s' if len(no_sub_paid) != 1 else ''} with no submission event ({', '.join(no_sub_paid.index)}, year {', '.join(str(y) for y in no_sub_paid['year'])}).")
    a("")
    a(f"## 2. Stage timing on the paths cases take ({Y}, top 15 by cases)")
    a("")
    a("| From | To | Cases | Times it happened | Median | P90 |")
    a("|---|---|---|---|---|---|")
    for t in t18.head(15).itertuples():
        a(f"| {t.from_activity} | {t.to_activity} | {fn(t.cases)} | {fn(t.transitions)} | {fd(t.median_days)} | {fd(t.p90_days)} |")
    a("")
    a(f"Denominator: cases in {Y} that took that step. All pairs, for both years, are in `transitions.csv` (the process-map table).")
    a("")
    a(f"## 6. Top paths ({Y})")
    a("")
    a("| Rank | Cases | % of cases | Steps | Path |")
    a("|---|---|---|---|---|")
    for v in v18.itertuples():
        a(f"| {v.rank} | {fn(v.cases)} | {fp(v.pct_of_cases)} | {v.steps} | {v.variant} |")
    a("")
    a(f"Denominator: all {fn(len(c18))} cases in {Y}, including drafts and incomplete cases. {P}'s top 10 is in `variants_top10.csv`.")
    a("")
    a("## 7. Compliance checks (both years; case ids)")
    a("")
    a("| Check | Cases | Case ids |")
    a("|---|---|---|")
    for chk, label in [("payment_without_request", "Payment Handled with no Request Payment"), ("payment_before_final_approval", "Payment before final approval"),
                       ("request_without_prior_approval", "Request Payment with no approval before it"), ("paid_more_than_once", "Paid more than once")]:
        a(f"| {label} | {fn(flag_n(chk))} of {fn(k(f'Compliance: {chk}', 'all', 'denominator'))} | {flag_ids(chk)} |")
    a("")
    a("## 9. Submissions per month (2018, local time)")
    a("")
    a("| Month | Submission events | First submissions | Resubmissions |")
    a("|---|---|---|---|")
    for m in mv.itertuples():
        a(f"| {m.month} | {fn(m.submission_events)} | {fn(m.first_submissions)} | {fn(m.resubmissions)} |")
    a("")
    a("Workload context only. Filter: “Declaration SUBMITTED by EMPLOYEE” events dated in 2018 (some belong to 2017 cases that were resubmitted).")
    a("")
    a("## Findings")
    a("")
    a(f"1. **A paid declaration takes a median of {fd(ct('median', Y))} from first submission to payment, and 1 in 10 takes more than {fd(ct('p90', Y))}.** "
      f"The mean ({fd(ct('mean', Y))}) is well above the median because of a long tail: {fn(over60)} of the {fn(n_ct18)} paid {Y} cases took over 60 days. Denominator: {fn(n_ct18)} paid {Y} cases with a submission.")
    a(f"2. **About 1 in 8 submitted declarations is rejected at least once ({fp(k('Submitted cases rejected at least once (by an approver)', Y))}, {fn(k('Submitted cases rejected at least once (by an approver)', Y, 'numerator'))} of {fn(len(sub18))} submitted {Y} cases), "
      f"and ADMINISTRATION makes most of the rejections:** {fn(r('ADMINISTRATION', Y, 'rejection_events'))} of {fn(int(rj[(rj['year'] == Y) & (rj['role'] != 'EMPLOYEE')]['rejection_events'].sum()))} approver rejections, "
      f"{r('ADMINISTRATION', Y, 'rejections_per_100_cases_reached'):.1f} per 100 cases it handled, against {r('SUPERVISOR', Y, 'rejections_per_100_cases_reached'):.1f} for SUPERVISOR and {r('BUDGET OWNER', Y, 'rejections_per_100_cases_reached'):.1f} for BUDGET OWNER.")
    a(f"3. **Paid cases with a rejection took longer:** paid {Y} cases with an approver rejection took a median of {fd(np.percentile(with_r, 50))} from first submission to payment, against {fd(np.percentile(without_r, 50))} for those without one "
      f"({fn(len(with_r))} and {fn(len(without_r))} paid cases). The rejected cases also hold {fp(rej_amt18 / nz18['amount'].sum() * 100)} of the {Y} amount ({fm(rej_amt18)} of {fm(nz18['amount'].sum())} units as in source, zero amounts excluded).")
    a(f"4. **ADMINISTRATION's step is almost instant; the waits are at the supervisor, budget owner and payment steps.** In {Y}, ADMINISTRATION acted a median of {fd(w('ADMINISTRATION', Y, 'median_days'))} after the previous event "
      f"(P90 {fd(w('ADMINISTRATION', Y, 'p90_days'))}). SUPERVISOR waited a median of {fd(w('SUPERVISOR', Y, 'median_days'))} (P90 {fd(w('SUPERVISOR', Y, 'p90_days'))}), "
      f"BUDGET OWNER {fd(w('BUDGET OWNER', Y, 'median_days'))} (P90 {fd(w('BUDGET OWNER', Y, 'p90_days'))}), Request Payment came {fd(w('Request Payment (system)', Y, 'median_days'))} after the previous step "
      f"(P90 {fd(w('Request Payment (system)', Y, 'p90_days'))}), and Payment Handled {fd(w('Payment Handled (system)', Y, 'median_days'))} after that (P90 {fd(w('Payment Handled (system)', Y, 'p90_days'))}).")
    a(f"5. **The process is highly standard.** {fp(k('Cases on the most common path', Y))} of {fn(len(c18))} {Y} cases follow one 5-step path "
      f"(submitted, approved by administration, final approval by supervisor, payment requested, paid); the top two paths cover {fp(v18.head(2)['pct_of_cases'].sum())} and the top 10 cover {fp(k('Cases on the top 10 paths', Y))}.")
    a(f"6. **About 1 in 10 submitted declarations was resubmitted:** {fp(k('Submitted cases with 1 or more resubmissions', Y))} of submitted {Y} cases ({fn(k('Submitted cases with 1 or more resubmissions', Y, 'numerator'))} of {fn(len(sub18))}) were resubmitted at least once, "
      f"with {fn(k(RESUB_KPI, Y))} resubmissions in total.")
    a(f"7. **Compliance checks flagged {fn(fl['case_id'].nunique())} of {fn(int(cases['paid'].sum()))} paid cases (both years), and found no double payments:** {fn(flag_n('payment_without_request', Y))} paid {Y} cases went straight from final approval to payment with no Request Payment event "
      f"(median {fd(float(direct_pay['median_days'].iloc[0])) if len(direct_pay) else 'n/a'} between them); in {P}, {fn(flag_n('payment_before_final_approval', P))} cases were paid with no final approval at all "
      f"({flag_ids('payment_before_final_approval')}). No case was paid more than once ({fn(flag_n('paid_more_than_once'))} of {fn(k('Compliance: paid_more_than_once', 'all', 'denominator'))} paid cases).")
    a(f"8. **Incomplete cases are few, and mostly unsubmitted drafts.** In {Y}, {fn(inc18)} of {fn(len(c18))} cases ({fp(inc18 / len(c18) * 100)}) are incomplete: {fn(drafts18)} drafts saved and never submitted, "
      f"and {fn(int(no_resp18.sum()))} whose last event is a rejection by another role with no employee response. "
      f"In {P}, {fn(int(no_resp17.sum()))} cases end on a rejection with no response, all “REJECTED by MISSING” (the approver's role wasn't recorded).")
    a("")
    a("## Limitations")
    a("")
    a(f"- **{P} is not comparable with {Y}.** {P} covers two departments only, and its roles differ: PRE_APPROVER and the “MISSING” role appear only in {P}, "
      f"ADMINISTRATION appears in only {fn(int(r('ADMINISTRATION', P, 'cases_reached_role')))} {P} cases, and BUDGET OWNER in {fn(int(r('BUDGET OWNER', P, 'cases_reached_role')))}. Side-by-side numbers are context, not a trend.")
    a("- **The log has no department, employee or approver identity.** Resources are only “STAFF MEMBER” or “SYSTEM”, so waits and rejections can't be broken down by person or team, and workload per approver can't be measured.")
    a("- **Waits are measured between recorded events.** Time spent before the first submission, and any work that isn't logged, is invisible. A near-zero wait (as for ADMINISTRATION) may reflect how events are recorded rather than how long people take.")
    a("- **“REJECTED by EMPLOYEE” is read as the employee's response to a rejection,** not a rejection: in most cases it directly follows an approver rejection. It is shown separately and not counted in rejection rates.")
    a(f"- **End of the log:** the log runs until {log_end}, months after the last {Y} submission, so few {Y} cases are cut off by the end of the data. "
      f"The {fn(len(open18))} {Y} cases that end on a rejection with no employee response last moved between {open18.min().strftime('%Y-%m-%d')} and {open18.max().strftime('%Y-%m-%d')}; "
      "the never-submitted drafts are spread across the year.")
    a("- **Amounts were anonymised by the publisher** and carry no currency. They are used only for medians and totals, never converted.")
    a("- **The data is from a public benchmark (BPI Challenge 2020)**; findings describe this log, not any current process.")
    a("")
    a("## Files")
    a("")
    a("`data/outputs/tableau/`: `kpi_summary.csv` (every KPI with year, filter, denominator, numerator and unrounded value), `cycle_time_by_case.csv`, `transitions.csv` (process map), "
      "`role_wait_times.csv`, `rejections_by_role.csv`, `variants_top10.csv`, `monthly_volume.csv`, `compliance_flags.csv`. Values in the CSVs are not rounded.")
    a("")
    with open(REPORT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))


if __name__ == "__main__":
    main()
