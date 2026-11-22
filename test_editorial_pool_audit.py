"""Regression for source-to-event-to-output completeness, not merely 49 row count."""
import unittest
from editorial_pool_audit import audit

def event(url, **kw):
    return dict(url=url, title="An event", source_id="venue", verification_status="verified_eligible", **kw)

class PoolAuditTests(unittest.TestCase):
    def fixture(self):
        a, b = event("https://venue.test/a"), event("https://venue.test/b")
        return {
            "research_coverage": {"eligible_verified_events": [a,b], "source_scans": [{"source_id": "venue", "status": "reviewed_leads", "candidate_urls": [a["url"], b["url"]]}]},
            "top3": [a], "new_discoveries": [],
            "worth_reconsidering": [], "calendar_only_events": [b],
        }

    def test_reviewed_eligible_pool_reconciles_all_outputs(self):
        self.assertTrue(audit(self.fixture())["ok"])

    def test_rejects_hidden_eligible_discovery(self):
        x = self.fixture()
        x["calendar_only_events"] = []
        self.assertFalse(audit(x)["ok"])
        self.assertEqual(len(audit(x)["missing_from_outputs"]), 1)

    def test_rejects_copied_owner_test_and_missing_calendar_only(self):
        x = self.fixture()
        old = {"top3": x["top3"], "new_discoveries": [], "worth_reconsidering": [],
               "calendar_only_events": x["calendar_only_events"]}
        self.assertFalse(audit(x, comparison=old)["ok"])
        self.assertIn("reuses ALL", " ".join(audit(x, comparison=old)["errors"]))
        x["calendar_only_events"] = []
        self.assertFalse(audit(x, comparison=old)["ok"])

    def test_49_source_records_do_not_substitute_for_verified_events(self):
        x = self.fixture()
        x["research_coverage"] = {"source_scans": [{"source_id": str(i)} for i in range(49)]}
        self.assertFalse(audit(x)["ok"])

    def test_rejects_unverified_pool_entries(self):
        x = self.fixture()
        x["research_coverage"]["eligible_verified_events"][0]["verification_status"] = "raw_http_lead"
        self.assertFalse(audit(x)["ok"])

    def test_rejects_duplicate_urls_in_email_and_calendar(self):
        x = self.fixture()
        x["new_discoveries"] = [event("https://venue.test/b")]
        self.assertFalse(audit(x)["ok"])

if __name__ == "__main__":
    unittest.main()
