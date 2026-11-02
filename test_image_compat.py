"""Email image compatibility and preview fallback regression checks."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent

class ImageCompatTests(unittest.TestCase):
    def test_explicit_brush_and_hero_images_and_preview_only_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            preview = Path(folder) / 'preview.html'
            email = Path(folder) / 'email.html'
            for output in (preview, email):
                subprocess.run([sys.executable, str(BASE / 'render.py'), '--output', str(output)],
                               capture_output=True, text=True, check=True)
            p = preview.read_text()
            e = email.read_text()
            self.assertIn('class="masthead-brush"', e)
            self.assertIn('class="hero-photo event-photo"', e)
            self.assertIn('class="support-photo event-photo"', e)
            self.assertIn('class="thumb event-photo"', e)
            self.assertNotIn('class="masthead" background=', e)
            self.assertNotIn('class="hero-bg" background=', e)
            self.assertIn('img.event-photo', p)
            self.assertIn("img.addEventListener('error',useNeutral", p)
            self.assertNotIn('<script>', e)
            self.assertEqual(e.count('class="thumb event-photo"'), 7)
            self.assertEqual(e.count('class="support-photo event-photo"'), 2)
            self.assertEqual(e.count('class="hero-photo event-photo"'), 1)

if __name__ == '__main__':
    unittest.main()
