#!/usr/bin/env python3
"""Optional read-only Chromium supplement for JS-heavy Stockholm sources.

Reads the COMPLETE no-login HTTP probe and attempts browser DOM extraction for
aggregators, Luma, inaccessible and low-yield pages. Never logs in, books,
registers, verifies ticket stock or claims editorial review. Browser failures
are reported honestly and do not erase successful HTTP findings.
"""
import argparse
import asyncio
import json
from pathlib import Path

from source_sweep import discover_links, safe_https

MAX_LINKS = 18


async def enrich(report, concurrency=4, timeout=11000):
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        raise RuntimeError("Install Playwright Chromium to run browser sweep") from exc
    sem = asyncio.Semaphore(concurrency)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            async def check(item):
                is_aggregator = item.get("source_type") == "aggregator"
                needs_browser = (
                    is_aggregator
                    or item.get("source_id") == "luma-stockholm"
                    or item.get("probe_status") != "index_reachable"
                    or len(item.get("candidate_links", [])) < 4
                )
                if not needs_browser:
                    item["browser_status"] = "not_needed_html_leads_available"
                    return
                attempts = []
                leads = {}
                # Browser cannot read private pages; never click RSVP buttons
                # or pursue credential gated routes.
                for url in item.get("attempted_urls", [])[:4]:
                    if not safe_https(url):
                        continue
                    async with sem:
                        page = None
                        try:
                            page = await browser.new_page(viewport={"width":1200,"height":850})
                            response = await page.goto(url,wait_until="domcontentloaded",timeout=timeout)
                            await page.wait_for_timeout(650)
                            fetched = await page.locator("a[href]").evaluate_all(
                                "(nodes) => nodes.slice(0,900).map(n => [n.href, (n.innerText||n.getAttribute('aria-label')||'').trim().slice(0,140)])"
                            )
                            status = response.status if response else None
                            links = discover_links(page.url, fetched)
                            for lead in links:
                                leads.setdefault(lead["url"],lead)
                            attempts.append({"url": url, "final_url":page.url,
                                             "http_code":status, "status":"dom_read",
                                             "all_visible_anchor_count":len(fetched),
                                             "event_candidate_count":len(links)})
                        except Exception as exc:
                            attempts.append({"url":url,"status":"browser_error","error":str(exc)[:180]})
                        finally:
                            if page is not None:
                                await page.close()
                item["browser_attempts"] = attempts
                item["browser_status"] = ("dom_read" if any(x["status"]=="dom_read" for x in attempts)
                    else "unavailable")
                item["browser_candidate_links"] = list(leads.values())[:MAX_LINKS]
                # Keep unique leads from either channel. A browser success is
                # NOT a human or AI editorial review of live event details.
                merged = {}
                for x in list(leads.values()) + item.get("candidate_links", []):
                    merged.setdefault(x["url"],x)
                item["candidate_links"] = list(merged.values())[:MAX_LINKS]
                item["editorial_review_status"] = "NOT_REVIEWED"
            await asyncio.gather(*(check(item) for item in report["sources"]))
        finally:
            await browser.close()
    report["total_discovered_links"] = sum(len(s.get("candidate_links",[])) for s in report["sources"])
    report["browser_enriched_count"] = sum(s.get("browser_status")=="dom_read" for s in report["sources"])
    report["browser_unavailable_count"] = sum(s.get("browser_status")=="unavailable" for s in report["sources"])
    report.setdefault("limitations",[]).append(
        "Chromium loaded public DOM for low-yield/JS sources only. Event identity and dates still require original-page editorial checks."
    )
    return report


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--probe",default="research/source-probe.json")
    a.add_argument("--output",default=None)
    args=a.parse_args()
    input_path=Path(args.probe)
    report=json.loads(input_path.read_text(encoding="utf-8"))
    report=asyncio.run(enrich(report))
    output=Path(args.output or args.probe)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "sources_attempted":report["attempted_count"],
        "browser_dom_loaded_sources":report["browser_enriched_count"],
        "browser_unavailable_sources":report["browser_unavailable_count"],
        "total_unverified_leads":report["total_discovered_links"],
        "editorial_review_count":report["editorially_reviewed_count"]
    }))


if __name__=="__main__":
    main()
