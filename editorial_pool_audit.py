#!/usr/bin/env python3
"""Fail-closed check that genuine verified eligible events reach email OR calendar.

Source accounting is separate: 49 reviewed source rows alone cannot prove that
the resulting issue considered its discovered events. This test never
generates editorial decisions or turns anonymous HTTP links into events.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

SECTIONS = ("top3", "new_discoveries", "worth_reconsidering", "calendar_only_events")
EMAIL = SECTIONS[:3]


def event_id(event):
    url = event.get("url", "")
    try:
        p = urlsplit(url)
        if p.scheme != "https" or not p.netloc:
            return None
        normalized = urlunsplit((p.scheme, p.netloc.lower(), p.path.rstrip("/"), p.query, ""))
    except (TypeError, ValueError):
        return None
    return normalized


def audit(issue, *, comparison=None):
    errors = []
    pool = (issue.get("research_coverage") or {}).get("eligible_verified_events")
    if not isinstance(pool, list) or not pool:
        errors.append("Missing nonempty research_coverage.eligible_verified_events: source scans alone are not an event pool")
        pool = []
    selection = [(section, event) for section in SECTIONS for event in issue.get(section, [])]
    selected_ids = [event_id(e) for _, e in selection]
    selected = {x for x in selected_ids if x}
    if len(selected) != len([x for x in selected_ids if x]):
        errors.append("Duplicate original event URLs across newsletter/calendar sections")
    pool_ids = []
    for event in pool:
        if not isinstance(event, dict):
            errors.append("Invalid eligible event record")
            continue
        key = event_id(event)
        if not key or not event.get("title") or not event.get("source_id"):
            errors.append("Eligible events need original HTTPS URL, title, and source_id")
            continue
        if event.get("verification_status") != "verified_eligible":
            errors.append(f"{key}: eligibility not explicitly verified")
        pool_ids.append(key)
    if len(set(pool_ids)) != len(pool_ids):
        errors.append("Duplicate original URLs within eligible verified pool")
    missing = sorted(set(pool_ids) - selected)
    unaccounted = sorted(selected - set(pool_ids))
    if missing:
        errors.append(f"Verified eligible events omitted from BOTH email and calendar: {missing}")
    if unaccounted:
        errors.append(f"Selected events absent from eligible verified pool: {unaccounted}")
    extras = issue.get("calendar_only_events")
    if not isinstance(extras, list):
        errors.append("Missing calendar_only_events list (empty allowed only when all verified eligible events are in email)")
        extras = []
    if comparison is not None:
        prior = {event_id(e) for section in SECTIONS for e in comparison.get(section, [])}
        new = sorted(selected - prior)
        if not new:
            errors.append("Owner rehearsal reuses ALL original issue event URLs; not a fresh source-to-selection test")
        if not extras:
            errors.append("Owner full-source rehearsal has zero calendar-only events; it does not exercise wider calendar handoff")
    else:
        new = []
    return {"ok": not errors, "errors": errors,
            "eligible_verified": len(pool_ids), "selected": len(selected),
            "newsletter": sum(len(issue.get(s, [])) for s in EMAIL),
            "calendar_only": len(extras), "new_vs_reference": len(new),
            "missing_from_outputs": missing, "unaccounted_selections": unaccounted}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--issue", required=True)
    p.add_argument("--comparison")
    p.add_argument("--report", default="release/editorial-pool-report.json")
    args = p.parse_args()
    issue = json.loads(Path(args.issue).read_text())
    comparison = json.loads(Path(args.comparison).read_text()) if args.comparison else None
    result = audit(issue, comparison=comparison)
    target = Path(args.report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
