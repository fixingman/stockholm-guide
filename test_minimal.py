"""Regression checks for the separate minimal editorial experiment."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parent
class Audit(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[];self.images=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if tag=="a":self.links.append(d.get("href",""))
        if tag=="img":self.images.append(d.get("src",""))
class MinimalTests(unittest.TestCase):
    def test_every_event_is_rendered_and_linked(self):
        g=json.loads((ROOT/"guide_data.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"rendered.html"
            subprocess.run([sys.executable,str(ROOT/"render_minimal.py"),"--output",str(path)],check=True,capture_output=True)
            html=path.read_text(encoding="utf-8");a=Audit();a.feed(html)
            expected=sum(len(g[k]) for k in ("top3","new_discoveries","worth_reconsidering","unavailable"))
            self.assertEqual(expected,33)
            self.assertEqual(len(a.links),expected)
            self.assertEqual(len(a.images),1)
            self.assertIn("milestone_skyline.png",a.images[0])
            self.assertEqual(html.count("class=\"event-name\""),expected)
            self.assertNotIn("→",html)
            for section in ("top3","new_discoveries","worth_reconsidering","unavailable"):
                for item in g[section]:
                    self.assertIn(item["url"].replace("&","&amp;"),html)
            self.assertLess(len(html.encode("utf-8")),100_000)
            self.assertIn("class=\"brand\"",html)
if __name__=="__main__":unittest.main()
