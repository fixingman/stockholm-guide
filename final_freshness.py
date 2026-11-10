#!/usr/bin/env python3
"""Final editorial freshness gate, run just before sending.

This checks timestamped independent organizer re-review evidence, not organizer
truth. Never silently turn a reachable page into 'confirmed'. No email is sent.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from editorial_quality import SECTIONS, hostname, verified_timestamp

MAX_FINAL_REVIEW_AGE_HOURS = 24


def audit_freshness(issue, *, now=None, max_age_hours=MAX_FINAL_REVIEW_AGE_HOURS):
    now = now or datetime.now(timezone.utc)
    errors, warnings, rows = [], [], []
    if not issue.get("issue_number") or not issue.get("date_range"):
        errors.append("Issue identity missing")
    for section in SECTIONS:
        for item in issue.get(section, []):
            name = item.get("title", "(untitled)")
            review = item.get("final_review") or {}
            checked = verified_timestamp(review.get("checked_at", ""))
            source = review.get("organizer_source_url", "")
            status = review.get("event_status")
            booking = review.get("booking_status")
            notes = review.get("notes", "")
            row = {"title": name, "section": section, "event_status": status,
                   "booking_status": booking, "checked_at": review.get("checked_at"),
                   "organizer_source_url": source}
            rows.append(row)
            if not checked or not hostname(source):
                errors.append(f"Missing timed final organizer review: {name}")
                continue
            hours = (now - checked).total_seconds() / 3600
            if hours < 0 or hours > max_age_hours:
                errors.append(f"Final check outside {max_age_hours}h window: {name}")
            if status not in ("scheduled", "rescheduled", "cancelled", "unknown"):
                errors.append(f"Unknown event status after final review: {name}")
            elif status == "unknown" and not notes:
                errors.append(f"Unknown event status needs explanation: {name}")
            if booking not in ("available", "sold_out", "required_unverified",
                               "not_required", "unknown"):
                errors.append(f"Missing final booking status: {name}")
            if section != "unavailable" and status in ("cancelled", "rescheduled"):
                errors.append(f"Changed event must be corrected or moved to unavailable: {name}")
            if section != "unavailable" and booking == "sold_out":
                errors.append(f"Sold out event still shown as available: {name}")
            if section == "unavailable" and status == "scheduled" and booking in ("available", "not_required"):
                warnings.append(f"Unavailable section may be outdated: {name}")
            if status == "rescheduled" and not notes:
                errors.append(f"Reschedule needs details: {name}")
    return {"ready_for_send": not errors, "errors": errors, "warnings": warnings,
            "checked_rows": len(rows), "max_age_hours": max_age_hours,
            "reviewed_events": rows,
            "note": "Timestamped evidence audit; cannot independently establish that page claims are true."}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--report", default="final-freshness-report.json")
    ap.add_argument("--max-age-hours", type=float, default=24)
    args=ap.parse_args()
    result=audit_freshness(json.loads(Path(args.data).read_text()), max_age_hours=args.max_age_hours)
    Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"ready_for_send":result["ready_for_send"],"errors":result["errors"],
                      "warnings":result["warnings"],"checked_rows":result["checked_rows"]},indent=2))
    return 0 if result["ready_for_send"] else 1


if __name__=="__main__":
    raise SystemExit(main())
