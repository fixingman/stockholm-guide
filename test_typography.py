"""Checks that rendered email uses the shared typography/spacing tokens."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parent

class TypographyTests(unittest.TestCase):
    def test_token_values_render_as_inline_email_css(self):
        tokens = json.loads((BASE / "design_tokens.json").read_text())
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "test.html"
            subprocess.run([sys.executable, str(BASE / "render.py"), "--output", str(out)], check=True, capture_output=True, text=True)
            html = out.read_text()
            self.assertIn(f"font:bold {tokens['hero_title']} Georgia", html)
            self.assertIn(f"font:{tokens['hero_body']} Arial", html)
            self.assertIn(f"font:bold {tokens['event_title']} Georgia", html)
            self.assertIn(f"font:{tokens['event_body']} Arial", html)
            self.assertIn(f"font:{tokens['event_metadata']} Arial", html)
            self.assertIn(f"margin-bottom:{tokens['heading_bottom']}", html)
            self.assertIn(f"padding:{tokens['section_gap']} 25px", html)
            self.assertNotIn("{{ tokens.", html)

if __name__ == "__main__":
    unittest.main()
