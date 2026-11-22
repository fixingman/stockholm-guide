"""Regression tests for the public no-send calendar and accurate dated events."""
import json
import tempfile
import unittest
from pathlib import Path

from build_calendar import build_data, render


def sample():
    source = "https://example.org/events/current"
    return {
        "issue_number": "006",
        "date_range": "29 November–12 December 2026",
        "published_at": "2026-11-29T08:00:00+01:00",
        "top3": [{
            "title": "Evening concert",
            "dates": "Sun 29 Nov · 19:00",
            "event_start": "2026-11-29T19:00:00+01:00",
            "url": source,
            "venue": "An arts space",
            "price": "100 SEK",
            "booking": "Check organizer",
        }],
        "new_discoveries": [{
            "title": "Ongoing design exhibition",
            "dates": "Runs into January",
            "schedule_note": "Open throughout November and December",
            "url": "https://example.org/exhibition",
            "venue": "Museum",
        }],
        "worth_reconsidering": [{
            "title": "A long-running exhibition",
            "dates": "Closes 6 Dec",
            "last_chance": True,
            "event_end": "2026-12-06T17:00:00+01:00",
            "last_chance_source_url": "https://example.org/exhibition/closing",
            "url": "https://example.org/exhibition/closing",
            "final_review": {
                "organizer_source_url": "https://example.org/exhibition/closing",
                "event_status": "scheduled",
                "booking_status": "not_required",
            },
            "venue": "Gallery",
        }],
        "unavailable": [{
            "title": "Unbookable sold out concert",
            "dates": "5 Dec 2026",
            "event_start": "2026-12-05T20:00:00+01:00",
            "url": "https://example.org/soldout",
        }],
    }


class CalendarTests(unittest.TestCase):
    def test_precise_date_flexible_date_and_verified_closing(self):
        d = build_data(sample())
        self.assertEqual(d["event_count"], 3)
        self.assertEqual((d["window_start"], d["window_end"]), ("2026-11-29", "2026-12-12"))
        entries = {x["title"]: x for x in d["events"]}
        self.assertEqual(entries["Evening concert"]["date"], "2026-11-29")
        self.assertEqual(entries["Evening concert"]["time"], "19:00")
        self.assertEqual(entries["Ongoing design exhibition"]["kind"], "flexible")
        self.assertIsNone(entries["Ongoing design exhibition"]["date"])
        self.assertEqual(entries["A long-running exhibition"]["date"], "2026-12-06")
        self.assertEqual(entries["A long-running exhibition"]["kind"], "closing")
        self.assertTrue(entries["A long-running exhibition"]["last_chance"])
        self.assertNotIn("Unbookable sold out concert", entries)

    def test_no_unverified_last_chance_pins_or_just_found_overrides(self):
        issue = sample()
        closing = issue["worth_reconsidering"][0]
        closing["final_review"]["organizer_source_url"] = "https://example.org/different-event"
        d = build_data(issue)
        other = next(x for x in d["events"] if x["title"] == "A long-running exhibition")
        self.assertIsNone(other["date"])
        self.assertFalse(other["last_chance"])
        self.assertEqual(other["kind"], "flexible")

    def test_converts_utc_start_to_stockholm_calendar_date(self):
        issue = sample()
        issue["top3"][0]["event_start"] = "2026-11-28T23:30:00+00:00"
        item = next(x for x in build_data(issue)["events"] if x["section"] == "top3")
        self.assertEqual(item["date"], "2026-11-29")
        self.assertEqual(item["time"], "00:30")

    def test_invalid_url_omitted_and_script_breakout_is_escaped(self):
        issue = sample()
        issue["new_discoveries"][0]["title"] = '</script><script>alert("danger")</script>'
        issue["top3"][0]["url"] = "javascript:alert(1)"
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "issue.json"
            out = Path(temp) / "calendar.html"
            p.write_text(json.dumps(issue))
            d = render(p, out)
            html = out.read_text()
            self.assertEqual(d["event_count"], 2)
            self.assertNotIn('</script><script>alert', html)
            self.assertIn("calendar.js", html)
            self.assertIn("fullcalendar@6.1.22/index.global.min.js", html)
            self.assertIn('id="fullcalendar"', html)
            self.assertNotIn('id="month-grid"', html)  # No hand-maintained date grid.
            self.assertIn("application/json", html)
            self.assertIn("Official event page", html)

    def test_public_issue_renders_and_every_dated_card_has_source(self):
        repo = Path(__file__).resolve().parent
        current = repo / "issues" / "current.json"
        if not current.exists():
            self.skipTest("No current issue found")
        with tempfile.TemporaryDirectory() as temp:
            d = render(current, Path(temp) / "calendar.html")
        self.assertGreaterEqual(d["event_count"], 3)
        self.assertEqual(sum(e["section"] == "top3" for e in d["events"]), 3)
        self.assertTrue(all(e["url"].startswith("https://") for e in d["events"]))
        self.assertFalse(any(e["section"] == "unavailable" for e in d["events"]))
        self.assertTrue(all(e["date"] is None or len(e["date"]) == 10 for e in d["events"]))


if __name__ == "__main__":
    unittest.main()
