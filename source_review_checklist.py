#!/usr/bin/env python3
"""Create an honest, complete source-review checklist for the next issue.

Every registered source appears exactly once. The public sweep may provide
candidate URLs and HTTP errors, but no row is marked as editorially reviewed.
Saturday/Sunday agents must replace NOT_REVIEWED with a genuine review result,
carried into issue.research_coverage.source_scans. Private records not used.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from source_coverage import https


def build(registry, probe):
    sources = registry.get("sources", [])
    observations = {p["source_id"]: p for p in probe.get("sources", [])}
    if len(observations) != len(probe.get("sources", [])):
        raise ValueError("Probe contains duplicate source IDs")
    expected = {s["id"] for s in sources}
    if not expected or len(expected) != len(sources):
        raise ValueError("Empty or duplicate source registry")
    if set(observations) != expected:
        missing = sorted(expected - set(observations))
        extra = sorted(set(observations) - expected)
        raise ValueError(f"Probe/registry mismatch: missing {missing}, extra {extra}")
    rows = []
    for src in sources:
        p = observations[src["id"]]
        base = src["official_calendar_url"]
        urls = list(dict.fromkeys([base] + src.get("additional_discovery_urls", [])))
        if not all(https(u) for u in urls):
            raise ValueError(f"Invalid public source URL in {src['id']}")
        raw = p.get("candidate_links", [])
        rows.append({
            "source_id": src["id"],
            "source_name": src["name"],
            "status": "NOT_REVIEWED",
            "checked_at": None,
            "reviewer": None,
            "review_method": None,
            "checked_urls": [],
            "required_urls": urls,
            "finding": None,
            "candidate_urls": [],
            "probe_status": p.get("probe_status"),
            "probe_http_attempts": p.get("attempts", []),
            "probe_browser_attempts": p.get("browser_attempts", []),
            "unverified_candidate_leads": [link for link in raw if isinstance(link, dict) and https(link.get("url"))][:18],
            "note": "These are UNVERIFIED leads; this row must be reviewed and completed by the editorial agent. Do not copy status NOT_REVIEWED into a released issue.",
        })
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_probe_created_at": probe.get("created_at"),
        "registry_count": len(sources),
        "accounted_for_count": len(rows),
        "editorially_reviewed_count": 0,
        "rows": rows,
        "instructions": [
            "Read every registered source's original public calendar or fallback; verify actual future event dates and venue information.",
            "For verified public pages, set reviewed_leads with original public candidate URLs or reviewed_no_fit with source-specific finding.",
            "For inaccessible pages, document at least two attempts and an alternate public search, then blocked_after_retry.",
            "Set timezone-aware checked_at and actual reviewer and method. Include original registered index in checked_urls, all Luma categories for Luma.",
            "Publish only the completed rows as issue.research_coverage.source_scans; source_coverage.py will reject unchecked or boilerplate rows.",
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", default="discovery_sources.json")
    p.add_argument("--probe", default="research/source-probe.json")
    p.add_argument("--output", default="research/source-review-checklist.json")
    a = p.parse_args()
    registry = json.loads(Path(a.registry).read_text(encoding="utf-8"))
    probe = json.loads(Path(a.probe).read_text(encoding="utf-8"))
    data = build(registry, probe)
    target = Path(a.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "registered": data["registry_count"],
        "checklist_records": len(data["rows"]),
        "editorially_reviewed": data["editorially_reviewed_count"],
        "output": str(target),
    }))


if __name__ == "__main__":
    main()
