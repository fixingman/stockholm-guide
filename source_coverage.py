#!/usr/bin/env python3
"""Verify EVERY registered source was actually accounted for in a new issue.

Reachability of a homepage (including source_sweep.py's HTTP probe) is not an
editorial scan. From Issue 006 onward the release requires 100% registry IDs
to have honest, timestamped, explicit outcomes with review evidence.
All public data; no subscribers. Older already-sent issues are grandfathered.
"""
import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse


REVIEWED = {"reviewed_leads", "reviewed_no_fit"}
BLOCKED = "blocked_after_retry"
ALLOWED = REVIEWED | {BLOCKED}


def timestamp(value):
    try:
        x = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return x if x.utcoffset() is not None else None
    except (ValueError, AttributeError, TypeError):
        return None


def https(url):
    if not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username
    except ValueError:
        return False


def issue_index(issue):
    match = re.search(r"\d+", str(issue.get("issue_number", "")))
    return int(match.group()) if match else None


def audit(issue, registry, *, strict=True, as_of=None):
    now = as_of or datetime.now(timezone.utc)
    ids = {s["id"] for s in registry.get("sources", [])}
    records = (issue.get("research_coverage") or {}).get("source_scans") or []
    errors, warnings, seen = [], [], set()
    if issue_index(issue) is None:
        errors.append("Invalid issue number")
    grandfathered = issue_index(issue) is not None and issue_index(issue) <= 5
    if not strict or grandfathered:
        return {
            "ready_for_source_coverage": True,
            "policy": "historical-exemption" if grandfathered else "informational",
            "registered_count": len(ids),
            "accounted_for_count": len(records),
            "reviewed_count": 0,
            "blocked_count": 0,
            "not_checked_count": max(0, len(ids)-len(records)),
            "errors": [], "warnings": ["Full-registry audit enforced from Issue 006, no retroactive changes to previously sent issues."],
        }

    if not ids or len(ids) != len(registry.get("sources", [])):
        errors.append("Invalid or duplicated source registry IDs")
    if not isinstance(records, list):
        records = []
        errors.append("source_scans is not a list")
    published = timestamp(issue.get("published_at"))
    if not published:
        errors.append("Missing timezone-aware issue published_at")

    index = {s["id"]: s for s in registry.get("sources", [])}
    reviewed = blocked = 0
    for row in records:
        if not isinstance(row, dict):
            errors.append("Invalid source scan record")
            continue
        source_id = row.get("source_id")
        if not isinstance(source_id, str) or source_id not in index:
            errors.append(f"Unknown source ID: {source_id!r}")
            continue
        if source_id in seen:
            errors.append("Duplicate source ID: " + source_id)
            continue
        seen.add(source_id)
        status = row.get("status")
        if status not in ALLOWED:
            errors.append(f"{source_id}: invalid, unchecked or probe-only status {status!r}")
            continue

        checked_at = timestamp(row.get("checked_at"))
        if checked_at is None or not published:
            errors.append(source_id + ": missing timestamped review")
        else:
            # Saturday scouting and Sunday final review are within the
            # 14-day issue's closing preparation window.
            age = published - checked_at
            if age < -timedelta(minutes=10) or age > timedelta(hours=72):
                errors.append(source_id + ": source review is future-dated or >72h stale")
            if checked_at > now + timedelta(minutes=10):
                errors.append(source_id + ": review timestamp is in the future")

        checked_urls = row.get("checked_urls")
        if not isinstance(checked_urls, list) or not checked_urls or not all(https(url) for url in checked_urls):
            errors.append(source_id + ": missing public HTTPS checked URLs")
            checked_urls = []
        primary = index[source_id]["official_calendar_url"]
        if primary not in checked_urls:
            errors.append(source_id + ": official source calendar not checked")
        if source_id == "luma-stockholm":
            extras = index[source_id].get("additional_discovery_urls", [])
            for extra in extras:
                if extra not in checked_urls:
                    errors.append(source_id + ": mandatory Luma category not attempted: " + extra)

        finding = row.get("finding", "")
        if not isinstance(finding, str) or len(finding.strip()) < 18:
            errors.append(source_id + ": missing specific editorial finding/obstacle")
        if status in REVIEWED:
            reviewer = row.get("reviewer")
            if not isinstance(reviewer, str) or len(reviewer.strip()) < 3:
                errors.append(source_id + ": no named assistant/editor who actually reviewed listing")
            if row.get("review_method") not in ("public_original_pages", "public_browser", "public_organizer_calendar"):
                errors.append(source_id + ": index HTTP probe cannot stand in for editorial review")
            if status == "reviewed_leads":
                urls = row.get("candidate_urls")
                if not isinstance(urls, list) or not urls or not all(https(url) for url in urls):
                    errors.append(source_id + ": reviewed_leads must have real public HTTPS candidate URLs")
            reviewed += 1
        else:
            blocked += 1
            attempts = row.get("attempts")
            if not isinstance(attempts, list) or len(attempts) < 2:
                errors.append(source_id + ": blocked must show at least two documented attempts")
            elif any(not isinstance(a, dict) or not https(a.get("url")) or not str(a.get("outcome","")).strip() for a in attempts):
                errors.append(source_id + ": blocked attempts need public URL and exact outcome")
            if not isinstance(row.get("alternate_search"), str) or len(row["alternate_search"].strip()) < 12:
                errors.append(source_id + ": blocked source needs a documented alternative search")
    missing = ids - seen
    if missing:
        errors.append("Sources never examined: " + ", ".join(sorted(missing)))
    # Allow real temporarily inaccessible public services, but not mass
    # silent crawler failure. Over 20% blocked is an incomplete release.
    max_blocked = max(2, len(ids)//5)
    if blocked > max_blocked:
        errors.append(f"Too many inaccessible sources ({blocked}/{len(ids)}); maximum {max_blocked} with evidence")
    if blocked:
        warnings.append(f"{blocked} sources inaccessible after retries; not counted as editorial reviews")
    if len(records) != len(ids):
        errors.append(f"Source coverage {len(records)}/{len(ids)} records, require 100% accounted for")
    return {
        "ready_for_source_coverage": not errors,
        "policy": "all-registered-sources",
        "registered_count": len(ids),
        "accounted_for_count": len(seen),
        "reviewed_count": reviewed,
        "blocked_count": blocked,
        "not_checked_count": len(missing),
        "max_blocked_count": max_blocked,
        "errors": errors,
        "warnings": warnings,
        "note": "Machine verifies coverage provenance fields, not truth of real-world events. Reachable HTML alone is never a review.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--issue", required=True)
    parser.add_argument("--registry", default="discovery_sources.json")
    parser.add_argument("--report", default="source-coverage-report.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    issue = json.loads(Path(args.issue).read_text(encoding="utf-8"))
    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    result = audit(issue, registry, strict=args.strict)
    dest = Path(args.report)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ready_for_source_coverage"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
