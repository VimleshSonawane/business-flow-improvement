"""Build the data file for the demo site from the project's existing outputs.

Reads only files already in the repository and writes demo/data/site.json:
  data/outputs/*.csv, data/outputs/tableau/*.csv, data/processed/*.csv (row counts)
  data/raw/bpi2020/SOURCE.md (checksum), docs/charter.md (targets, milestones),
  docs/decisions.md and docs/data-cleaning-log.md (decision titles),
  docs/pm/roadmap.csv, docs/pm/control-plan.csv and docs/pm/raid-log.csv (Smartsheet exports),
  docs/approval-workflow-final-presentation.pptx (slide 16, only to cross-check the control plan),
  analysis/*.py and .github/workflows/fetch-bpi2020.yml (short code excerpts, copied as is).
Nothing is computed from the raw log and no number is typed in by hand. It stops with an error if
the charter, the Smartsheet exports or the deck disagree with the output files.

Standard library only. Deterministic: fixed key order, fixed rounding, no timestamps, so two
runs give byte-identical output.

Run from anywhere:  python3 analysis/04_site_data.py
"""

import collections
import csv
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "demo", "data", "site.json")
T = os.path.join(ROOT, "data", "outputs", "tableau")
YEAR = "2018"
GITHUB = "https://github.com/VimleshSonawane/business-flow-improvement/blob/main/"

# RAID rating bands for score = probability x impact (1-5 scales). The Smartsheet Rating column is
# a formula and is not in the export; these bands reproduce it for every risk in the sheet.
RATING = [(10, "High"), (5, "Medium"), (0, "Low")]


def path(*p):
    return os.path.join(ROOT, *p)


def rows(name, base=T):
    with open(os.path.join(base, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(x, nd=4):
    if x in ("", None):
        return None
    v = float(x)
    return int(v) if v == int(v) and "." not in str(x) else round(v, nd)


def count_rows(p):
    with open(p, encoding="utf-8") as fh:
        return sum(1 for _ in fh) - 1


def excerpt(rel, anchor, n):
    """Copy n lines of a file, starting at the first line containing anchor."""
    with open(path(rel), encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    i = next(k for k, l in enumerate(lines) if anchor in l)
    block = lines[i:i + n]
    indent = min(len(l) - len(l.lstrip()) for l in block if l.strip())
    return {"file": rel, "start_line": i + 1, "end_line": i + n,
            "url": f"{GITHUB}{rel}#L{i + 1}-L{i + n}",
            "code": "\n".join(l[indent:] for l in block)}


def decision_titles(rel):
    out = {}
    with open(path(rel), encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^(\d+)\. \*\*(.+?)\*\*\s*(.*)", line)
            if m:
                out[int(m.group(1))] = {"title": m.group(2).rstrip("."), "text": m.group(3).strip()}
    return out


def main():
    kpi = {(r["kpi_id"], r["kpi"], r["year"]): r for r in rows("kpi_summary.csv")}

    def k(kid, name, year=YEAR):
        r = kpi[(kid, name, year)]
        return {"value": num(r["value"]), "denominator": int(r["denominator"]),
                "denominator_description": r["denominator_description"], "filter": r["case_set"]}

    figs = {(r["figure"], r["year"]): r for r in rows("report_figures.csv")}

    def f(name, year=YEAR):
        return num(figs[(name, year)]["value"])

    baseline = {
        "median_days": k("1a", "Cycle time, median"),
        "p90_days": k("1d", "Cycle time, P90"),
        "rejected_pct": k("4a", "Cases rejected at least once (approver rejections; REJECTED by EMPLOYEE not counted)"),
        "mon_thu_pct": k("3b", "Payment Handled events on a Monday or Thursday"),
        "mean_days": k("1b", "Cycle time, mean"),
        "p75_days": k("1c", "Cycle time, P75"),
        "paid_cases": k("0a", "Cases paid (has a Payment Handled event)"),
        "with_rejection_median": k("5c", "Cycle time median, paid WITH a rejection"),
        "without_rejection_median": k("5d", "Cycle time median, paid WITHOUT a rejection"),
        "admin_median_seconds": k("3c", "Submission to ADMINISTRATION action, median (2018 only)"),
        "cases_2018": f("Cases by year definition"),
        "cases_total": f("Cases in the processed log", "both years"),
        "events_total": f("Events in the processed log", "both years"),
    }
    baseline["rejected_pct"]["rejected"] = int(re.search(r"\((\d+) of", kpi[(
        "4a", "Cases rejected at least once (approver rejections; REJECTED by EMPLOYEE not counted)", YEAR)]["unit"]).group(1))

    # Cycle-time distribution, 2018 paid cases, 1-day bins and a 60+ bucket.
    bins = {"rejected": [0] * 61, "never_rejected": [0] * 61}
    for r in rows("cycle_time_by_case.csv"):
        if r["year"] != YEAR:
            continue
        b = min(int(float(r["cycle_days"])), 60)
        bins["rejected" if r["rejected_at_least_once"] == "yes" else "never_rejected"][b] += 1
    dist = {"labels": [str(i) for i in range(60)] + ["60+"], **bins,
            "total": sum(bins["rejected"]) + sum(bins["never_rejected"])}

    waits = [{"step": r["step"], "events": int(r["events"]), "cases": int(r["cases"]),
              "median_days": num(r["median_days"]), "p90_days": num(r["p90_days"])}
             for r in rows("role_wait_times.csv") if int(r["events"])]
    rejections = [{"role": r["role"], "rejections": int(r["rejections"]),
                   "cases_with_rejection": int(r["cases_with_rejection"]),
                   "cases_reaching_role": int(r["cases_reaching_role"]),
                   "per_100": num(r["rejections_per_100_cases_reaching_role"])}
                  for r in rows("rejections_by_role.csv") if int(r["cases_reaching_role"])]
    weekdays = [{"day": d, "payments": f(f"Payment Handled events on a {d}")}
                for d in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]]
    monthly = [{"month": r["month"], "submissions": int(r["submissions_all"]),
                "first": int(r["first_submissions"]), "resubmissions": int(r["resubmissions"])}
               for r in rows("monthly_volume.csv")]
    paths = [{"rank": int(r["rank"]), "cases": int(r["cases"]), "pct": num(r["pct_of_cases"]),
              "steps": r["variant"].split(" > ")}
             for r in rows("variants_top10.csv") if r["year"] == YEAR]
    transitions = [{"from": r["from_activity"], "to": r["to_activity"], "cases": int(r["case_count"]),
                    "transitions": int(r["transition_count"]), "median_days": num(r["median_days"]),
                    "p90_days": num(r["p90_days"])}
                   for r in rows("transitions.csv") if r["year"] == YEAR]
    extra = {r["rejecting_role"]: {"paid_cases": int(r["paid_cases_rejected_by_role"]),
                                   "median_days": num(r["cycle_median_days"]),
                                   "extra_days": num(r["extra_median_days"])}
             for r in rows("rework_extra_days.csv", path("data", "outputs"))}

    scenarios = []
    for r in rows("scenarios.csv", path("data", "outputs")):
        remaining = int(r["submitted_cases_remaining"])
        scenarios.append({
            "id": r["scenario"], "description": r["description"],
            "median_days": num(r["cycle_median_days"]), "p90_days": num(r["cycle_p90_days"]),
            "over_14_pct": num(r["share_over_14_days_pct"]), "over_14_cases": int(r["cases_over_14_days"]),
            "payment_wait_days": num(r["payment_wait_median_days"]),
            "rejected_cases": int(r["approver_rejected_cases"]),
            "rejection_pct": num(r["rejection_rate_remaining_pct"]),
            "rejection_pct_all_submitted": num(r["rejection_rate_pct"]),
            "submitted_base": remaining, "submitted_all": int(r["submitted_cases_2018"])})

    flags = rows("compliance_flags.csv")
    by_check = collections.Counter(r["check"] for r in flags)
    exceptions = {"flag_events": len(flags), "distinct_cases": len({r["case_id"] for r in flags}),
                  "by_check": dict(sorted(by_check.items())),
                  "paid_without_final_approval": sorted(r["case_id"] for r in flags
                                                        if r["check"] == "payment_without_final_approval"),
                  "paid_cases_checked": int(kpi[("7", "Compliance: flag events (all checks)", "all")]["denominator"])}

    # Charter targets and milestones.
    charter = open(path("docs", "charter.md"), encoding="utf-8").read()
    tgt = re.search(r"P90 cycle time for paid claims from ([\d.]+) days to ([\d.]+) days or less", charter)
    tgr = re.search(r"rejected at least once from ([\d.]+)% to ([\d.]+)% or less", charter)
    tgp = re.search(r"median wait before payment from ([\d.]+) days to ([\d.]+) day or less", charter)
    targets = {"p90_days": float(tgt.group(2)), "rejection_pct": float(tgr.group(2)),
               "payment_wait_days": float(tgp.group(2))}
    if (float(tgt.group(1)), float(tgr.group(1)), float(tgp.group(1))) != (
            round(baseline["p90_days"]["value"], 2), round(baseline["rejected_pct"]["value"], 2),
            round(scenarios[0]["payment_wait_days"], 2)):
        sys.exit("STOP: charter baseline figures don't match the outputs.")
    ms_line = next(l for l in charter.split("\n") if l.startswith("M0 "))
    milestones = [{"id": m.group(1), "name": m.group(2).strip(), "date": m.group(3),
                   "done": bool(m.group(4))}
                  for m in re.finditer(r"(M\d) (.+?) — (\d{4}-\d{2}-\d{2})( \(done\))?", ms_line)]
    closed = re.search(r"Project closed:\*\* (\d{4}-\d{2}-\d{2})", charter)
    project_closed = closed.group(1) if closed else None

    pm = path("docs", "pm")

    def nums(text):
        return [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", text or "")]

    def stop(msg):
        sys.exit("STOP: " + msg)

    # Control plan: the Smartsheet export, checked against the outputs, the charter and the deck.
    plan = rows("control-plan.csv", pm)
    cp = {r["KPI"]: r for r in plan}
    w = {x["step"]: x for x in waits}
    s6 = next(x for x in scenarios if x["id"] == "S6")
    expect = {
        "P90 cycle time": f"{baseline['p90_days']['value']:.2f} days",
        "Median cycle time": f"{baseline['median_days']['value']:.2f} days",
        "Rejection rate": f"{baseline['rejected_pct']['value']:.2f}%",
        "Zero-amount submissions": f"{int(kpi[('10c', 'Share of rejected cases that have a zero amount', YEAR)]['unit'].split('(')[1].split()[0])} (all rejected)",
        "Payment wait": f"{scenarios[0]['payment_wait_days']:.2f} days",
        "Payments on Monday or Thursday": f"{baseline['mon_thu_pct']['value']:.2f}%",
        "Approval wait P90": " / ".join(f"{w[x]['p90_days']:.2f}" for x in ("BUDGET OWNER", "SUPERVISOR", "Request Payment")) + " days",
        "Paid without final approval": f"{len(exceptions['paid_without_final_approval'])} (cases "
            + ", ".join(sorted((c.split()[-1] for c in exceptions["paid_without_final_approval"]), reverse=True)) + ")",
    }
    for kk, v in expect.items():
        if cp[kk]["Baseline (2018)"] != v:
            stop(f"control-plan.csv baseline for {kk!r} is {cp[kk]['Baseline (2018)']!r}, outputs give {v!r}.")
    if f"{s6['median_days']:.2f}" not in cp["Median cycle time"]["Target"]:
        stop("control-plan.csv median target doesn't quote the S6 median.")
    for kk, t in (("P90 cycle time", targets["p90_days"]), ("Rejection rate", targets["rejection_pct"]),
                  ("Payment wait", targets["payment_wait_days"])):
        if nums(cp[kk]["Target"]) != [t]:
            stop(f"control-plan.csv target for {kk!r} doesn't match the charter ({t}).")
    # Cross-check with the deck's control-plan slide (slide 16): same baseline and target numbers.
    z = zipfile.ZipFile(path("docs", "approval-workflow-final-presentation.pptx"))
    xml = z.read("ppt/slides/slide16.xml").decode("utf-8")
    cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c).replace("&gt;", ">").replace("&lt;", "<")
                    .replace("&amp;", "&")).strip() for c in re.findall(r"<a:tc>(.*?)</a:tc>", xml, re.S)]
    body = cells[cells.index("Owner") + 1:]
    deck = [body[i:i + 5] for i in range(0, len(body) - 4, 5)]
    deck_name = {"Payment wait (median)": "Payment wait"}
    shown = []
    for k_, now_, tgt_, _, _ in deck:
        r = cp[deck_name.get(k_, k_)]
        if nums(now_) != nums(r["Baseline (2018)"])[:len(nums(now_))] or nums(tgt_) != nums(r["Target"]):
            stop(f"the deck's control plan disagrees with control-plan.csv for {k_!r}.")
        shown.append(r["KPI"])
    control = [{"kpi": r["KPI"], "now": r["Baseline (2018)"], "target": r["Target"],
                "alert": r["Alert trigger"], "owner": r["Owner (role-played)"], "frequency": r["Check frequency"],
                "fix": r["Linked fix"]} for r in plan if r["KPI"] in shown]
    review = cp["Review cadence"]["Target"]

    # Roadmap: waves, their tasks and milestones M5-M7, from the Smartsheet export.
    def iso(d):
        m, d_, y = d.split("/")
        return f"20{y}-{m}-{d_}"
    waves, wave_ms, current = [], [], None
    for r in rows("roadmap.csv", pm):
        name = r["Task Name"]
        if not r["Start"]:
            current = {"wave": name, "tasks": []}
            waves.append(current)
            continue
        m = re.match(r"(M\d+): (.+)", name)
        if m:
            wave_ms.append({"id": m.group(1), "name": m.group(2), "date": iso(r["Start"]), "status": r["Status"]})
            continue
        current["tasks"].append({"name": name, "start": iso(r["Start"]), "end": iso(r["Finish"]),
                                 "owner": r["Owner (role-played)"], "status": r["Status"],
                                 "effect": r["Expected effect (what-if, 2018 data)"]})
        sid = re.match(r"(S\d)", r["Expected effect (what-if, 2018 data)"])
        if sid:
            sc = next(x for x in scenarios if x["id"] == sid.group(1))
            allowed = {round(v, 2) for v in (sc["p90_days"], sc["median_days"], sc["payment_wait_days"],
                                              sc["rejection_pct"], scenarios[0]["p90_days"],
                                              scenarios[0]["payment_wait_days"], scenarios[0]["rejection_pct"])}
            text = re.sub(r"\b(?:[SF]\d|P90)\b", "", r["Expected effect (what-if, 2018 data)"])
            bad = [v for v in nums(text) if v not in allowed and v != 40]  # 40 = the S4/S5 assumed cut (%)
            if bad:
                stop(f"roadmap.csv effect for {name!r} has numbers not in scenarios.csv: {bad}")
    waves = [{"wave": wv["wave"], "start": min(t["start"] for t in wv["tasks"]),
              "end": max(t["end"] for t in wv["tasks"]), "items": [t["name"] for t in wv["tasks"]]}
             for wv in waves if wv["tasks"]]

    # RAID log, from the Smartsheet export.
    raid_rows = rows("raid-log.csv", pm)
    raid_counts = dict(collections.Counter(r["Type"] for r in raid_rows))
    risks = []
    for r in raid_rows:
        if r["Type"] != "Risk":
            continue
        pr, im = int(r["Probability"]), int(r["Impact"])
        sc_ = pr * im
        risks.append({"id": r["ID"], "description": r["Description"], "probability": pr, "impact": im,
                      "score": sc_, "rating": next(lbl for lo, lbl in RATING if sc_ >= lo),
                      "status": r["Status"], "response": r["Response"], "owner": r["Owner"]})
    risks.sort(key=lambda x: (-x["score"], x["id"]))
    raid = {"counts": raid_counts, "total": len(raid_rows), "risks": risks,
            "rating_bands": [{"min_score": lo, "rating": lbl} for lo, lbl in RATING]}

    dec = decision_titles("docs/decisions.md")
    clean = decision_titles("docs/data-cleaning-log.md")

    pipeline = [
        {"id": "raw", "name": "Raw event log", "file": "data/raw/bpi2020/DomesticDeclarations.xes.gz",
         "does": "The original BPI Challenge 2020 log of domestic travel-expense claims, saved unchanged.",
         "rows": {"claims": baseline["cases_total"], "events": baseline["events_total"]},
         "decision": None, "excerpt": None},
        {"id": "checksum", "name": "Checksum check", "file": ".github/workflows/fetch-bpi2020.yml",
         "does": "A GitHub Actions workflow downloads the log and compares its size and MD5 with the publisher's values.",
         "rows": None, "decision": None,
         "excerpt": excerpt(".github/workflows/fetch-bpi2020.yml", "EXPECTED_SIZE=", 12)},
        {"id": "clean", "name": "01_clean.py", "file": "analysis/01_clean.py",
         "does": "Reads the log with the Python standard library, converts times to UTC and flags problems without deleting rows.",
         "rows": None, "decision": {"source": "docs/data-cleaning-log.md", "id": 5, **clean[5]},
         "excerpt": excerpt("analysis/01_clean.py", "# Duplicate events", 7)},
        {"id": "processed", "name": "events.csv and cases.csv", "file": "data/processed/events.csv",
         "does": "Clean tables: one row per event and one row per claim.",
         "rows": {"events": count_rows(path("data", "processed", "events.csv")),
                  "cases": count_rows(path("data", "processed", "cases.csv"))},
         "decision": {"source": "docs/data-cleaning-log.md", "id": 7, **clean[7]}, "excerpt": None},
        {"id": "baseline", "name": "02_baseline.py", "file": "analysis/02_baseline.py",
         "does": "Computes the baseline KPIs: cycle time, waits, rejections, paths and control checks.",
         "rows": None, "decision": {"source": "docs/decisions.md", "id": 2, **dec[2]},
         "excerpt": excerpt("analysis/02_baseline.py", "# 1. Cycle time", 12)},
        {"id": "kpi", "name": "KPI and Tableau CSVs", "file": "data/outputs/tableau/kpi_summary.csv",
         "does": "Tables for the report and the Tableau dashboard, with every KPI's filter and denominator.",
         "rows": {"kpi_rows": count_rows(os.path.join(T, "kpi_summary.csv")),
                  "csv_files": len([n for n in os.listdir(T) if n.endswith(".csv")])},
         "decision": {"source": "docs/decisions.md", "id": 1, **dec[1]}, "excerpt": None},
        {"id": "scenarios", "name": "03_scenarios.py", "file": "analysis/03_scenarios.py",
         "does": "Recomputes each paid claim's cycle time with capped or removed waits to estimate what-if scenarios.",
         "rows": None, "decision": {"source": "docs/decisions.md", "id": 11, **dec[11]},
         "excerpt": excerpt("analysis/03_scenarios.py", "def cycle(c, s1=False", 13)},
        {"id": "scenario_csv", "name": "scenarios.csv", "file": "data/outputs/scenarios.csv",
         "does": "One row per scenario: median, P90, share over 14 days, payment wait and rejection rate.",
         "rows": {"scenarios": count_rows(path("data", "outputs", "scenarios.csv"))},
         "decision": {"source": "docs/decisions.md", "id": 10, **dec[10]}, "excerpt": None},
        {"id": "tableau", "name": "Tableau dashboard", "file": None,
         "url": "https://public.tableau.com/app/profile/vimlesh.vilas.sonawane/viz/ApprovalWorkflowBaselineBPI2020realdata/Baselinedashboard",
         "does": "The interactive 2018 baseline dashboard, built from the Tableau CSVs.",
         "rows": None, "decision": None, "excerpt": None},
    ]
    for p in pipeline:
        if p.get("file"):
            p["url"] = GITHUB + p["file"]

    source = open(path("data", "raw", "bpi2020", "SOURCE.md"), encoding="utf-8").read()
    raw = {"size_bytes": int(re.search(r"Size: (\d+)", source).group(1)),
           "md5": re.search(r"MD5: ([0-9a-f]{32})", source).group(1),
           "check": re.search(r"Check result: (\w+)", source).group(1)}

    site = {
        "generated_by": "analysis/04_site_data.py",
        "year": YEAR,
        "baseline": baseline,
        "targets": targets,
        "cycle_distribution": dist,
        "waits": waits,
        "rejections": rejections,
        "rework_extra": extra,
        "weekdays": weekdays,
        "monthly": monthly,
        "paths": paths,
        "transitions": transitions,
        "scenarios": scenarios,
        "exceptions": exceptions,
        "zero_amount": {"rejected_zero": int(re.search(r"\((\d+) cases\)", kpi[(
            "10c", "Share of rejected cases that have a zero amount", YEAR)]["unit"]).group(1)),
            "rejected_total": int(kpi[("10c", "Share of rejected cases that have a zero amount", YEAR)]["denominator"]),
            "share_pct": num(kpi[("10c", "Share of rejected cases that have a zero amount", YEAR)]["value"])},
        "raw": raw,
        "milestones": milestones,
        "project_closed": project_closed,
        "waves": waves,
        "wave_milestones": wave_ms,
        "control_plan": control,
        "control_review": review,
        "control_plan_total": len(plan),
        "raid": raid,
        "pipeline": pipeline,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(site, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT):,} bytes)")


if __name__ == "__main__":
    main()
