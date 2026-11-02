from pathlib import Path
import asyncio
from playwright.async_api import async_playwright
async def main():
 base=Path(__file__).parent
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name,width in [('desktop',1100),('mobile',390)]:
   page=await browser.new_page(viewport={'width':width,'height':860},device_scale_factor=1)
   from base64 import b64encode
   html=(base/'preview.html').read_text()
   for f in (base/'assets').iterdir():
    if not (f.name.startswith('milestone_') or f.name.startswith('event-placeholder')):continue
    mime='image/png' if f.suffix.lower()=='.png' else 'image/jpeg'
    b64=b64encode(f.read_bytes()).decode()
    html=html.replace('assets/'+f.name, 'data:'+mime+';base64,'+b64)
   await page.set_content(html,wait_until='load')
   await page.screenshot(path=str(base/f'{name}.png'),full_page=True)
   await page.screenshot(path=str(base/f'{name}-top.png'),full_page=False)
   r=await page.evaluate('''()=>({viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,imgs:[...document.images].map(x=>({src:x.getAttribute('src'),ok:x.complete&&x.naturalWidth>0})),headers:[...document.querySelectorAll('h2')].map(x=>x.textContent.trim()),links:[...document.querySelectorAll('a')].length,overflow:[...document.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,8).map(e=>({tag:e.tagName,cls:e.className,right:Math.round(e.getBoundingClientRect().right)}))})''')
   print(name,{k:v for k,v in r.items() if k!='imgs'},'images_ok',all(x['ok'] for x in r['imgs']),'image_count',len(r['imgs']))
   await page.close()
  await browser.close()
asyncio.run(main())
