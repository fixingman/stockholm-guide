#!/usr/bin/env python3
"""Browser-based email resilience QA: desktop/mobile, dark mode, blocked images.

Chromium is a PROXY for browser behavior, NOT a Gmail/Apple Mail renderer.
No emails are sent. Screenshots are saved only as GitHub CI artifacts.
"""
import argparse
import json
from pathlib import Path

from delivery_guard import EmailStructure


def inspect_static(html):
    parser=EmailStructure()
    parser.feed(html)
    errors=[]
    if "<h1 " not in html or html.count("<h2 ")!=4:
        errors.append("Missing one H1 and four H2 section headings")
    if "prefers-color-scheme: dark" not in html:
        errors.append("No progressive dark-mode styles")
    if 'name="viewport"' not in html:
        errors.append("Missing mobile viewport")
    if 'class="event-card-link"' not in html:
        errors.append("Missing clickable event links")
    if not parser.images or any(not i["alt"].strip() for i in parser.images):
        errors.append("Image elements must have meaningful nonempty alt text")
    if "display:none" not in html or "max-height:0" not in html:
        errors.append("Hidden inbox preheader absent")
    if not parser.sections or len(parser.sections)!=4:
        errors.append("Four readable section headings missing")
    return {"ok":not errors,"errors":errors,"headings":parser.sections,"image_count":len(parser.images)}


def check_browser(html_file, output):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RuntimeError("Install playwright and chromium for browser QA") from e
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for width in (320,390,650):
            for scheme in ("light","dark"):
                context=browser.new_context(viewport={"width":width,"height":900},
                                             color_scheme=scheme,device_scale_factor=1)
                page=context.new_page()
                # Abort remote requests: prove legibility when image hosts are blocked.
                page.route("**/*",lambda route: route.abort() if route.request.resource_type=="image" else route.continue_())
                page.goto(html_file.resolve().as_uri(),wait_until="domcontentloaded")
                page.screenshot(path=str(output/f"email-{width}-{scheme}-images-blocked.png"),full_page=True)
                measured=page.evaluate("""() => ({
                  docWidth: document.documentElement.scrollWidth,
                  viewport: window.innerWidth,
                  heading1: document.querySelectorAll('h1').length,
                  heading2: document.querySelectorAll('h2').length,
                  visibleEventLinks: [...document.querySelectorAll('a.event-card-link')].every(a => a.getBoundingClientRect().width > 0),
                  imgCount: document.querySelectorAll('img').length,
                  bg: getComputedStyle(document.querySelector('.shell')).backgroundColor
                })""")
                ok=(measured["docWidth"]<=width+2 and measured["heading1"]==1
                    and measured["heading2"]==4 and measured["visibleEventLinks"])
                results.append({"width":width,"scheme":scheme,"ok":ok,**measured})
                context.close()
        browser.close()
    return results


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--html",required=True)
    ap.add_argument("--report",default="email-client-qa.json")
    ap.add_argument("--screenshots",default="email-client-screenshots")
    ap.add_argument("--browser",action="store_true")
    args=ap.parse_args()
    path=Path(args.html)
    static=inspect_static(path.read_text())
    screens=[]
    if args.browser:
        output=Path(args.screenshots);output.mkdir(parents=True,exist_ok=True)
        screens=check_browser(path,output)
    result={"static":static,"browser_scenarios":screens,
            "ok":static["ok"] and all(r["ok"] for r in screens),
            "scope":"Chromium responsive/dark/images-blocked proxy; not actual Gmail or Apple Mail"}
    Path(args.report).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
    return 0 if result["ok"] else 1


if __name__=="__main__":
    raise SystemExit(main())
