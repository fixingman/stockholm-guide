#!/usr/bin/env python3
"""Populate fixed Stockholm Guide milestone template without altering typography or layout.
Usage: python render.py --data guide_data.json --output preview.html
Email sends: host assets at public HTTPS URLs and pass --asset-base-url https://.../assets.
"""
import argparse,json
from pathlib import Path
from urllib.parse import urlparse
from jinja2 import Environment,FileSystemLoader,select_autoescape
base=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--data',default=str(base/'guide_data.json'));p.add_argument('--output',default=str(base/'preview.html'));p.add_argument('--asset-base-url',default='assets');a=p.parse_args()
g=json.loads(Path(a.data).read_text())
assert len(g['top3'])==3
assert g.get('hero_pick_index',0) in (0,1,2)
for key in ('top3','new_discoveries','worth_reconsidering','unavailable'):
 assert g[key],key
 for idx,x in enumerate(g[key]):
  required=('title','dates','url','price','booking') if key=='unavailable' else ('title','dates','url','description','price','booking')
  assert all(x.get(k) for k in required),f'{key}[{idx}] missing metadata'
  assert urlparse(x['url']).scheme=='https'
  # An event photograph may be used ONLY when its official provenance was checked.
  has_image=bool(x.get('image_url'))
  fields=('image_source_url','image_verified','image_alt')
  if has_image:
   assert x.get('image_verified') is True, f'{key}[{idx}] image must be verified'
   assert all(x.get(k) for k in fields), f'{key}[{idx}] image provenance missing'
   assert urlparse(x['image_url']).scheme=='https', f'{key}[{idx}] image URL must use HTTPS'
   assert urlparse(x['image_source_url']).scheme=='https', f'{key}[{idx}] image source must use HTTPS'
   assert urlparse(x['image_url']).netloc and urlparse(x['image_source_url']).netloc
   assert len(x['image_alt'])>8, f'{key}[{idx}] image alt text too vague'
  else:
   # Unverified images never render, even if an obsolete thumbnail field exists.
   x.pop('image_url',None)
asset=a.asset_base_url.rstrip('/')
assets={'stroke':f'{asset}/milestone_heading_stroke.png','brush':f'{asset}/milestone_brush.jpg','torn':f'{asset}/milestone_torn.png','hero':f'{asset}/event-placeholder.jpg','secondary1':f'{asset}/event-placeholder.jpg','secondary2':f'{asset}/event-placeholder.jpg','placeholder_thumb':f'{asset}/event-placeholder-thumb.jpg','skyline':f'{asset}/milestone_skyline.png'}
env=Environment(loader=FileSystemLoader(base),autoescape=select_autoescape(['html','xml']))
html=env.get_template('template.html.j2').render(guide=g,assets=assets)
Path(a.output).write_text(html,encoding='utf-8')
lines=[f"The Stockholm Guide · Issue #{g['issue_number']} · {g['date_range']}",g['intro']]
for key,title in [('top3','TOP 3 PICKS'),('new_discoveries','NEW DISCOVERIES'),('worth_reconsidering','WORTH RECONSIDERING'),('unavailable','UNAVAILABLE / SOLD OUT')]:
 lines+=['',title]
 for x in g[key]:
  lines+=['',x.get('day',''),x['title'],x['dates'],x.get('description',''),x['price'],'Booking: '+x['booking'],x['url']]
lines+=['',g['disclaimer']]
Path(a.output).with_suffix('.txt').write_text('\n'.join(lines))
print({k:len(g[k]) for k in ('top3','new_discoveries','worth_reconsidering','unavailable')})
print(a.output)
