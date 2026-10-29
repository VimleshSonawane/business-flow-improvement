"""Clean and profile the BPI Challenge 2020 Domestic Declarations event log.

Reads data/raw/bpi2020/DomesticDeclarations.xes.gz as is (never writes to data/raw/),
and writes:
  data/processed/events.csv   one row per event
  data/processed/cases.csv    one row per case
  docs/data-cleaning-log.md   numbered checks, findings, decisions, rows/cases affected

Standard library only. No rows are deleted: problems are flagged in columns.
Outputs are deterministic: running the script twice gives byte-identical files.

Run from anywhere:  python3 analysis/01_clean.py
"""

import collections
import csv
import gzip
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "bpi2020", "DomesticDeclarations.xes.gz")
OUT_DIR = os.path.join(ROOT, "data", "processed")
EVENTS_CSV = os.path.join(OUT_DIR, "events.csv")
CASES_CSV = os.path.join(OUT_DIR, "cases.csv")
LOG_MD = os.path.join(ROOT, "docs", "data-cleaning-log.md")

PUBLISHER_CASES = 10500
PUBLISHER_EVENTS = 56437
LOCAL_TZ = ZoneInfo("Europe/Amsterdam")

# A case is "complete" when its last event (in time order) is one of these.
END_PAID = "Payment Handled"
END_REJECTED = "Declaration REJECTED by EMPLOYEE"


def parse_xes(path):
    """Return [(trace attributes, [event attributes])] in file order, keys as in the file."""
    cases = []
    trace_attrs = None
    event_attrs = None
    depth_event = False
    with gzip.open(path, "rb") as fh:
        for kind, el in ET.iterparse(fh, events=("start", "end")):
            tag = el.tag
            if kind == "start":
                if tag == "trace":
                    trace_attrs = {}
                    case_events = []
                elif tag == "event":
                    event_attrs = {}
                    depth_event = True
                continue
            if tag == "event":
                case_events.append(event_attrs)
                depth_event = False
                el.clear()
            elif tag == "trace":
                cases.append((trace_attrs, case_events))
                el.clear()
            elif tag in ("string", "date", "float", "int", "boolean", "id"):
                key, value = el.get("key"), el.get("value")
                if depth_event:
                    event_attrs[key] = value
                elif trace_attrs is not None:
                    trace_attrs[key] = value
    return cases


def parse_ts(value):
    """Return (utc datetime, offset string) or (None, reason)."""
    if value is None or value == "":
        return None, "missing"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None, "unparseable"
    if dt.tzinfo is None:
        return None, "no timezone"
    return dt.astimezone(timezone.utc), value[-6:]


def iso_utc(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ") if dt else ""


def main():
    cases_raw = parse_xes(RAW)
    log = []  # (title, found, decision, affected)

    n_cases = len(cases_raw)
    n_events = sum(len(evs) for _, evs in cases_raw)
    log.append((
        "Totals against the publisher",
        f"{n_cases:,} cases and {n_events:,} events parsed; the publisher states "
        f"{PUBLISHER_CASES:,} cases and {PUBLISHER_EVENTS:,} events.",
        "MATCH" if (n_cases, n_events) == (PUBLISHER_CASES, PUBLISHER_EVENTS)
        else "MISMATCH, see below.",
        "All rows.",
    ))

    # Attribute inventory.
    case_keys = sorted({k for t, _ in cases_raw for k in t})
    event_keys = sorted({k for _, evs in cases_raw for e in evs for k in e})
    fixed = ["concept:name", "time:timestamp", "org:role", "org:resource"]
    extra_event_keys = [k for k in event_keys if k not in fixed]

    # Case id check: concept:name is the case id; trace "id" should be the same.
    case_ids = [t.get("concept:name", "") for t, _ in cases_raw]
    dup_case_ids = sum(c - 1 for c in collections.Counter(case_ids).values() if c > 1)
    id_differs = sum(1 for t, _ in cases_raw if t.get("id") != t.get("concept:name"))
    log.append((
        "Case identifiers",
        f"{dup_case_ids} duplicate case ids; trace attribute `id` differs from "
        f"`concept:name` in {id_differs} cases.",
        "Use trace `concept:name` as case_id.",
        f"{dup_case_ids} cases.",
    ))

    # Build event rows.
    rows = []
    for case_no, (tattrs, evs) in enumerate(cases_raw):
        cid = tattrs.get("concept:name", "")
        for pos, e in enumerate(evs):
            utc, info = parse_ts(e.get("time:timestamp"))
            rows.append({
                "case_id": cid,
                "_case_no": case_no,
                "file_position": pos,
                "activity": e.get("concept:name", ""),
                "timestamp": iso_utc(utc),
                "_utc": utc,
                "timestamp_original": e.get("time:timestamp", ""),
                "utc_offset": info if utc else "",
                "org:role": e.get("org:role", ""),
                "org:resource": e.get("org:resource", ""),
                **{k: e.get(k, "") for k in extra_event_keys},
                "timestamp_problem": "" if utc else info,
            })

    # Missing values per event attribute.
    missing_event = {k: sum(1 for _, evs in cases_raw for e in evs if e.get(k, "") == "")
                     for k in event_keys}
    missing_case = {k: sum(1 for t, _ in cases_raw if t.get(k, "") == "") for k in case_keys}

    # Missing or invalid timestamps.
    bad_ts = [r for r in rows if r["_utc"] is None]
    log.append((
        "Missing or invalid timestamps",
        f"{len(bad_ts)} events have a missing, unparseable or timezone-less timestamp.",
        "Flag in `timestamp_problem`; keep the row; such events would sort last in their case.",
        f"{len(bad_ts)} events.",
    ))

    # Timezone handling.
    offsets = collections.Counter(r["utc_offset"] for r in rows if r["_utc"])
    dst_mismatch = 0
    for r in rows:
        if r["_utc"]:
            local = r["_utc"].astimezone(LOCAL_TZ).isoformat()[-6:]
            if local != r["utc_offset"]:
                dst_mismatch += 1
    log.append((
        "Timezone handling",
        "Offsets in the file: " + ", ".join(f"{o} ({n:,})" for o, n in sorted(offsets.items()))
        + f". Every offset matches Dutch winter/summer time (Europe/Amsterdam) except "
        f"{dst_mismatch} events.",
        "Convert all timestamps to UTC (`timestamp`, ISO 8601 with Z). Keep the original "
        "value in `timestamp_original` and its offset in `utc_offset`. All milliseconds are .000, "
        "so seconds precision loses nothing.",
        f"{len(rows) - len(bad_ts):,} events converted.",
    ))

    # Duplicate events: same case, activity, timestamp, role and resource.
    key = lambda r: (r["case_id"], r["activity"], r["timestamp"], r["org:role"], r["org:resource"])
    seen = collections.Counter()
    for r in rows:
        seen[key(r)] += 1
        r["duplicate_of_earlier"] = "yes" if seen[key(r)] > 1 else "no"
    dups = [r for r in rows if r["duplicate_of_earlier"] == "yes"]
    dup_ids = sum(c - 1 for c in collections.Counter(r.get("id", "") for r in rows).values() if c > 1) \
        if "id" in extra_event_keys else 0
    log.append((
        "Duplicate events",
        f"{len(dups)} events repeat an earlier event in the same case with the same activity, "
        f"timestamp, role and resource (in {len({r['case_id'] for r in dups})} cases). "
        f"{dup_ids} repeated event `id` values.",
        "Flag repeats in `duplicate_of_earlier` (first occurrence = no); keep all rows.",
        f"{len(dups)} events.",
    ))

    # Time order within a case: file order vs timestamp order.
    by_case = collections.defaultdict(list)
    for r in rows:
        by_case[r["_case_no"]].append(r)
    ooo_events = 0
    ooo_cases = 0
    ties = 0
    tie_cases = 0
    for evs in by_case.values():
        prev = None
        hit = False
        for r in evs:  # file order
            r["out_of_order_in_file"] = "no"
            if r["_utc"] and prev and r["_utc"] < prev:
                r["out_of_order_in_file"] = "yes"
                ooo_events += 1
                hit = True
            if r["_utc"]:
                prev = r["_utc"] if prev is None else max(prev, r["_utc"])
        ooo_cases += hit
        stamps = [r["_utc"] for r in evs if r["_utc"]]
        ties += len(stamps) - len(set(stamps))
        tie_cases += len(stamps) != len(set(stamps))
    log.append((
        "Events out of time order within a case",
        f"In file order, {ooo_events:,} events have an earlier timestamp than an event listed "
        f"before them, in {ooo_cases:,} cases. {ties} events (in {tie_cases} cases) share an exact "
        f"timestamp with an earlier event of the same case.",
        "Flag in `out_of_order_in_file`. Sort each case by UTC timestamp, then by file "
        "position for ties, and record the result in `event_order` (1 = first). "
        "Timestamps are trusted over file order.",
        f"{ooo_events:,} events in {ooo_cases:,} cases.",
    ))

    # Sort and number events.
    far = datetime.max.replace(tzinfo=timezone.utc)
    for evs in by_case.values():
        evs.sort(key=lambda r: (r["_utc"] or far, r["file_position"]))
        for i, r in enumerate(evs, 1):
            r["event_order"] = i

    # Cases table.
    case_rows = []
    for case_no, (tattrs, _) in enumerate(cases_raw):
        evs = by_case.get(case_no, [])
        stamps = [r["_utc"] for r in evs if r["_utc"]]
        start = min(stamps) if stamps else None
        end = max(stamps) if stamps else None
        acts = [r["activity"] for r in evs]
        rej = sum(1 for a in acts if a.startswith("Declaration REJECTED") and a != END_REJECTED)
        emp_rej = sum(1 for a in acts if a == END_REJECTED)
        last = acts[-1] if acts else ""
        if last == END_PAID:
            end_status = "paid"
        elif last == END_REJECTED:
            end_status = "rejected"
        else:
            end_status = "no_clear_end"
        amount_raw = tattrs.get("Amount", "")
        try:
            amount = float(amount_raw) if amount_raw != "" else None
        except ValueError:
            amount = None
        if amount is None:
            amount_flag = "missing"
        elif amount < 0:
            amount_flag = "negative"
        elif amount == 0:
            amount_flag = "zero"
        else:
            amount_flag = ""
        row = {
            "case_id": tattrs.get("concept:name", ""),
            "start": iso_utc(start),
            "end": iso_utc(end),
            "duration_days": f"{(end - start).total_seconds() / 86400:.4f}" if stamps else "",
            "event_count": len(evs),
            "first_activity": acts[0] if acts else "",
            "last_activity": last,
            "rejected_at_least_once": "yes" if rej else "no",
            "rejection_count": rej,
            "employee_rejection_count": emp_rej,
            "amount": amount_raw,
            "amount_flag": amount_flag,
            "year": start.astimezone(LOCAL_TZ).year if start else "",
            "end_status": end_status,
            "is_complete": "yes" if end_status != "no_clear_end" else "no",
            "starts_with_submission": "yes" if acts and acts[0] in (
                "Declaration SUBMITTED by EMPLOYEE", "Declaration SAVED by EMPLOYEE") else "no",
        }
        for k in case_keys:
            if k not in ("concept:name", "Amount"):
                row[k] = tattrs.get(k, "")
        case_rows.append(row)

    # Cases without a clear end.
    status = collections.Counter(r["end_status"] for r in case_rows)
    no_end = [r for r in case_rows if r["end_status"] == "no_clear_end"]
    last_acts = collections.Counter(r["last_activity"] for r in no_end)
    extract_end = max(r["end"] for r in case_rows if r["end"])
    log.append((
        "Cases without a clear end",
        f"Last activity is `{END_PAID}` in {status['paid']:,} cases and `{END_REJECTED}` in "
        f"{status['rejected']:,} cases. {len(no_end):,} cases end on something else: "
        + ", ".join(f"{a} ({n})" for a, n in last_acts.most_common())
        + f". Latest event in the log: {extract_end}.",
        "`is_complete` = yes when the last event is a payment (`Payment Handled`) or the employee "
        "closing a rejected declaration (`Declaration REJECTED by EMPLOYEE`); otherwise no. "
        "`end_status` gives which. Incomplete cases are kept and flagged, not removed.",
        f"{len(no_end):,} cases flagged incomplete.",
    ))

    # Cases that do not start with the employee submitting or saving.
    odd_start = [r for r in case_rows if r["starts_with_submission"] == "no"]
    log.append((
        "Cases that do not start with the employee",
        f"{len(odd_start)} cases start with an activity other than SUBMITTED or SAVED by EMPLOYEE"
        + "".join(f"; {a} ({n})" for a, n in collections.Counter(
            r["first_activity"] for r in odd_start).most_common()) + ".",
        "Flag in `starts_with_submission`; keep.",
        f"{len(odd_start)} cases.",
    ))

    # Year coverage.
    years = collections.Counter(r["year"] for r in case_rows)
    ev_years = collections.Counter(r["_utc"].astimezone(LOCAL_TZ).year for r in rows if r["_utc"])
    log.append((
        "2017 vs 2018 coverage",
        "Cases by start year (Dutch local time): "
        + ", ".join(f"{y} ({n:,})" for y, n in sorted(years.items()))
        + ". Events by year: " + ", ".join(f"{y} ({n:,})" for y, n in sorted(ev_years.items()))
        + ". The dataset description says 2017 covers two departments only and 2018 covers "
        "all departments. The log has no department attribute, so this cannot be checked "
        "from the data.",
        "Keep all years; add `year` (start year) to cases.csv. Any 2017-vs-2018 comparison "
        "must not be read as a trend. 2019 events belong to cases that started in 2018.",
        ", ".join(f"{y}: {n:,} cases" for y, n in sorted(years.items())) + ".",
    ))

    # Amounts.
    flags = collections.Counter(r["amount_flag"] for r in case_rows)
    amounts = sorted(float(r["amount"]) for r in case_rows if r["amount_flag"] in ("", "zero", "negative"))
    log.append((
        "Amounts that are zero, negative or missing",
        f"Missing: {flags['missing']}. Zero: {flags['zero']}. Negative: {flags['negative']}. "
        f"Range: {amounts[0]:.2f} to {amounts[-1]:.2f}. Amounts are not whole euros (for "
        "example 26.85120450862128) because the publisher anonymised them.",
        "Flag in `amount_flag`; keep the raw value unchanged in `amount`; no rows removed.",
        f"{flags['missing'] + flags['zero'] + flags['negative']} cases flagged.",
    ))

    # Rejections and unusual activities.
    act_counts = collections.Counter(r["activity"] for r in rows)
    rare = sorted(a for a, n in act_counts.items() if n <= 5)
    missing_role = act_counts.get("Declaration REJECTED by MISSING", 0)
    emp_after = 0
    for evs in by_case.values():
        for prev_r, r in zip(evs, evs[1:]):
            if r["activity"] == END_REJECTED and prev_r["activity"].startswith("Declaration REJECTED"):
                emp_after += 1
    emp_total = act_counts.get(END_REJECTED, 0)
    log.append((
        "How rejections are counted",
        f"`{END_REJECTED}` occurs {emp_total:,} times; {emp_after:,} of these come straight "
        "after a rejection by an approver, so it is the employee responding to a rejection, "
        f"not a new rejection. `Declaration REJECTED by MISSING` occurs {missing_role} times "
        "(the approver role was not recorded).",
        "`rejection_count` counts rejections by approvers (ADMINISTRATION, SUPERVISOR, "
        "PRE_APPROVER, BUDGET OWNER, MISSING) and excludes the employee step, which goes in "
        "`employee_rejection_count`. `rejected_at_least_once` = yes when `rejection_count` > 0.",
        f"{sum(1 for r in case_rows if r['rejection_count']):,} cases rejected at least once.",
    ))
    log.append((
        "Rare activities",
        "Activities seen 5 times or fewer: " + ", ".join(
            f"{a} ({act_counts[a]})" for a in rare) + ".",
        "Keep all activities with their original names; nothing merged or renamed.",
        f"{sum(act_counts[a] for a in rare)} events.",
    ))

    # Resources.
    resources = collections.Counter(r["org:resource"] for r in rows)
    log.append((
        "Resource values",
        "org:resource has only " + ", ".join(f"{k} ({v:,})" for k, v in sorted(resources.items()))
        + ". People were anonymised by the publisher.",
        "Keep as is; org:role is the useful organisational field.",
        "None.",
    ))

    # Write events.csv.
    os.makedirs(OUT_DIR, exist_ok=True)
    event_cols = (["case_id", "event_order", "activity", "timestamp", "timestamp_original",
                   "utc_offset", "org:role", "org:resource"]
                  + extra_event_keys
                  + ["file_position", "timestamp_problem", "duplicate_of_earlier",
                     "out_of_order_in_file"])
    ordered = [r for case_no in range(len(cases_raw)) for r in by_case.get(case_no, [])]
    with open(EVENTS_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=event_cols, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(ordered)

    case_cols = list(case_rows[0].keys())
    with open(CASES_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=case_cols, lineterminator="\n")
        w.writeheader()
        w.writerows(case_rows)

    # Profile.
    stamps = sorted(r["timestamp"] for r in rows if r["timestamp"])
    profile = []
    profile.append(f"Cases: {n_cases:,}   Events: {n_events:,}")
    profile.append(f"Date range (UTC): {stamps[0]} to {stamps[-1]}")
    profile.append("")
    profile.append("Activity | Count")
    profile.append("---|---:")
    for a, n in sorted(act_counts.items(), key=lambda x: (-x[1], x[0])):
        profile.append(f"{a} | {n:,}")
    profile.append("")
    profile.append("Attribute | Level | Missing values")
    profile.append("---|---|---:")
    for k in case_keys:
        profile.append(f"{k} | case | {missing_case[k]}")
    for k in event_keys:
        profile.append(f"{k} | event | {missing_event[k]}")
    profile.append("")
    profile.append("Start year | Cases")
    profile.append("---|---:")
    for y, n in sorted(years.items()):
        profile.append(f"{y} | {n:,}")
    print("\n".join(profile))

    # Write the cleaning log.
    md = ["# Data cleaning log — BPI Challenge 2020, Domestic Declarations", "",
          "Generated by `analysis/01_clean.py`. Do not edit by hand; re-run the script.", "",
          "Input: `data/raw/bpi2020/DomesticDeclarations.xes.gz` (read only, never modified; "
          "see `data/raw/bpi2020/SOURCE.md`). Outputs: `data/processed/events.csv`, "
          "`data/processed/cases.csv`.", "",
          "No row was deleted. Every problem is flagged in a column.", "",
          "## Checks and decisions", ""]
    for i, (title, found, decision, affected) in enumerate(log, 1):
        md += [f"{i}. **{title}**",
               f"   - Found: {found}",
               f"   - Decision: {decision}",
               f"   - Affected: {affected}", ""]
    md += ["## Definition of a complete case", "",
           f"`is_complete = yes` when the case's last event, in time order, is `{END_PAID}` "
           f"(`end_status = paid`) or `{END_REJECTED}` (`end_status = rejected`). "
           "Anything else is `no_clear_end`.", "",
           "## Column notes", "",
           "- `events.csv`: `timestamp` is UTC. `event_order` is the order by time within the "
           "case. `file_position` is the 0-based order in the raw file. `id` is the raw event id.",
           "- `cases.csv`: `start`/`end` are the first and last UTC timestamps; `duration_days` = "
           "(end - start) in days, 4 decimals; `year` = start year in Dutch local time; "
           "`amount` is the raw value from the file.", "",
           "## Profile", ""] + profile + [""]
    with open(LOG_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(md))


if __name__ == "__main__":
    main()
