"""Conservative, data-backed scanning cues; never infer booking urgency from prose."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from editorial_quality import verified_timestamp

STOCKHOLM = ZoneInfo("Europe/Stockholm")


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
    if item.get("first_seen_issue")==guide.get("issue_number") and item.get("new_discovery_verified") is True:
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
            item["scan_cues"]=cues_for(item,guide)
    guide["inbox_preheader"]=inbox_preview(guide)
    return guide
