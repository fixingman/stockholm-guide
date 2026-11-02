"""Content safety and image provenance regressions. No email is sent."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent

class RenderTests(unittest.TestCase):
    def render(self, data):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'data.json'
            output = Path(folder) / 'email.html'
            source.write_text(json.dumps(data))
            result = subprocess.run([sys.executable, str(BASE / 'render.py'), '--data', str(source),
                                     '--output', str(output)], capture_output=True, text=True)
            return result, output.read_text() if output.exists() else ''

    def test_event_text_is_escaped_in_jinja_suffix_template(self):
        data = json.loads((BASE / 'guide_data.json').read_text())
        data['top3'][1]['title'] = '<script>alert("unsafe")</script> & title'
        result, html = self.render(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertIn('&amp; title', html)

    def test_unverified_photo_cannot_render(self):
        data = json.loads((BASE / 'guide_data.json').read_text())
        data['top3'][0]['image_verified'] = False
        result, html = self.render(data)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(html, '')

if __name__ == '__main__':
    unittest.main()
