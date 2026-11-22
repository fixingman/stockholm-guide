#!/usr/bin/env python3
"""Publish standards-compliant, read-only iCalendar feeds from verified calendar data.

Only precise event starts and verified closing dates are exported. Flexible
events are deliberately omitted: their schedule cannot be safely invented.
"""
import argparse
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

STOCKHOLM = ZoneInfo("Europe/Stockholm")
PUBLIC_BASE = "https://fixingman.github.io/stockholm-guide/"


def filename(event):
    """Stable across newsletter sections and repeated publications."""
    identity = "\n".join((event["url"], event["title"], event["date"] or "", event["kind"]))
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24] + ".ics"


def ical_text(value):
    """RFC 5545 TEXT escaping (including line breaks)."""
    value = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    return value.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,").replace("\n", r"\n")


def folded(line):
    """Fold at <= 75 UTF-8 octets, never splitting a Unicode character."""
    chunks, chunk = [], ""
    for char in line:
        candidate = chunk + char
        if len(candidate.encode("utf-8")) > 75:
            chunks.append(chunk)
            chunk = " " + char
        else:
            chunk = candidate
    chunks.append(chunk)
    return "\r\n".join(chunks)


def event_lines(event, stamp):
    if not event.get("date") or event.get("kind") not in ("event", "closing"):
        return []
    day = date.fromisoformat(event["date"])
    summary = ("Closing reminder: " if event["kind"] == "closing" else "") + event["title"]
    notes = [event.get("description", ""), event.get("dates", "")]
    if event.get("price"):
        notes.append("Price: " + event["price"])
    if event.get("booking"):
        notes.append("Booking: " + event["booking"])
    if event["kind"] == "closing":
        notes.append("Closing-day reminder only; no opening time is implied.")
    else:
        notes.append("End time is not confirmed; check the organizer.")
    notes.append("Official event page: " + event["url"])
    content = [
        "BEGIN:VEVENT",
        "UID:" + filename(event)[:-4] + "@fixingman.github.io",
        "DTSTAMP:" + stamp,
        "SUMMARY:" + ical_text(summary),
        "DESCRIPTION:" + ical_text("\n".join(x for x in notes if x)),
    ]
    if event["kind"] == "closing":
        content += [
            "DTSTART;VALUE=DATE:" + day.strftime("%Y%m%d"),
            "DTEND;VALUE=DATE:" + (day + timedelta(days=1)).strftime("%Y%m%d"),
            "TRANSP:TRANSPARENT",
        ]
    else:
        if not event.get("time"):
            raise ValueError("A timed session needs an actual time")
        hour, minute = map(int, event["time"].split(":"))
        start = datetime(day.year, day.month, day.day, hour, minute, tzinfo=STOCKHOLM)
        content.append("DTSTART:" + start.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        # No DTEND: no fabricated session length. RFC 5545 permits DTSTART only.
    content.append("LOCATION:" + ical_text(event.get("venue", "")))
    # URLs are URI values, not iCalendar TEXT. Reject embedded control chars.
    url = event["url"]
    if any(c in url for c in ("\r", "\n", "\x00")):
        raise ValueError("Invalid event URL control character")
    content.extend(["URL:" + url, "END:VEVENT"])
    return content


def ical_bytes(events, published_at):
    publication = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    if publication.tzinfo is None:
        raise ValueError("Publication requires an offset")
    stamp = publication.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0",
        "PRODID:-//The Stockholm Guide//Events Calendar//EN",
        "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
        "X-WR-CALNAME:" + ical_text("The Stockholm Guide"),
        "X-WR-TIMEZONE:Europe/Stockholm",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
    ]
    for event in events:
        lines.extend(event_lines(event, stamp))
    lines.append("END:VCALENDAR")
    return ("\r\n".join(folded(line) for line in lines) + "\r\n").encode("utf-8")


def write_feeds(data, feed_path, events_dir):
    """Generate the single subscription feed plus the individual .ics files."""
    events = [e for e in data["events"] if e.get("date") and e.get("kind") in ("event", "closing")]
    target = Path(feed_path)
    directory = Path(events_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir(parents=True, exist_ok=True)
    for stale in directory.glob("*.ics"):
        stale.unlink()
    target.write_bytes(ical_bytes(events, data["published_at"]))
    for event in events:
        (directory / filename(event)).write_bytes(ical_bytes([event], data["published_at"]))
    if len({filename(e) for e in events}) != len(events):
        raise ValueError("Calendar events have colliding stable file identities")
    return len(events)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="issues/current.json")
    parser.add_argument("--output", default="calendar.ics")
    parser.add_argument("--events-dir", default="calendar-events")
    args = parser.parse_args()
    # Exactly the same approved data source and eligibility rules as the webpage.
    from build_calendar import build_data
    guide = build_data(json.loads(Path(args.data).read_text(encoding="utf-8")))
    count = write_feeds(guide, args.output, args.events_dir)
    print(f"Public read-only iCalendar: {count} verified dated items; no subscribers or email")
