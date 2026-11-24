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

    def test_explicit_range_gives_single_download_full_interval_only(self):
        issue = sample()
        issue["top3"][0]["dates"] = "Sun 29 Nov · 19:00–21:00"
        data = build_data(issue)
        event = next(e for e in data["events"] if e["kind"] == "event")
        self.assertEqual(event["single_event_end"], "2026-11-29T21:00:00+01:00")
        single = ical_bytes([event], data["published_at"], single_download=True).decode()
        feed = ical_bytes([event], data["published_at"]).decode()
        self.assertIn("DTSTART:20261129T180000Z", single)
        self.assertIn("DTEND:20261129T200000Z", single)
        self.assertNotIn("DTEND:20261129T200000Z", feed)
        self.assertIn("End time is not confirmed", feed)

    def test_explicit_end_cue_and_overnight_intervals(self):
        issue = sample()
        issue["top3"][0]["dates"] = "doors 19:00 · ends 23:00"
        event = next(e for e in build_data(issue)["events"] if e["kind"] == "event")
        self.assertEqual(event["single_event_end"], "2026-11-29T23:00:00+01:00")
        issue["top3"][0]["dates"] = "19:00–01:00"
        event = next(e for e in build_data(issue)["events"] if e["kind"] == "event")
        self.assertEqual(event["single_event_end"], "2026-11-30T01:00:00+01:00")

    def test_never_guess_end_time_or_use_exhibition_closing_as_session_end(self):
        issue = sample()
        issue["top3"][0]["event_end"] = "2026-12-30T23:00:00+01:00"
        issue["top3"][0]["dates"] = "doors 19:00 · show 20:00"
        event = next(e for e in build_data(issue)["events"] if e["kind"] == "event")
        self.assertIsNone(event["single_event_end"])
        single = ical_bytes([event], issue["published_at"], single_download=True).decode()
        self.assertNotIn("DTEND:", single)
        self.assertIn("End time is not confirmed", single)
        issue["top3"][0]["dates"] = "18:00–20:00"  # Does not match actual 19:00 start
        event = next(e for e in build_data(issue)["events"] if e["kind"] == "event")
        self.assertIsNone(event["single_event_end"])

    def test_structured_session_end_and_per_file_distinction(self):
        issue = sample()
        issue["top3"][0]["session_end"] = "2026-11-29T22:30:00+01:00"
        data = build_data(issue)
        event = next(e for e in data["events"] if e["kind"] == "event")
        self.assertEqual(event["single_event_end"], "2026-11-29T22:30:00+01:00")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            write_feeds(data, root / "calendar.ics", root / "events")
            individual = (root / "events" / filename(event)).read_text()
            subscribed = (root / "calendar.ics").read_text()
            self.assertIn("DTEND:20261129T213000Z", individual)
            self.assertNotIn("DTEND:20261129T213000Z", subscribed)
            self.assertNotIn("End time is not confirmed", individual)
            self.assertIn("End time is not confirmed", subscribed)

    def test_exact_exhibition_date_window_is_offered_only_as_optional_visit(self):
        issue = sample()
        issue["new_discoveries"][0]["schedule_note"] = (
            "Open 27 Nov 2026–10 Jan 2027; museum hours vary."
        )
        data = build_data(issue)
        exhibition = next(e for e in data["events"] if e["kind"] == "flexible")
        self.assertEqual(exhibition["visit_window"], {
            "start": "2026-11-27", "end": "2027-01-10"
        })
        self.assertIsNone(exhibition["ical_url"])
        self.assertNotIn("Ongoing design exhibition",
                         ical_bytes(data["events"], data["published_at"]).decode())

        # No unbounded/vague dates may produce a visit picker.
        issue["new_discoveries"][0]["schedule_note"] = "Open all winter; ask venue."
        exhibition = next(e for e in build_data(issue)["events"] if e["kind"] == "flexible")
        self.assertIsNone(exhibition["visit_window"])

    def test_multiday_festival_not_added_as_hourly_or_blocked_all_week(self):
        issue = sample()
        event = issue["top3"][0]
        event["dates"] = "Festival through 1 Dec · doors 19:00"
        event["event_end"] = "2026-12-01T19:00:00+01:00"
        event["visit_start"] = "2026-11-29"
        event["visit_end"] = "2026-12-01"
        event["calendar_mode"] = "multi_day"
        data = build_data(issue)
        item = next(e for e in data["events"] if e["title"] == "Evening concert")
        self.assertEqual(item["kind"], "flexible")
        self.assertEqual(item["visit_window"]["end"], "2026-12-01")
        self.assertIsNone(item["ical_url"])
        feed = ical_bytes(data["events"], data["published_at"]).decode()
        self.assertNotIn("Evening concert", feed)
        self.assertNotIn("DTSTART;VALUE=DATE:20261129", feed)
        self.assertIn("DTSTART;VALUE=DATE:20261206", feed)  # existing closing reminder

    def test_structured_multiple_sessions_offer_precise_choices_not_durations(self):
        issue = sample()
        event = issue["top3"][0]
        event["event_start"] = None
        event["sessions"] = [
            {"event_start": "2026-11-30T20:00:00+01:00",
             "session_end": "2026-11-30T22:00:00+01:00",
             "dates": "Mon 30 Nov · 20:00–22:00"},
            {"event_start": "2026-11-29T19:00:00+01:00",
             "dates": "Sun 29 Nov · 19:00"},
            {"event_start": "unverified date"},
        ]
        data = build_data(issue)
        item = next(e for e in data["events"] if e["title"] == "Evening concert")
        self.assertEqual(item["kind"], "event")
        self.assertEqual(item["date"], "2026-11-29")
        self.assertEqual([x["date"] for x in item["sessions"]],
                         ["2026-11-29", "2026-11-30"])
        self.assertEqual(item["sessions"][0]["start_utc"], "20261129T180000Z")
        self.assertIsNone(item["sessions"][0]["end_utc"])
        self.assertEqual(item["sessions"][1]["end_utc"], "20261130T210000Z")
        self.assertEqual(item["sessions"][1]["time"], "20:00")

    def test_exhibition_range_metadata_is_not_overridden_by_session_end(self):
        issue = sample()
        event = issue["top3"][0]
        event["schedule_note"] = "Exhibition 27 Nov 2026–10 Jan 2027"
        event["event_end"] = "2027-01-10T17:00:00+01:00"
        event["dates"] = "Fri 29 Nov · opening at 19:00"
        data = build_data(issue)
        item = next(e for e in data["events"] if e["title"] == "Evening concert")
        self.assertEqual(item["kind"], "event",
                         "A distinct timed opening should remain a timed session")
        self.assertEqual(item["visit_window"]["end"], "2027-01-10")
        self.assertIsNone(item["single_event_end"])

    def test_current_real_exhibitions_have_selection_windows(self):
        import json
        repo = Path(__file__).resolve().parent
        issue = json.loads((repo / "issues" / "current.json").read_text())
        data = build_data(issue)
        windows = {e["title"]: e["visit_window"]
                   for e in data["events"] if e.get("visit_window")}
        self.assertEqual(
            windows["Pepparkakshus 2026 — Gingerbread architecture of the future"],
            {"start": "2026-11-27", "end": "2027-01-10"}
        )
        self.assertEqual(
            windows["Women Behind the Camera, 1848–1968 — exhibition opening"],
            {"start": "2026-12-05", "end": "2027-04-11"}
        )

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
