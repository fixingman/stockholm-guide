"""Regression suite for pre-send delivery manifest and Gmail read-back."""
import json
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path

from delivery_guard import assess, create_manifest, extract_html_from_mime, verify_sent_html
from render_minimal import render

ROOT = Path(__file__).resolve().parent


class DeliveryGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "guide_data.json").read_text())
        with tempfile.TemporaryDirectory() as directory:
            _, cls.html = render(ROOT / "guide_data.json", Path(directory) / "email.html",
                                 "https://fixingman.github.io/stockholm-guide/assets")

    def test_complete_sample_passes_offline(self):
        result = assess(self.data, self.html)
        self.assertTrue(result["ready_for_delivery"], result["errors"])
        self.assertEqual(result["total_event_rows"], 24)
        self.assertEqual(len(result["featured_images"]), 3)
        self.assertEqual(result["inline_fallbacks"], 0)

    def test_old_placeholder_delivery_is_blocked(self):
        bad = self.html.replace(self.data["top3"][0]["image_url"], "https://example.com/event-placeholder-thumb.jpg")
        report = assess(self.data, bad)
        self.assertFalse(report["ready_for_delivery"])
        self.assertTrue(any("placeholder" in e.lower() for e in report["errors"]))

    def test_missing_black_header_blocks_delivery(self):
        bad = self.html.replace("background:#161616;", "background:#eee;", 1)
        report = assess(self.data, bad)
        self.assertFalse(report["ready_for_delivery"])
        self.assertIn("Missing or altered black section-title strips", report["errors"])

    def test_incomplete_event_rows_blocks_delivery(self):
        bad = self.html.replace('class="event-card-link"', 'class="something-else"', 1)
        self.assertFalse(assess(self.data, bad)["ready_for_delivery"])

    def test_duplicate_event_image_is_blocked(self):
        first=self.data["top3"][0]["image_url"]
        second=self.data["top3"][1]["image_url"]
        data=json.loads(json.dumps(self.data))
        data["top3"][1]["image_url"]=first
        html=self.html.replace(second, first)
        self.assertFalse(assess(data, html)["ready_for_delivery"])

    def test_image_download_failure_blocks_delivery(self):
        result=assess(self.data, self.html, network=True,
                      checker=lambda url: {"url": url, "ok": False, "reason": "remote server refused"})
        self.assertFalse(result["ready_for_delivery"])
        self.assertEqual(len(result["image_checks"]), 3)

    def test_manifest_and_sent_mime_match(self):
        with tempfile.TemporaryDirectory() as directory:
            d=Path(directory)
            data=d/"issue.json"
            html_file=d/"email.html"
            data.write_text(json.dumps(self.data))
            html_file.write_text(self.html)
            manifest=create_manifest(data, html_file, network=False)
            self.assertTrue(manifest["ready_for_delivery"])
            email=EmailMessage()
            email["Subject"]="[TEST] Newsletter"
            email.set_content("Text alternative")
            email.add_alternative(self.html, subtype="html")
            received=extract_html_from_mime(email.as_bytes())
            self.assertTrue(verify_sent_html(received, manifest)["matched"])
            self.assertFalse(verify_sent_html(received+"<!-- changed -->", manifest)["matched"])

    def test_sent_mime_missing_html_fails(self):
        email=EmailMessage()
        email.set_content("Only plain text")
        with self.assertRaises(ValueError):
            extract_html_from_mime(email.as_bytes())


if __name__ == "__main__":
    unittest.main()
