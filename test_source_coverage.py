"""Regression guards for a complete 49-source editorial check and honest HTTP probing."""
import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from source_coverage import audit
from source_sweep import LinkExtractor, discover_links, inspect, sweep

ROOT = Path(__file__).resolve().parent


def registry():
    return json.loads((ROOT / "discovery_sources.json").read_text())


def checked_issue(reg=None):
    reg = reg or registry()
    now = datetime.now(timezone.utc)
    issue = {
        "issue_number": "006",
        "published_at": now.isoformat(),
        "research_coverage": {"source_scans": []}
    }
    for src in reg["sources"]:
        checked = [src["official_calendar_url"]] + src.get("additional_discovery_urls", [])
        issue["research_coverage"]["source_scans"].append({
            "source_id": src["id"],
            "checked_at": (now - timedelta(hours=3)).isoformat(),
            "status": "reviewed_no_fit",
            "review_method": "public_organizer_calendar",
            "reviewer": "Stockholm editorial agent",
            "checked_urls": checked,
            "finding": "Reviewed upcoming public programme; no suitable unique events in this test fixture."
        })
    return issue


class CoverageTests(unittest.TestCase):
    def test_complete_live_registry_passes(self):
        reg = registry()
        issue = checked_issue(reg)
        out = audit(issue, reg, strict=True)
        self.assertTrue(out["ready_for_source_coverage"], out["errors"])
        self.assertEqual(out["registered_count"], 49)
        self.assertEqual(out["reviewed_count"], 49)
        self.assertEqual(out["not_checked_count"], 0)

    def test_one_missing_source_blocks_even_if_many_organizers_featured(self):
        reg = registry()
        issue = checked_issue(reg)
        issue["research_coverage"]["source_scans"].pop()
        result = audit(issue, reg, strict=True)
        self.assertFalse(result["ready_for_source_coverage"])
        self.assertEqual(result["not_checked_count"], 1)
        self.assertTrue(any("never examined" in x for x in result["errors"]))

    def test_http_probe_only_is_never_an_editorial_review(self):
        reg = registry()
        issue = checked_issue(reg)
        issue["research_coverage"]["source_scans"][0]["status"] = "index_reachable"
        result = audit(issue, reg, strict=True)
        self.assertFalse(result["ready_for_source_coverage"])
        self.assertTrue(any("probe-only" in x for x in result["errors"]))

    def test_luma_requires_city_and_all_registered_category_urls(self):
        reg = registry()
        issue = checked_issue(reg)
        row = next(x for x in issue["research_coverage"]["source_scans"]
                   if x["source_id"] == "luma-stockholm")
        row["checked_urls"] = [row["checked_urls"][0]]
        result = audit(issue, reg, strict=True)
        self.assertFalse(result["ready_for_source_coverage"])
        self.assertTrue(any("mandatory Luma category" in x for x in result["errors"]))

    def test_blocked_url_needs_two_retries_and_alternative(self):
        reg = registry()
        issue = checked_issue(reg)
        row = issue["research_coverage"]["source_scans"][0]
        row.update({
            "status": "blocked_after_retry",
            "finding": "Original calendar returns HTTP 403 and did not expose public content.",
            "attempts": [
                {"url": row["checked_urls"][0], "outcome": "HTTP 403"},
                {"url": row["checked_urls"][0], "outcome": "HTTP 403"}
            ],
            "alternate_search": "Searched original organizer publicly elsewhere; no confirmed event.",
        })
        self.assertTrue(audit(issue, reg, strict=True)["ready_for_source_coverage"])
        row["attempts"].pop()
        self.assertFalse(audit(issue, reg, strict=True)["ready_for_source_coverage"])
        row["attempts"].append({"url": row["checked_urls"][0], "outcome": "HTTP 403"})
        row.pop("alternate_search")
        self.assertFalse(audit(issue, reg, strict=True)["ready_for_source_coverage"])

    def test_too_many_blocked_is_an_incomplete_search(self):
        reg = registry()
        issue = checked_issue(reg)
        for row in issue["research_coverage"]["source_scans"][:10]:
            row.update({
                "status": "blocked_after_retry",
                "attempts": [{"url":row["checked_urls"][0],"outcome":"HTTP 403"}]*2,
                "alternate_search":"Attempted public event search through alternate host.",
            })
        self.assertFalse(audit(issue, reg, strict=True)["ready_for_source_coverage"])

    def test_stale_or_fake_future_review_blocks(self):
        reg = registry()
        issue = checked_issue(reg)
        issue["research_coverage"]["source_scans"][0]["checked_at"] = (
            datetime.now(timezone.utc)-timedelta(days=6)).isoformat()
        self.assertFalse(audit(issue, reg, strict=True)["ready_for_source_coverage"])

    def test_old_safely_sent_issue_not_retroactively_invalidated(self):
        reg = registry()
        old = {"issue_number":"005", "published_at":"2026-11-22T16:46:51+01:00"}
        self.assertTrue(audit(old, reg, strict=True)["ready_for_source_coverage"])
        self.assertEqual(audit(old, reg, strict=True)["policy"], "historical-exemption")


class SourceProbeTests(unittest.TestCase):
    def test_html_extracts_research_leads_without_confirming_them(self):
        parser = LinkExtractor()
        parser.feed('<title>Culture</title><a href="/events/2026-12-concert">Concert</a>'
                    '<a href="/privacy">Privacy</a><a href="/kalender/">Programme</a>')
        found = discover_links("https://example.org/", parser.links)
        self.assertEqual(len(found), 2)
        self.assertTrue(all(x["unverified"] for x in found))
        self.assertTrue(all(x["url"].startswith("https://") for x in found))

    def test_every_registered_source_is_probed_even_if_blocked(self):
        sample = {"sources": [
            {"id":"a","name":"A", "official_calendar_url":"https://a.example/events/"},
            {"id":"b","name":"B", "official_calendar_url":"https://b.example/events/"},
        ]}
        def fake_fetch(url, timeout=12):
            if url.startswith("https://b."):
                return {"url":url,"status":"blocked","http_code":403,"error":"HTTP 403"}
            return {"url":url,"status":"reachable","http_code":200,
                    "final_url":url,"page_title":"Upcoming",
                    "links":[("/events/2026-concert","December concert")]}
        with patch("source_sweep.fetch", side_effect=fake_fetch):
            result=sweep(sample, max_workers=2, retries=2)
        self.assertEqual(result["attempted_count"], 2)
        self.assertEqual(result["index_reachable_count"], 1)
        self.assertEqual(result["editorially_reviewed_count"], 0)
        self.assertTrue(all(x["editorial_review_status"]=="NOT_REVIEWED" for x in result["sources"]))
        self.assertEqual(len(result["sources"][1]["attempts"]), 2)


if __name__ == "__main__":
    unittest.main()
