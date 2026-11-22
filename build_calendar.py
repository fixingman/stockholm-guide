#!/usr/bin/env python3
"""Render a public, no-send events calendar from the current editorial issue.

No subscriber, Gmail, authorization, or private records are read. No invented
dates: only timestamped event_start and *verified* last-chance event_end dates
become calendar pins. Other items remain discoverable as flexible listings.
"""
import argparse
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from editorial_scanning import enhance, has_verified_last_chance

ROOT = Path(__file__).resolve().parent
TZ = ZoneInfo("Europe/Stockholm")
SECTIONS = ("top3", "new_discoveries", "worth_reconsidering", "calendar_only_events")


def timestamp(value):
    if not value:
        return None
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return t.astimezone(TZ) if t.tzinfo else None
    except (ValueError, AttributeError, TypeError):
        return None


def https_url(value):
    try:
        p = urlparse(value or "")
        return bool(p.scheme == "https" and p.netloc and not p.username and not p.password)
    except (ValueError, TypeError):
        return False


def calendar_extra_approved(entry, issue):
    """Only original, dated editorial evidence may populate calendar-only listings.

    The source probe/checklist is not a review. Its unverified candidate links
    must never become public events just because a website returned HTTP 200.
    """
    url = entry.get("url")
    review = entry.get("final_review") or {}
    source_id = entry.get("source_id")
    published = timestamp(issue.get("published_at"))
    checked = timestamp(review.get("checked_at"))
    if not (https_url(url) and source_id and published and checked):
        return False
    age = published - checked
    if not (timedelta(0) <= age <= timedelta(hours=72)):
        return False
    if review.get("organizer_source_url") != url or review.get("event_status") != "scheduled":
        return False
    if review.get("booking_status") in ("sold_out", "cancelled", "unavailable"):
        return False
    if not (entry.get("title") and entry.get("dates") and entry.get("venue")):
        return False
    if entry.get("event_start") and timestamp(entry["event_start"]) is None:
        return False
    scans = (issue.get("research_coverage") or {}).get("source_scans") or []
    return any(
        row.get("source_id") == source_id
        and row.get("status") == "reviewed_leads"
        and url in (row.get("candidate_urls") or [])
        for row in scans if isinstance(row, dict)
    )


def build_data(issue):
    if not issue.get("issue_number") or not issue.get("published_at"):
        raise ValueError("A published issue with a dated publication time is required")
    publication = timestamp(issue["published_at"])
    if publication is None:
        raise ValueError("published_at requires a timezone")
    issue = enhance(issue)
    start = date.fromisoformat(issue['window_start']) if issue.get('window_start') else publication.date()
    end = start + timedelta(days=13)
    items, seen = [], set()
    for section in SECTIONS:
        for index, entry in enumerate(issue.get(section, [])):
            if section == "calendar_only_events" and not calendar_extra_approved(entry, issue):
                continue
            url = entry.get("url", "")
            if not https_url(url):
                continue
            title = entry.get("display_title") or entry.get("title", "").strip()
            if not title:
                continue
            # Do not collapse separate events pointing to a general venue calendar.
            key = re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()
            if key in seen:
                continue
            seen.add(key)
            beginning = timestamp(entry.get("event_start"))
            if section == "calendar_only_events" and beginning and not (start <= beginning.date() <= end):
                continue
            closing = timestamp(entry.get("event_end"))
            verified_closing = bool(closing and has_verified_last_chance(entry, issue))
            # Last chance is pinned to the CLOSING DATE only if no precise
            # session is specified; don't imply it is a one-day performance.
            date = beginning.date().isoformat() if beginning else closing.date().isoformat() if verified_closing else None
            kind = "event" if beginning else "closing" if verified_closing else "flexible"
            items.append({
                "id": f"{section}-{index}",
                "title": title,
                "section": section,
                "venue": entry.get("venue", ""),
                "dates": entry.get("dates", ""),
                "description": entry.get("description", ""),
                "price": entry.get("price", ""),
                "booking": entry.get("booking", ""),
                "schedule_note": entry.get("schedule_note", ""),
                "url": url,
                "date": date,
                "time": beginning.strftime("%H:%M") if beginning else None,
                "closing_date": closing.date().isoformat() if verified_closing else None,
                "last_chance": verified_closing,
                "kind": kind,
            })
    items.sort(key=lambda x: (x["date"] is None, x["date"] or "", x["time"] or "99:99", x["title"].casefold()))
    return {
        "issue_number": issue["issue_number"],
        "date_range": issue.get("date_range", ""),
        "published_at": issue["published_at"],
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "timezone": "Europe/Stockholm",
        "event_count": len(items),
        "events": items,
    }


def render(source, output):
    data = build_data(json.loads(Path(source).read_text(encoding="utf-8")))
    # Protect inline JSON from breaking out of <script type=application/json>.
    # Safe text is created by calendar.js using textContent, never innerHTML.
    blob = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
    for original, replacement in (("<", r"\u003c"), (">", r"\u003e"), ("&", r"\u0026")):
        blob = blob.replace(original, replacement)
    env = Environment(loader=FileSystemLoader(ROOT), undefined=StrictUndefined,
                      autoescape=select_autoescape(default=True))
    rendered = env.get_template("calendar_template.html.j2").render(
        data=data, json_blob=blob
    )
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="issues/current.json")
    parser.add_argument("--output", default="calendar.html")
    args = parser.parse_args()
    result = render(args.data, args.output)
    pinned = sum(x["date"] is not None for x in result["events"])
    print(f"Calendar #{result['issue_number']}: {pinned} dated, "
          f"{result['event_count']-pinned} flexible; no sending")
