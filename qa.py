"""Browser smoke tests, including an inline-only email fallback (not a Gmail emulator)."""
import argparse
import asyncio
import json
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default='qa-output')
    parser.add_argument('--html', type=Path)
    parser.add_argument('--data', type=Path)
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    preview_path = (args.html or base / 'preview.html').resolve()
    html = preview_path.read_text()
    assert len(html.encode()) < 100_000, 'Email approaches Gmail clipping threshold'
    data = json.loads((args.data or base / 'guide_data.json').read_text())
    reports = []
    async with async_playwright() as p:
        options = {'headless': True}
        if os.environ.get('CHROME_PATH'):
            options['executable_path'] = os.environ['CHROME_PATH']
        browser = await p.chromium.launch(**options)
        context = await browser.new_context()
        for name, width, inline_only in [('desktop', 1100, False), ('mobile', 390, False),
                                         ('mobile-small', 320, False), ('inline-only', 390, True), ('inline-small', 320, True)]:
            page = await context.new_page()
            await page.set_viewport_size({'width': width, 'height': 900})
            # Load actual local branding and official event URLs; no request substitution.
            await page.goto(preview_path.as_uri(), timeout=60000)
            if inline_only:
                await page.locator('style').evaluate_all('(els) => els.forEach(e => e.remove())')
            await page.evaluate('document.fonts.ready')
            await page.screenshot(path=str(output / f'{name}.png'), full_page=True)
            await page.screenshot(path=str(output / f'{name}-top.png'))
            await page.locator('.shell').screenshot(path=str(output / f'{name}-guide.png'))
            if name in ('desktop', 'mobile'):
                await page.locator('.discovery-list').locator('..').screenshot(path=str(output / f'{name}-discoveries.png'))
                await page.locator('.sky').screenshot(path=str(output / f'{name}-footer.png'))
            result = await page.evaluate('''() => ({
                brandTextRight: (()=>{let r=document.createRange();r.selectNodeContents(document.querySelector('.brand'));return r.getBoundingClientRect().right})(),
                mastheadRight: document.querySelector('.masthead').getBoundingClientRect().right,
                viewport: innerWidth, scrollWidth: document.documentElement.scrollWidth,
                images: [...document.images].map(x => ({src:x.getAttribute('src'),ok:x.complete && x.naturalWidth > 0})),
                headings: [...document.querySelectorAll('h2')].map(x=>x.textContent.trim()),
                text: document.body.innerText,
                links: [...document.querySelectorAll('a')].map(x=>x.getAttribute('href')),
                overflow: [...document.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>innerWidth+1)
                    .map(e=>({tag:e.tagName,cls:e.className,right:Math.round(e.getBoundingClientRect().right)}))
            })''')
            assert result['brandTextRight'] <= result['mastheadRight'] + 1, (name, 'brand crosses masthead', result['brandTextRight'], result['mastheadRight'])
            columns = await page.evaluate('''() => {
                const rect = s => {let r=document.querySelector(s).getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom}};
                return {main:rect('.discovery-main'),date:rect('.discovery-date'),venue:rect('.discovery-venue'),
                    title:rect('.reconsider-title'),copy:rect('.reconsider-main'),
                    heroCells:document.querySelector('.hero-card').rows[0].cells.length,
                    reconsiderImages:document.querySelector('.reconsider-list').querySelectorAll('img:not([alt=""])').length};
            }''')
            assert columns['heroCells'] == 1, 'Hero must be one integrated background cell'
            assert columns['reconsiderImages'] == 0, 'Reconsiderations must not have event photos'
            if width > 600 and not inline_only:
                assert columns['date']['x'] >= columns['main']['right'] - 1, (name, columns)
                assert columns['venue']['x'] >= columns['date']['right'] - 1, (name, columns)
                assert columns['copy']['x'] >= columns['title']['right'] - 1, (name, columns)
            else:
                assert columns['date']['y'] >= columns['main']['bottom'] - 1, (name, columns)
            backgrounds = await page.evaluate('''async () => {
                const urls = [...new Set([...document.querySelectorAll('[background]')].map(e=>e.getAttribute('background')))];
                return await Promise.all(urls.map(src=>new Promise(resolve=>{let i=new Image(); i.onload=()=>resolve({src,ok:true});i.onerror=()=>resolve({src,ok:false});i.src=src})))
            }''')
            assert all(x['ok'] for x in backgrounds), (name, backgrounds)
            result['columns'] = columns
            result['backgrounds'] = backgrounds
            assert result['scrollWidth'] <= width, (name, result['overflow'])
            assert all(x['ok'] for x in result['images']), (name, result['images'])
            assert len(result['headings']) == 4
            assert len(result['links']) == sum(len(data[k]) for k in ('top3', 'new_discoveries', 'worth_reconsidering', 'unavailable'))
            for section in ('top3', 'new_discoveries', 'worth_reconsidering', 'unavailable'):
                for item in data[section]:
                    assert item['title'] in result['text'], (name, item['title'])
                    assert item['url'] in result['links']
                    for key in ('dates', 'price', 'booking'):
                        assert item[key] in result['text'], (name, item[key])
            result.pop('text')
            result['name'] = name
            reports.append(result)
            print(name, 'PASS', 'width', width, 'images', len(result['images']), 'links', len(result['links']))
            await page.close()
        await browser.close()
    (output / 'report.json').write_text(json.dumps(reports, indent=2))

asyncio.run(main())
