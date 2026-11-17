"""Offline regression checks for same-host optimized email photo variants."""
import io
import unittest
from PIL import Image
import optimize_issue_images as p


def photo(size=(4000, 2727), color=(120, 110, 100), quality=90):
    image = Image.new("RGB", size, color)
    out = io.BytesIO()
    image.save(out, format="JPEG", quality=quality)
    blob = out.getvalue()
    return blob, Image.open(io.BytesIO(blob)), "https://example.com/photo.jpg", size


class ImageOptimizationTests(unittest.TestCase):
    def test_wordpress_variants_remain_on_original_host(self):
        url = "https://example.com/wp-content/uploads/2024/03/image.jpg"
        found = p.candidate_urls(url, (4000, 2727))
        self.assertTrue(found)
        self.assertTrue(all(v.startswith("https://example.com/wp-content/uploads/") for v in found))
        self.assertIn("-1024x698.jpg", found[0])

    def test_sanity_and_next_resize_preserve_origin(self):
        sanity = p.candidate_urls("https://cdn.sanity.io/images/abc/production/pic.jpg?rect=0%2C0%2C500%2C500&w=4000", (4000, 4000))
        self.assertIn("w=960", sanity[0])
        self.assertIn("rect=", sanity[0])
        self.assertIn("fm=jpg", sanity[0])
        next_image = p.candidate_urls("https://fylkingen.se/_next/image?url=%2Fphoto.jpg&w=3840&q=75", (4000, 2727))
        self.assertIn("w=1080", next_image[0])

    def test_reject_mismatched_photo_even_if_smaller(self):
        source = photo(color=(120, 110, 100))
        variant = photo(size=(1024, 698), color=(240, 15, 10))
        def checker(url):
            blob, im, _, dims = variant if "-1024x" in url else source
            return blob, im, url, dims
        entry = {"title": "Event", "image_verified": True,
                 "image_url": "https://example.com/wp-content/uploads/2024/03/image.jpg"}
        result = p.optimize_entry(entry, checker)
        self.assertEqual(result["status"], "unchanged")
        self.assertNotIn("image_original_url", entry)

    def test_use_verified_smaller_original_host_photo(self):
        source = photo()
        variant = photo(size=(1024, 698), quality=72)
        def checker(url):
            blob, im, _, dims = variant if "-1024x" in url else source
            return blob, im, url, dims
        entry = {"title": "Event", "image_verified": True,
                 "image_url": "https://example.com/wp-content/uploads/2024/03/image.jpg",
                 "image_source_url": "https://example.com/events/example",
                 "image_identity_review": {"event_match": True}}
        result = p.optimize_entry(entry, checker)
        self.assertEqual(result["status"], "optimized")
        self.assertEqual(entry["image_original_url"], "https://example.com/wp-content/uploads/2024/03/image.jpg")
        self.assertIn("-1024x698.jpg", entry["image_url"])
        self.assertTrue(entry["image_optimization"]["optimized_bytes"] < entry["image_optimization"]["source_bytes"])
        self.assertTrue(entry["image_identity_review"]["event_match"])
        self.assertEqual(p.optimize_entry(entry, checker)["status"], "skipped")

    def test_unverified_approved_cached_and_no_variant_are_unchanged(self):
        self.assertEqual(p.optimize_entry({"image_verified": False})["status"], "skipped")
        self.assertEqual(p.optimize_entry({"image_verified": True, "image_url": "https://example.com/a.jpg", "image_cache_file": "a.jpg"})["status"], "skipped")
        source = photo()
        def checker(url):
            blob, im, _, dims = source
            return blob, im, url, dims
        entry = {"image_verified": True, "image_url": "https://example.com/photo.jpg"}
        self.assertEqual(p.optimize_entry(entry, checker)["status"], "unchanged")


if __name__ == "__main__":
    unittest.main()
