"""Conservative, data-backed scanning cues; never infer urgency from prose."""
from datetime import datetime, timedelta
import re
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from editorial_quality import verified_timestamp

STOCKHOLM = ZoneInfo("Europe/Stockholm")


def has_verified_last_chance(item, guide):
    """Closing-day cue requires explicit organizer evidence and a dated deadline."""
    if item.get("last_chance") is not True:
        return False
    published = verified_timestamp(guide.get("published_at", ""))
    closing = verified_timestamp(item.get("event_end", ""))
    source = item.get("last_chance_source_url", "")
    review = item.get("final_review") or {}
    if not (published and closing and source.startswith("https://")):
        return False
    # A URL in metadata alone isn't evidence of the exact closing date: it
    # must correspond to the independently reviewed organizer event page.
    if source != review.get("organizer_source_url"):
        return False
    if review.get("event_status") != "scheduled" or review.get("booking_status") == "sold_out":
        return False
    remaining = closing - published
    return timedelta(0) <= remaining <= timedelta(days=28)


def cues_for(item, guide):
    cues=[]
    published=verified_timestamp(guide.get("published_at",""))
    event=verified_timestamp(item.get("event_start",""))
    if published and event:
        today=published.astimezone(STOCKHOLM).date()
        event_date=event.astimezone(STOCKHOLM).date()
        first_sat=today+timedelta(days=(5-today.weekday())%7)
        if first_sat <= event_date <= first_sat+timedelta(days=1):
            cues.append("THIS WEEKEND")
    verification=item.get("verification") or {}
    booking=verification.get("booking") or {}
    if booking.get("status")=="confirmed" and item.get("booking_signal") in ("advance_required","limited"):
        cues.append("BOOK AHEAD" if item["booking_signal"]=="advance_required" else "LIMITED PLACES")
    # Last-chance resurfacing wins over generic "JUST FOUND" classification,
    # even when an old issue incorrectly marks a resurfaced item as new.
    if has_verified_last_chance(item, guide):
        return ["LAST CHANCE", *cues][:2]
    if item.get("last_chance") is not True and item.get("first_seen_issue")==guide.get("issue_number") and item.get("new_discovery_verified") is True:
        cues.append("JUST FOUND")
    return cues[:2]


def inbox_preview(guide):
    # The issue's actual editorial picks are the source; don't fabricate claims.
    picks=[x.get("preview_title") or x.get("title","") for x in guide.get("top3",[])[:2]]
    picks=[x.strip() for x in picks if x.strip()]
    if not picks:
        return "Unusual events and experiences in Stockholm"
    text=" + ".join(picks)+" · Unusual events in Stockholm"
    return text[:123].rstrip(" ·+")


def enhance(guide):
    for section in ("top3","new_discoveries","worth_reconsidering","unavailable"):
        for item in guide.get(section,[]):
            # Normalize TEST-008-era title prefixes into the existing badge
            # system without rewriting immutable historical issue artifacts.
            title=item.get("title", "")
            if item.get("last_chance") is True and re.match(r"^LAST CHANCE\\s*[-—–:]\\s*", title, re.I):
                item["display_title"]=re.sub(r"^LAST CHANCE\\s*[-—–:]\\s*", "", title, count=1, flags=re.I)
            item["scan_cues"]=cues_for(item,guide)
    guide["inbox_preheader"]=inbox_preview(guide)
    return guide
