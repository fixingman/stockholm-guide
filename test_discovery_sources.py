"""Regression checks for the persistent Stockholm Guide discovery registry.

These assert source coverage and access policy, not that external organizers
currently have events, nor that a login-gated page was accessible.
"""
import json
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent


class DiscoverySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = json.loads((ROOT / "discovery_sources.json").read_text())
        cls.sources = cls.registry["sources"]
        cls.by_id = {item["id"]: item for item in cls.sources}

    def test_registry_has_unique_sources_and_https(self):
        self.assertEqual(len(self.sources), len(self.by_id))
        self.assertGreaterEqual(len(self.sources), 28)
        for item in self.sources:
            self.assertTrue(item.get("name"))
            url = item["official_calendar_url"]
            self.assertEqual(urlsplit(url).scheme, "https", item["id"])
            self.assertTrue(urlsplit(url).hostname, item["id"])

    def test_user_preferences_are_preserved(self):
        self.assertNotIn("slakthusen", self.by_id)
        self.assertIn("fallan", self.by_id)
        self.assertIn("fargfabriken", self.by_id)
        lumen = self.by_id["lumen-project"]
        self.assertEqual(lumen["discovery_priority"], "personal-favorite-highest")
        self.assertIn("lumenproject.se", lumen["official_calendar_url"])

    def test_multiple_discovery_platforms_and_luma_categories(self):
        for source_id in ("visit-stockholm", "luma-stockholm", "meetup-stockholm",
                          "tickster-stockholm", "resident-advisor", "stockholm-events-cross-index"):
            self.assertIn(source_id, self.by_id)
            self.assertEqual(self.by_id[source_id]["source_type"], "aggregator")
        luma = self.by_id["luma-stockholm"]
        self.assertEqual(luma["official_calendar_url"], "https://luma.com/stockholm")
        self.assertTrue(any("/arts" in x for x in luma["additional_discovery_urls"]))
        self.assertTrue(any("/tech" in x for x in luma["additional_discovery_urls"]))

    def test_expanded_unique_stockholm_sources_and_luma_scan_accountability(self):
        # Future regressions must not silently drop the independent venues
        # or revert to merely registering Luma without scanning it.
        required = (
            "cyklopen", "ronnells-antikvariat", "filmform",
            "frim-stockholm", "moderna-museet-stockholm",
            "arkdes-events", "cinemateket-stockholm",
            "thirdplace-stockholm", "startskott-stockholm",
        )
        self.assertGreaterEqual(len(self.sources), 49)
        for source_id in required:
            self.assertIn(source_id, self.by_id)
            self.assertTrue(self.by_id[source_id]["editorial_fit"])
            self.assertTrue(self.by_id[source_id]["editorial_instructions"])
            self.assertTrue(self.by_id[source_id]["official_calendar_url"].startswith("https://"))
        policy = self.registry["source_diversity_policy"]
        self.assertIn("Luma", policy["luma_explicit_check"])
        self.assertIn("Log", policy["luma_explicit_check"])
        self.assertIn("not checked", policy["scanning_accountability"])
        self.assertIn("do not", policy["new_source_rotation"].lower() + " do not assume all sources scanned")

    def test_no_signup_bypass_or_unverified_publication_policy(self):
        policy = self.registry["source_diversity_policy"]
        self.assertIn("Never sign in", policy["access_policy"])
        self.assertIn("original organizer", policy["aggregators"])
        self.assertIn("deduplicate", policy["overlap_policy"].lower())
        self.assertIn("private", self.by_id["luma-stockholm"]["editorial_instructions"].lower())

    def test_recurring_scanning_targets(self):
        p = self.registry["source_diversity_policy"]
        self.assertGreaterEqual(p["review_target_distinct_sources"], 12)
        self.assertGreaterEqual(p["review_target_categories"], 5)


if __name__ == "__main__":
    unittest.main()
