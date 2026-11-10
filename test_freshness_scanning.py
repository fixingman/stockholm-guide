"""Offline regression coverage for freshness, honest scan cues and private records."""
import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from editorial_scanning import enhance
from final_freshness import audit_freshness
from render_minimal import render

ROOT=Path(__file__).resolve().parent
NOW=datetime(2026,11,15,8,30,tzinfo=ZoneInfo("Europe/Stockholm"))


def sample():
    g=json.loads((ROOT/"guide_data.json").read_text(encoding="utf-8"))
    for section in ("top3","new_discoveries","worth_reconsidering","unavailable"):
        for item in g[section]:
            item["final_review"]={
              "checked_at":(NOW-timedelta(minutes=25)).isoformat(),
              "organizer_source_url":item["url"],
              "event_status":"scheduled",
              "booking_status":"unknown",
              "notes":"No current stock assertion"
            }
    return g


class FreshnessTests(unittest.TestCase):
    def test_recent_checks_pass(self):
        self.assertTrue(audit_freshness(sample(),now=NOW)["ready_for_send"])

    def test_old_review_fails(self):
        g=sample()
        g["top3"][0]["final_review"]["checked_at"]=(NOW-timedelta(days=2)).isoformat()
        self.assertFalse(audit_freshness(g,now=NOW)["ready_for_send"])

    def test_cancelled_event_must_not_remain_available(self):
        g=sample()
        g["top3"][0]["final_review"]["event_status"]="cancelled"
        self.assertFalse(audit_freshness(g,now=NOW)["ready_for_send"])

    def test_sold_out_event_must_be_moved(self):
        g=sample()
        g["new_discoveries"][0]["final_review"]["booking_status"]="sold_out"
        self.assertFalse(audit_freshness(g,now=NOW)["ready_for_send"])

    def test_fake_future_review_rejected(self):
        g=sample()
        g["top3"][0]["final_review"]["checked_at"]=(NOW+timedelta(days=1)).isoformat()
        self.assertFalse(audit_freshness(g,now=NOW)["ready_for_send"])


class ScanningTests(unittest.TestCase):
    def test_only_grounded_cues_show(self):
        g=sample()
        g["published_at"]=NOW.isoformat()
        item=g["top3"][0]
        item["event_start"]=datetime(2026,11,21,19,tzinfo=ZoneInfo("Europe/Stockholm")).isoformat()
        item["booking_signal"]="advance_required"
        item["verification"]={"booking":{"status":"confirmed"}}
        item["first_seen_issue"]=g["issue_number"]
        item["new_discovery_verified"]=True
        got=enhance(g)
        self.assertEqual(got["top3"][0]["scan_cues"],["THIS WEEKEND","BOOK AHEAD"])
        self.assertIn(g["top3"][0]["title"],got["inbox_preheader"])
        self.assertLessEqual(len(got["inbox_preheader"]),123)

    def test_unknown_booking_does_not_show_urgency(self):
        g=sample();g["top3"][0]["booking_signal"]="limited"
        g["top3"][0]["verification"]={"booking":{"status":"unknown"}}
        self.assertNotIn("LIMITED PLACES",enhance(g)["top3"][0]["scan_cues"])

    def test_newness_requires_issue_identity(self):
        g=sample();g["new_discoveries"][0]["first_seen_issue"]="001"
        g["new_discoveries"][0]["new_discovery_verified"]=True
        self.assertNotIn("JUST FOUND",enhance(g)["new_discoveries"][0]["scan_cues"])

    def test_full_list_survives_enhancement_and_render(self):
        g=sample();n=sum(len(g[k]) for k in ("top3","new_discoveries","worth_reconsidering","unavailable"))
        self.assertEqual(n,sum(len(enhance(g)[k]) for k in ("top3","new_discoveries","worth_reconsidering","unavailable")))
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"issue.json";out=Path(tmp)/"out.html"
            path.write_text(json.dumps(g),encoding="utf-8")
            _,h=render(path,out,"https://fixingman.github.io/stockholm-guide/assets")
            self.assertEqual(h.count('class="event-name"'),n)
            self.assertIn('THIS WEEKEND',enhance({**g,"published_at":NOW.isoformat(),"top3":[{**g["top3"][0],"event_start":"2026-11-21T19:00:00+01:00"},*g["top3"][1:]]})["top3"][0]["scan_cues"])


if __name__=="__main__":
    unittest.main()
