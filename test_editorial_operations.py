"""Offline QA for editorial evidence, source diversity, image review and list hygiene."""
import copy
import json
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from editorial_quality import audit
from recipient_guard import audit as recipients
from discovery_ranker import rank


ROOT=Path(__file__).resolve().parent


def make_strict_issue():
    g=json.loads((ROOT/"guide_data.json").read_text())
    timestamp=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat()
    for section in ("top3","new_discoveries","worth_reconsidering","unavailable"):
        for item in g[section]:
            item["event_start"]="2026-11-20T19:00:00+01:00"
            item["organizer_url"]=item["url"]
            item["verification"]={"checked_at":timestamp}
            for field in ("date","venue","booking","price"):
                item["verification"][field]={"status":"confirmed","source_url":item["url"]}
    for item in g["top3"]:
        item["image_identity_review"]={"event_match":True,
                                      "reviewer":"Human editorial review (test fixture)",
                                      "source_page":item["image_source_url"],
                                      "checked_at":timestamp}
    return g


class EditorialTests(unittest.TestCase):
    def test_legacy_issues_report_gaps_without_false_verification(self):
        g=json.loads((ROOT/"guide_data.json").read_text())
        r=audit(g)
        self.assertTrue(r["ready_for_editorial_release"])
        self.assertEqual(r["identity_reviewed_images"],0)
        self.assertTrue(any("verification" in e for e in r["warnings"]))

    def test_strict_valid_evidence_passes(self):
        g=make_strict_issue()
        # Saturday event's image was from official organizer festival page.
        self.assertTrue(audit(g,strict=True)["ready_for_editorial_release"])

    def test_missing_event_verification_blocks_strict(self):
        g=make_strict_issue()
        del g["top3"][0]["verification"]["date"]
        r=audit(g,strict=True)
        self.assertFalse(r["ready_for_editorial_release"])
        self.assertTrue(any("date evidence" in e for e in r["errors"]))

    def test_image_matching_is_an_independent_editorial_check(self):
        g=make_strict_issue()
        g["top3"][2]["image_identity_review"]["event_match"]=False
        r=audit(g,strict=True)
        self.assertFalse(r["ready_for_editorial_release"])
        self.assertTrue(any("photo identity" in e for e in r["errors"]))

    def test_stale_verification_fails(self):
        g=make_strict_issue()
        g["top3"][1]["verification"]["checked_at"]="2026-01-01T10:00:00+01:00"
        self.assertFalse(audit(g,strict=True)["ready_for_editorial_release"])

    def test_repeated_discovery_detected(self):
        g=make_strict_issue()
        prior={"new_discoveries":[{"title":g["new_discoveries"][0]["title"]}]}
        r=audit(g,history=[prior],strict=True)
        self.assertEqual(len(r["repeat_new_discoveries"]),1)


class SubscriberTests(unittest.TestCase):
    def run_guard(self, **updates):
        opts=dict(to=["owner@example.org"], bcc=["friend@example.org"],
                  consented=["owner@example.org","friend@example.org"],
                  unsubscribe_mailbox="owner@example.org",mode="scheduled")
        opts.update(updates)
        return recipients(**opts)

    def test_normal_scheduled_list(self):
        self.assertTrue(self.run_guard()["ready_for_send"])

    def test_no_bcc_for_test(self):
        r=self.run_guard(mode="test")
        self.assertFalse(r["ready_for_send"])
        self.assertTrue(any("BCC" in e for e in r["errors"]))

    def test_test_owner_only(self):
        self.assertTrue(self.run_guard(mode="test",bcc=[])["ready_for_send"])

    def test_suppressed_recipient_never_sent(self):
        r=self.run_guard(suppressed=["friend@example.org"])
        self.assertFalse(r["ready_for_send"])

    def test_unknown_consent_blocks(self):
        r=self.run_guard(consented=["owner@example.org"])
        self.assertFalse(r["ready_for_send"])

    def test_invalid_and_duplicate_recipient(self):
        self.assertFalse(self.run_guard(bcc=["owner@example.org"])["ready_for_send"])
        self.assertFalse(self.run_guard(bcc=["bad address"])["ready_for_send"])

    def test_no_unsubscribe_mailbox_blocks(self):
        self.assertFalse(self.run_guard(unsubscribe_mailbox="")["ready_for_send"])



class DiscoveryTests(unittest.TestCase):
    def test_organizer_cap_and_duplicate_filter(self):
        candidates=[{"title":f"Event {i}","url":f"https://same.example.org/{i}","novelty":"unusual"} for i in range(6)]
        candidates.append({"title":"Other organizer","url":"https://other.example.org/event","novelty":"unusual"})
        ranked=rank(candidates,limit=10,max_per_organizer=2)
        self.assertEqual(len(ranked["selected"]),3)
        self.assertTrue(any(x["reason"]=="organizer_cap" for x in ranked["deferred"]))

    def test_previous_issue_penalizes_repeat(self):
        candidates=[{"title":"Repeated event","url":"https://one.example.org/repeat","novelty":"unusual"},
                    {"title":"New event","url":"https://two.example.org/new","novelty":"unusual"}]
        previous={"new_discoveries":[{"title":"Repeated event"}]}
        ranked=rank(candidates,history=[previous])
        self.assertEqual(ranked["selected"][0]["title"],"New event")

if __name__=="__main__":
    unittest.main()
