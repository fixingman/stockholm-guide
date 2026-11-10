#!/usr/bin/env python3
"""Editorial quality checks: event evidence, source diversity, repetition and image identity.

Offline by design. A green score means the evidence fields are present and
internally consistent; it never proves ticket availability or photo rights.
"""
import argparse
import json
import re
from collections import Counter
from datetime import datetime, date, timezone
from pathlib import Path
from urllib.parse import urlparse

SECTIONS=("top3","new_discoveries","worth_reconsidering","unavailable")
FIELDS=("date","venue","booking","price")
GENERIC=("eventbrite.com","facebook.com","instagram.com","visitstockholm.com",
         "ticketmaster.se","evenemangstockholm.se","nortic.se")


def hostname(url):
    try:
        p=urlparse(url or "")
        return (p.hostname or "").lower().removeprefix("www.") if p.scheme=="https" else ""
    except ValueError:
        return ""


def event_key(item):
    return re.sub(r"[^a-z0-9]+", " ", item.get("title","").casefold()).strip()


def verified_timestamp(value):
    try:
        moment=datetime.fromisoformat(value.replace("Z","+00:00"))
        return moment if moment.tzinfo else None
    except (ValueError, AttributeError):
        return None


def audit(issue, history=(), strict=False, as_of=None):
    now=as_of or datetime.now(timezone.utc)
    errors=[]; warnings=[]; all_items=[]; organizers=[]; seen={}; records=[]
    for section in SECTIONS:
        for item in issue.get(section,[]):
            key=event_key(item)
            if key in seen and seen[key]!=section:
                # Same item is allowed in featured and a section, but is not unique discovery.
                if section!="top3" and seen[key]!="top3":
                    warnings.append("Repeated event across sections: "+item.get("title","?"))
            seen.setdefault(key,section)
            evidence=item.get("verification",{})
            source=hostname(item.get("url"))
            organizer=hostname(item.get("organizer_url")) or source
            if organizer in GENERIC:
                warnings.append("Generic listing instead of direct organizer source: "+item.get("title","?"))
            if not source:
                errors.append("Invalid event link: "+item.get("title","?"))
            organizers.append(organizer)
            record={"title":item.get("title"),"section":section,"source":source,"organizer":organizer}
            verified_at=verified_timestamp(evidence.get("checked_at","")) if isinstance(evidence,dict) else None
            if not verified_at:
                (errors if strict else warnings).append("Missing timestamped event verification: "+item.get("title","?"))
            elif verified_at>now:
                errors.append("Future-dated event verification: "+item.get("title","?"))
            elif (now-verified_at).total_seconds()>7*86400:
                (errors if strict else warnings).append("Stale event verification (>7 days): "+item.get("title","?"))
            for field in FIELDS:
                part=evidence.get(field,{}) if isinstance(evidence,dict) else {}
                if not isinstance(part,dict) or part.get("status") not in ("confirmed","unknown","unavailable") or not hostname(part.get("source_url","")):
                    (errors if strict else warnings).append("Missing explicit "+field+" evidence: "+item.get("title","?"))
                elif part.get("status")=="unknown" and not part.get("note"):
                    (errors if strict else warnings).append("Unknown "+field+" requires explanation: "+item.get("title","?"))
            # Date-time should be machine-readable where exact start is known.
            if strict and section!="unavailable" and not item.get("event_start") and not item.get("schedule_note"):
                errors.append("Missing event_start ISO timestamp or schedule_note: "+item.get("title","?"))
            if item.get("event_start") and not verified_timestamp(item["event_start"]):
                errors.append("Invalid event_start timezone: "+item.get("title","?"))
            records.append(record);all_items.append(item)
    unique={event_key(x) for x in all_items if event_key(x)}
    domains={x for x in organizers if x}
    total=len(unique)
    if len(domains)<3:
        warnings.append("Less than three organizer domains represented")
    count=Counter(organizers)
    concentration=max(count.values())/len(organizers) if organizers else 0
    if concentration>0.45:
        warnings.append("One organizer dominates over 45% of entries")
    past={event_key(x) for old in history for section in SECTIONS for x in old.get(section,[])}
    current_new={event_key(x) for x in issue.get("new_discoveries",[])}
    repeats=sorted(current_new & past)
    if repeats:
        warnings.append(str(len(repeats))+" items labeled new were in previous issues")
    reviewed=0
    for item in issue.get("top3",[]):
        if not item.get("image_verified"):
            warnings.append("Top 3 has no verified photo: "+item.get("title","?"))
            continue
        proof=item.get("image_identity_review",{})
        ok=(isinstance(proof,dict) and proof.get("event_match") is True
            and bool(proof.get("reviewer")) and hostname(proof.get("source_page",""))
            and verified_timestamp(proof.get("checked_at","")) is not None
            and (proof.get("source_page")==item.get("url") or
                 proof.get("source_page") in item.get("image_source_pages",[])))
        if ok:reviewed+=1
        else:(errors if strict else warnings).append("Featured photo identity not independently reviewed: "+item.get("title","?"))
    return {
        "ready_for_editorial_release":not errors,
        "mode":"strict" if strict else "legacy-baseline",
        "errors":errors,"warnings":warnings,
        "unique_events":total,"total_rows":len(all_items),
        "organizer_count":len(domains),"dominant_organizer_share":round(concentration,3),
        "organizer_domains":sorted(domains),"repeat_new_discoveries":repeats,
        "identity_reviewed_images":reviewed,"identity_review_target":len(issue.get("top3",[])),
        "event_evidence_rows":records,
        "note":"Evidence bookkeeping, not automated factual confirmation or legal image clearance."
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--data",required=True)
    p.add_argument("--history",action="append",default=[])
    p.add_argument("--strict",action="store_true")
    p.add_argument("--report",default="editorial-quality-report.json")
    a=p.parse_args()
    issue=json.loads(Path(a.data).read_text())
    history=[json.loads(Path(path).read_text()) for path in a.history]
    report=audit(issue,history,strict=a.strict)
    Path(a.report).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:report[k] for k in ("ready_for_editorial_release","mode","errors","warnings","unique_events","organizer_count","repeat_new_discoveries","identity_reviewed_images")},indent=2))
    return 0 if report["ready_for_editorial_release"] else 1


if __name__=="__main__":
    raise SystemExit(main())
