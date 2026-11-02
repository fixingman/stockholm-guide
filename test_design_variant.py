"""Visual variant and content invariants. Runs without a browser or email sender."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
BASE=Path(__file__).resolve().parent
class VariantTests(unittest.TestCase):
    def test_statement_masthead_and_color_photo_geometry(self):
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/"preview.html"
            subprocess.run([sys.executable,str(BASE/"render.py"),"--output",str(out)],check=True,capture_output=True,text=True)
            html=out.read_text(encoding="utf-8")
            self.assertIn("The Stockholm<br>Guide",html)
            self.assertIn("A CURATED GUIDE TO CULTURE,",html)
            self.assertIn('height="120"',html)
            self.assertIn('height="76"',html)
            self.assertIn(".support-photo{height:105px!important}",html)
            self.assertIn(".thumb{width:76px!important;height:70px!important}",html)
            self.assertIn('milestone_brush.jpg',html)
            self.assertIn('milestone_torn.png',html)
            self.assertNotIn("mix-blend-mode:luminosity",html)
            self.assertNotIn("background-blend-mode:normal,luminosity",html)
            self.assertEqual(html.count('class="support-photo event-photo"'),2)
            self.assertEqual(html.count('class="thumb event-photo"'),7)
if __name__ == "__main__":unittest.main()
