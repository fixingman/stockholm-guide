#!/usr/bin/env python3
"""Rank a researched candidate pool without letting one organizer dominate.

Candidate discovery itself must use live organizer sources. This code NEVER
invents events and NEVER treats a ranking score as confirmation of availability.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from editorial_quality import hostname,event_key,SECTIONS


def rank(candidates, history=(), limit=24, max_per_organizer=4):
    previous={event_key(item) for issue in history for section in SECTIONS for item in issue.get(section,[])}
    seen=set();organizers=Counter();selected=[];deferred=[]
    for item in candidates:
        key=event_key(item)
        if not key or key in seen or not hostname(item.get("url")):
            deferred.append({"title":item.get("title"),"reason":"duplicate_or_invalid_link"})
            continue
        seen.add(key)
        domain=hostname(item.get("organizer_url")) or hostname(item.get("url"))
        score=0
        score+=3 if item.get("novelty")=="unusual" else 1
        score+=3 if item.get("participatory") else 0
        score+=2 if item.get("evidence_url") and hostname(item["evidence_url"]) else 0
        score+=2 if item.get("image_candidate_url") else 0
        score-=4 if key in previous else 0
        score-=2 if domain in ("visitstockholm.com","evenemangstockholm.se","eventbrite.com") else 0
        item_copy=dict(item)
        item_copy["_selection_score"]=score
        item_copy["_organizer_domain"]=domain
        item_copy["_seen_in_previous_issue"]=key in previous
        selected.append(item_copy)
    selected.sort(key=lambda x:x["_selection_score"],reverse=True)
    output=[]
    for item in selected:
        dom=item["_organizer_domain"]
        if len(output)>=limit:break
        if organizers[dom]>=max_per_organizer:
            deferred.append({"title":item.get("title"),"reason":"organizer_cap","organizer":dom})
            continue
        organizers[dom]+=1;output.append(item)
    return {"selected":output,"deferred":deferred,
            "organizers":dict(organizers),"candidate_count":len(candidates),
            "note":"Ranking candidates only; fact-check, date-filter and confirm live event evidence separately."}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--candidates",required=True)
    p.add_argument("--history",action="append",default=[])
    p.add_argument("--output",default="discovery-shortlist.json")
    p.add_argument("--limit",type=int,default=24)
    p.add_argument("--organizer-cap",type=int,default=4)
    a=p.parse_args()
    candidates=json.loads(Path(a.candidates).read_text())
    history=[json.loads(Path(f).read_text()) for f in a.history]
    result=rank(candidates,history,limit=a.limit,max_per_organizer=a.organizer_cap)
    Path(a.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(f"Selected {len(result['selected'])} from {len(candidates)} candidates across {len(result['organizers'])} organizers")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
