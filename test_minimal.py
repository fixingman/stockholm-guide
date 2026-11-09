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
            self.assertEqual(len(a.links),expected+6)  # Event row links, 3 thumbnail links, and 3 feedback links
            self.assertEqual(len(a.images),1+sum(bool(item.get("image_verified") and item.get("image_url")) for item in g["top3"]))
            self.assertEqual(sum("milestone_skyline.png" in x for x in a.images),1)
            self.assertNotIn("event-placeholder-thumb.jpg",html)
            self.assertEqual(html.count('aria-label="No verified event photo available"'),sum(not (item.get("image_verified") and item.get("image_url")) for item in g["top3"]))
            self.assertEqual(html.count('class="top-thumb-link"'),3)
            self.assertEqual(html.count('class="event-card-link"'),expected-len(g["unavailable"]))
            self.assertIn("font-size:15px!important;line-height:21px!important",html)
            self.assertIn("font:bold 17px/24px",html)
            for item in g["top3"]:
                photo = item.get("image_cache_file") or item.get("image_url")
                if item.get("image_verified") and photo:
                    self.assertTrue(any(photo.replace("&", "&amp;") in x or photo in x for x in a.images), photo)
            self.assertNotIn("class=\"top-date",html)
            self.assertEqual(html.count("class=\"top-thumb\""),3)
            self.assertIn("milestone_skyline.png",a.images[-1])
            self.assertEqual(html.count("class=\"event-name\""),expected)
            self.assertNotIn("→",html)
            for section in ("top3","new_discoveries","worth_reconsidering","unavailable"):
                for item in g[section]:
                    self.assertIn(item["url"].replace("&","&amp;"),html)
            self.assertLess(len(html.encode("utf-8")),100_000)
            self.assertIn("class=\"brand\"",html)
            from urllib.parse import urlsplit, parse_qs
            from html import unescape
            class Feedback(HTMLParser):
                def __init__(self):
                    super().__init__();self.links=[]
                def handle_starttag(self,tag,attrs):
                    d=dict(attrs)
                    if tag=="a" and "feedback-link" in d.get("class","").split():
                        self.links.append(unescape(d["href"]))
            feedback=Feedback();feedback.feed(html)
            self.assertEqual(len(feedback.links),3)
            subjects=[]
            for index, link in enumerate(feedback.links):
                params=parse_qs(urlsplit(link).query)
                if index < 2:
                    self.assertEqual(urlsplit(link).netloc,"mail.google.com")
                    self.assertEqual(params.get("view"),["cm"])
                    self.assertEqual(params.get("fs"),["1"])
                    self.assertEqual(params.get("to"),["cankilicbay@gmail.com"])
                    self.assertIn("su",params)
                    subjects.append(params["su"][0])
                    self.assertIn("body",params)
                    self.assertIn("Stockholm Guide issue #",params["body"][0])
                else:
                    self.assertTrue(link.startswith("mailto:cankilicbay@gmail.com?"))
                    self.assertIn("subject",params)
                    self.assertIn("body",params)
                    subjects.append(params["subject"][0])
            self.assertIn(f"Stockholm Guide #{g['issue_number']} | LIKE",subjects)
            self.assertIn(f"Stockholm Guide #{g['issue_number']} | DISLIKE",subjects)
            self.assertIn("Stockholm Guide | UNSUBSCRIBE",subjects)
            self.assertNotIn("<script",html.lower())

            class UnavailableRows(HTMLParser):
                def __init__(self):
                    super().__init__();self.in_row=False;self.rows=[];self.current=""
                def handle_starttag(self,tag,attrs):
                    d=dict(attrs)
                    if tag=="td" and "unavailable-row" in d.get("class","").split():
                        self.in_row=True;self.current=""
                def handle_data(self,data):
                    if self.in_row:self.current+=data
                def handle_endtag(self,tag):
                    if tag=="td" and self.in_row:
                        self.rows.append(self.current);self.in_row=False
            rows=UnavailableRows();rows.feed(html)
            self.assertEqual(len(rows.rows),len(g["unavailable"]))
            self.assertEqual(html.count('class="unavailable-meta"'),len(g["unavailable"]))
            for row,item in zip(rows.rows,g["unavailable"]):
                self.assertIn(item["title"],row)
                self.assertIn(item["dates"],row)
                self.assertIn(item["booking"],row)
                self.assertNotIn(item["price"],row)

if __name__=="__main__":unittest.main()
