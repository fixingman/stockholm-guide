"""Offline regression tests for the image discovery/cache pipeline."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import image_pipeline as p


def jpeg():
    out = io.BytesIO()
    Image.new("RGB", (960, 540), "gray").save(out, format="JPEG")
    return out.getvalue()


class ImagePipelineTests(unittest.TestCase):
    def test_html_discovery_og_and_lazy(self):
        parser = p.PageImages()
        parser.feed('<meta property="og:image" content="/poster.jpg"><img data-src="/still.jpg" alt="event">'
                    '<script type="application/ld+json">{"image":"https://events.example/photo.jpg"}</script>')
        self.assertEqual(parser.candidates[0][0], "/poster.jpg")
        self.assertIn("https://events.example/photo.jpg", list(p.json_images(json.loads("".join(parser.jsonld[0:])))))

    def test_reject_invalid_or_insecure_urls(self):
        for url in ["http://example.com/a.jpg", "file:///etc/passwd", "https://user:pass@host/a"]:
            self.assertFalse(p.https(url))
        self.assertTrue(p.https("https://events.example/picture.jpg"))

    def test_approved_image_is_cached_to_stable_name(self):
        with tempfile.TemporaryDirectory() as d, patch.object(p, "ROOT", Path(d)):
            guide = {"issue_number":"900","top3":[{"title":"Exact concert","url":"https://events.example/2026",
                     "image_reuse_approved": True}]}
            source = Path(d)/"data.json"
            source.write_text(json.dumps(guide))
            picture = Image.open(io.BytesIO(jpeg()))
            with patch.object(p,"discover",return_value=[{"url":"https://events.example/image.jpg","description":"og:image","score":100}]), \
                 patch.object(p,"validate_photo",return_value=(jpeg(),picture,"https://events.example/image.jpg",(960,540))):
                report = p.run(source,Path(d)/"report.json",write=True)
            event=json.loads(source.read_text())["top3"][0]
            self.assertEqual(report["events"][0]["status"],"cached")
            self.assertTrue((Path(d)/"assets"/event["image_cache_file"]).is_file())
            self.assertTrue(event["image_url"].startswith("https://fixingman.github.io/"))
            self.assertEqual(event["image_source_url"],"https://events.example/2026")

    def test_unapproved_image_is_audited_but_not_copied(self):
        with tempfile.TemporaryDirectory() as d, patch.object(p,"ROOT",Path(d)):
            source=Path(d)/"data.json"
            source.write_text(json.dumps({"top3":[{"title":"Event","url":"https://events.example/2026"}]}))
            picture=Image.open(io.BytesIO(jpeg()))
            with patch.object(p,"discover",return_value=[{"url":"https://events.example/photo.jpg","description":"og:image","score":100}]), \
                 patch.object(p,"validate_photo",return_value=(jpeg(),picture,"https://events.example/photo.jpg",(960,540))):
                result=p.run(source,Path(d)/"report.json",write=True)
            self.assertEqual(result["events"][0]["status"],"needs_rights_review")
            self.assertFalse((Path(d)/"assets").exists())
            self.assertNotIn("image_verified",json.loads(source.read_text())["top3"][0])


if __name__=="__main__":
    unittest.main()
