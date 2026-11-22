"""No-email tests for public iCalendar subscriptions and single-event imports."""
import tempfile
import unittest
from pathlib import Path

from build_calendar import build_data, render
from calendar_ical import filename, ical_bytes, write_feeds
from test_calendar import sample


class CalendarICSTests(unittest.TestCase):
    def setUp(self):
        self.data = build_data(sample())

    def test_feed_exports_only_dated_sessions_and_verified_closing_reminders(self):
        feed = ical_bytes(self.data["events"], self.data["published_at"])
        self.assertTrue(feed.startswith(b"BEGIN:VCALENDAR\r\n"))
        self.assertTrue(feed.endswith(b"END:VCALENDAR\r\n"))
        self.assertEqual(feed.count(b"BEGIN:VEVENT"), 2)
        text = feed.decode("utf-8")
        self.assertIn("DTSTART:20261129T180000Z", text)
        self.assertNotIn("DTEND:20261129", text, "Never guess session end times")
        self.assertIn("DTSTART;VALUE=DATE:20261206", text)
        self.assertIn("DTEND;VALUE=DATE:20261207", text)
        self.assertIn("TRANSP:TRANSPARENT", text)
        self.assertNotIn("Ongoing design exhibition", text)
        self.assertNotIn("Unbookable sold out concert", text)

    def test_individual_files_match_feed_and_uid_stable_across_sections(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            count = write_feeds(self.data, root / "calendar.ics", root / "events")
            self.assertEqual(count, 2)
            files = list((root / "events").glob("*.ics"))
            self.assertEqual(len(files), 2)
            self.assertTrue(all(p.read_bytes().count(b"BEGIN:VEVENT") == 1 for p in files))
            self.assertEqual((root / "calendar.ics").read_bytes().count(b"BEGIN:VEVENT"), 2)
            original = next(e for e in self.data["events"] if e["kind"] == "event")
            moved = dict(original, section="worth_reconsidering", id="other-1")
            self.assertEqual(filename(original), filename(moved))
            self.assertEqual(original["ical_url"], "./calendar-events/" + filename(original))

    def test_long_unicode_lines_fold_at_75_octets_and_escape_text(self):
        event = next(e for e in self.data["events"] if e["kind"] == "event").copy()
        event["title"] = "Å🌟" * 55 + r"; special, event"
        event["description"] = "Line one\r\nBEGIN:VALARM\nA, B; C \\ D"
        raw = ical_bytes([event], self.data["published_at"])
        self.assertTrue(all(len(line) <= 75 for line in raw.split(b"\r\n")))
        unfolded = raw.decode("utf-8").replace("\r\n ", "")
        self.assertIn(r"\; special\, event", unfolded)
        self.assertIn(r"Line one\nBEGIN:VALARM\nA\, B\; C \\ D", unfolded)
        self.assertEqual(unfolded.count("\r\nBEGIN:VALARM\r\n"), 0)

    def test_only_known_dates_have_ical_links(self):
        for event in self.data["events"]:
            if event["kind"] == "flexible":
                self.assertIsNone(event["ical_url"])
            else:
                self.assertTrue(event["ical_url"].endswith(".ics"))
        self.assertEqual(self.data["subscribe_url"],
                         "https://fixingman.github.io/stockholm-guide/calendar.ics")
        self.assertEqual(self.data["webcal_url"],
                         "webcal://fixingman.github.io/stockholm-guide/calendar.ics")

    def test_owner_preview_uses_separate_feed_and_event_files(self):
        import json
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sample.json"
            output = Path(folder) / "owner.html"
            source.write_text(json.dumps(sample()))
            data = render(source, output, feed_file="owner-calendar.ics", events_dir="owner-events")
            self.assertIn("owner-calendar.ics", output.read_text())
            self.assertTrue(all(e["ical_url"].startswith("./owner-events/")
                                for e in data["events"] if e.get("ical_url")))


if __name__ == "__main__":
    unittest.main()
