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
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    html = (base / 'preview.html').read_text()
    assert len(html.encode()) < 100_000, 'Email approaches Gmail clipping threshold'
    data = json.loads((base / 'guide_data.json').read_text())
    reports = []
    async with async_playwright() as p:
        options = {'headless': True}
        if os.environ.get('CHROME_PATH'):
            options['executable_path'] = os.environ['CHROME_PATH']
        browser = await p.chromium.launch(**options)
        for name, width, inline_only in [('desktop', 1100, False), ('mobile', 390, False),
                                         ('mobile-small', 320, False), ('inline-only', 390, True), ('inline-small', 320, True)]:
            page = await browser.new_page(viewport={'width': width, 'height': 900})
            # Preview loads the actual local files published as email assets.
            # No request interception substitutes photos or hides production URL failures.
            await page.route('https://**/*', lambda route: route.abort())
            await page.goto((base / 'preview.html').as_uri())
            if inline_only:
                await page.locator('style').evaluate_all('(els) => els.forEach(e => e.remove())')
            await page.evaluate('document.fonts.ready')
            await page.screenshot(path=str(output / f'{name}.png'), full_page=True)
            await page.screenshot(path=str(output / f'{name}-top.png'))
            if name in ('desktop', 'mobile'):
                await page.locator('h2').nth(1).locator('..').screenshot(path=str(output / f'{name}-discoveries.png'))
                await page.locator('.sky').screenshot(path=str(output / f'{name}-footer.png'))
            result = await page.evaluate('''() => ({
                brandTextRight: (()=>{let r=document.createRange();r.selectNodeContents(document.querySelector('.brand'));return r.getBoundingClientRect().right})(),
                brandCellRight: document.querySelector('.brand-cell').getBoundingClientRect().right,
                viewport: innerWidth, scrollWidth: document.documentElement.scrollWidth,
                images: [...document.images].map(x => ({src:x.getAttribute('src'),ok:x.complete && x.naturalWidth > 0})),
                headings: [...document.querySelectorAll('h2')].map(x=>x.textContent.trim()),
                text: document.body.innerText,
                links: [...document.querySelectorAll('a')].map(x=>x.getAttribute('href')),
                overflow: [...document.querySelectorAll('*')].filter(e=>e.getBoundingClientRect().right>innerWidth+1)
                    .map(e=>({tag:e.tagName,cls:e.className,right:Math.round(e.getBoundingClientRect().right)}))
            })''')
            assert result['brandTextRight'] <= result['brandCellRight'] + 1, (name, 'brand crosses column', result)
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
