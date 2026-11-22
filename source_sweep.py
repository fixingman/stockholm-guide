#!/usr/bin/env python3
"""Public no-login discovery preflight for EVERY registered Stockholm source.

This is an index-page discovery PROBE, not a human/AI editorial verification.
It never marks any source as reviewed, verifies no event date or booking stock,
does not read subscriber data, and does not send email. A private/blocked source
remains blocked, not silently counted as scanned. The editorial source-coverage
audit is a separate mandatory Sunday release gate (from Issue 006).
"""
import argparse
import hashlib
import json
import re
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

USER_AGENT = "StockholmGuideDiscovery/1.0 (+public event discovery; no login)"
LINK_PATTERN = re.compile(
    r"event|events|kalender|calendar|whats.on|what.s.on|program|"
    r"konsert|utstall|exhibit|performance|show|ticket|biljett|"
    r"workshop|ritkurs|croquis|session|samtal|talk|festival|"
    r"\b2026\b|\b2027\b|november|december|dec\b|nov\b", re.I
)
SKIP_PATH = re.compile(
    r"login|signin|signup|register|account|privacy|cookie|"
    r"gdpr|contact|about|support|terms|mailto:", re.I
)
MAX_READ = 600_000
MAX_CANDIDATES = 18
MAX_URLS_PER_SOURCE = 5


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None
        self.title_parts = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a":
            self.current = [a.get("href", ""), []]
        if tag == "title":
            self.in_title = True
        if tag == "meta" and a.get("property") == "og:title" and a.get("content"):
            self.title_parts.append(a["content"])

    def handle_data(self, data):
        if self.current is not None:
            self.current[1].append(data)
        if self.in_title:
            self.title_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append((self.current[0], " ".join(self.current[1]).strip()))
            self.current = None
        if tag == "title":
            self.in_title = False


def safe_https(url):
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def fetch(url, timeout=12):
    """Bounded anonymous HTTP fetch. HTTP success only means reachable, NOT reviewed."""
    started = time.monotonic()
    req = Request(url, headers={
        "User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.7"
    })
    try:
        with urlopen(req, timeout=timeout, context=ssl.create_default_context()) as response:
            final = response.geturl()
            if not safe_https(final):
                return {"url": url, "status": "blocked", "error": "Redirected outside HTTPS", "seconds": round(time.monotonic()-started, 2)}
            code = response.status
            body = response.read(MAX_READ + 1)
            typ = response.headers.get("Content-Type", "")
            if len(body) > MAX_READ:
                body = body[:MAX_READ]
            if "text/html" not in typ and "application/xhtml" not in typ:
                return {"url": url, "final_url": final, "http_code": code, "status": "non_html", "error": typ[:120], "seconds": round(time.monotonic()-started, 2)}
            charset = response.headers.get_content_charset() or "utf-8"
            try:
                html = body.decode(charset, errors="replace")
            except LookupError:
                html = body.decode("utf-8", errors="replace")
            parser = LinkExtractor()
            parser.feed(html)
            return {"url": url, "final_url": final, "http_code": code,
                    "status": "reachable", "page_title": " ".join(parser.title_parts).strip()[:160],
                    "html_bytes_seen": len(body), "links": parser.links,
                    "seconds": round(time.monotonic()-started, 2)}
    except HTTPError as exc:
        return {"url": url, "http_code": exc.code, "status": "blocked" if exc.code in (401,403,429) else "http_error",
                "error": f"HTTP {exc.code}", "seconds": round(time.monotonic()-started, 2)}
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return {"url": url, "status": "connection_error", "error": str(exc)[:170],
                "seconds": round(time.monotonic()-started, 2)}


def discover_links(base, links):
    found = {}
    for href, label in links:
        try:
            link = urljoin(base, href)
        except ValueError:
            continue
        if not safe_https(link):
            continue
        parsed = urlparse(link)
        cleaned = parsed._replace(fragment="").geturl()
        text = re.sub(r"\s+", " ", label).strip()[:140]
        if not LINK_PATTERN.search(text + " " + parsed.path):
            continue
        if SKIP_PATH.search(parsed.path):
            continue
        if cleaned not in found:
            found[cleaned] = {"url": cleaned, "label": text, "unverified": True}
    # Identified opportunities are only research leads: never assert date,
    # ticket availability or event location from an index-page link.
    return list(found.values())[:MAX_CANDIDATES]


def inspect(source, timeout=12, retries=2):
    urls = [source["official_calendar_url"]] + source.get("additional_discovery_urls", [])
    urls = list(dict.fromkeys(x for x in urls if safe_https(x)))[:MAX_URLS_PER_SOURCE]
    attempts = []
    candidates = {}
    page_titles = []
    for url in urls:
        outcome = None
        for attempt in range(retries):
            result = fetch(url, timeout=timeout)
            attempts.append({k: v for k, v in result.items() if k != "links"} | {"attempt": attempt + 1})
            outcome = result
            if result["status"] in ("reachable", "non_html"):
                break
            if attempt + 1 < retries:
                time.sleep(0.5 + attempt)
        if outcome and outcome["status"] == "reachable":
            page_titles.append(outcome.get("page_title",""))
            for lead in discover_links(outcome.get("final_url", url), outcome.get("links", [])):
                candidates.setdefault(lead["url"], lead)
    reachable = sum(a["status"] == "reachable" for a in attempts)
    return {
        "source_id": source["id"],
        "source_name": source["name"],
        "source_type": source.get("source_type", "organizer"),
        "discovery_priority": source.get("discovery_priority"),
        "attempted_urls": urls,
        "attempts": attempts,
        "probe_status": "index_reachable" if reachable else "index_unavailable",
        "page_titles": page_titles,
        "candidate_links": list(candidates.values())[:MAX_CANDIDATES],
        "editorial_review_status": "NOT_REVIEWED", 
        "note": "Index reachability and links are NOT a reviewed event search; editor must inspect actual dated original event pages.",
    }


def sweep(registry, max_workers=7, timeout=12, retries=2, now=None):
    sources = registry["sources"]
    if len(sources) != len({s["id"] for s in sources}):
        raise ValueError("Duplicate source IDs in registry")
    for source in sources:
        if not safe_https(source["official_calendar_url"]):
            raise ValueError("Invalid HTTPS source: " + source["id"])
    scanned = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(inspect, s, timeout, retries): s for s in sources}
        for future in as_completed(futures):
            source = futures[future]
            try:
                scanned[source["id"]] = future.result()
            except Exception as exc:
                # A crash is an explicit failed attempt, never a false 'checked'.
                scanned[source["id"]] = {
                    "source_id": source["id"], "source_name": source["name"],
                    "probe_status": "probe_error", "error": str(exc)[:180],
                    "attempted_urls": [source["official_calendar_url"]],
                    "attempts": [], "candidate_links": [],
                    "editorial_review_status": "NOT_REVIEWED",
                }
    items = [scanned[s["id"]] for s in sources]
    count = sum(x["probe_status"] == "index_reachable" for x in items)
    blob = json.dumps(registry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {
        "schema_version": 1,
        "created_at": (now or datetime.now(timezone.utc)).isoformat(),
        "registry_sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "registered_count": len(sources),
        "attempted_count": len(items),
        "index_reachable_count": count,
        "index_unavailable_count": len(items) - count,
        "editorially_reviewed_count": 0,
        "total_discovered_links": sum(len(x.get("candidate_links", [])) for x in items),
        "sources": items,
        "limitations": [
            "HTML fetch without accounts: JavaScript-rendered lists may need a browser.",
            "HTTP 200 and discovered links do not count as an editorial review.",
            "No individual candidate dates, city, prices, stock or images verified.",
            "Blocked or unreachable URLs are explicitly recorded and need manual/alternate public review."
        ]
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", default="discovery_sources.json")
    p.add_argument("--output", default="research/source-probe.json")
    p.add_argument("--timeout", type=int, default=12)
    p.add_argument("--workers", type=int, default=7)
    p.add_argument("--retries", type=int, default=2)
    args = p.parse_args()
    result = sweep(json.loads(Path(args.registry).read_text(encoding="utf-8")),
                   max_workers=args.workers, timeout=args.timeout, retries=args.retries)
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "registry_count": result["registered_count"],
        "attempted_count": result["attempted_count"],
        "reachable": result["index_reachable_count"],
        "unavailable": result["index_unavailable_count"],
        "candidate_links": result["total_discovered_links"],
        "editorially_reviewed": 0,
        "output": str(dest)
    }))
    if result["attempted_count"] != result["registered_count"]:
        raise RuntimeError("Source probe missed registered sources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
