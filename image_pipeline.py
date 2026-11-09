#!/usr/bin/env python3
"""Discover official event artwork, verify it and (only with reuse permission) cache it.

No image search guessing, and no automatic republication of copyrighted media.
Output: image-report.json; with --write, approved assets + updated event JSON.
"""
import argparse
import hashlib
import io
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parent
MAX_HTML = 2_000_000
MAX_IMAGE = 9_000_000
USER_AGENT = "StockholmGuide/1.0 (event editorial image verification)"
SKIP = re.compile(r"logo|favicon|sprite|icon|avatar|tracking|pixel|placeholder", re.I)


class PageImages(HTMLParser):
    def __init__(self):
        super().__init__()
        self.candidates = []
        self.in_jsonld = False
        self.jsonld = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self.in_jsonld = True
        if tag == "meta":
            key = (attrs.get("property") or attrs.get("name") or "").lower()
            if key in ("og:image", "og:image:url", "twitter:image", "twitter:image:src"):
                self.candidates.append((attrs.get("content", ""), key, 100))
        elif tag == "img":
            alt = attrs.get("alt", "")
            for key, bonus in (("data-src", 33), ("data-original", 32), ("src", 30), ("srcset", 25)):
                value = attrs.get(key)
                if value:
                    if key == "srcset":
                        value = value.split(",")[-1].strip().split(" ")[0]
                    self.candidates.append((value, alt, bonus))

    def handle_data(self, data):
        if self.in_jsonld:
            self.jsonld.append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self.in_jsonld = False


def https(url):
    u = urlparse(url)
    return u.scheme == "https" and bool(u.hostname) and not u.username and not u.password


def download(url, limit, types):
    if not https(url):
        raise ValueError("Non-HTTPS or malformed URL")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": ", ".join(types)})
    with urlopen(request, timeout=14) as response:
        if not https(response.url):
            raise ValueError("Insecure redirect")
        mime = response.headers.get_content_type()
        if not any(mime.startswith(t) for t in types):
            raise ValueError("Unexpected media type: " + mime)
        length = response.headers.get("Content-Length")
        if length and int(length) > limit:
            raise ValueError("Content-Length exceeds limit")
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Response exceeds limit")
        return data, response.url, mime


def json_images(value):
    if isinstance(value, list):
        for v in value:
            yield from json_images(v)
    elif isinstance(value, dict):
        if "image" in value:
            yield from json_images(value["image"])
        if value.get("url") and value.get("@type", "").lower().endswith(("imageobject", "photograph")):
            yield value["url"]
        for key in ("@graph", "mainEntity"):
            if key in value:
                yield from json_images(value[key])
    elif isinstance(value, str) and value.startswith("https://"):
        yield value


def discover(page_url):
    data, final_url, _ = download(page_url, MAX_HTML, ("text/html",))
    parser = PageImages()
    parser.feed(data.decode("utf-8", "replace"))
    for raw in parser.jsonld:
        try:
            for image_url in json_images(json.loads(raw)):
                parser.candidates.append((image_url, "schema.org image", 90))
        except (ValueError, TypeError):
            pass
    seen = set()
    candidates = []
    for link, desc, bonus in parser.candidates:
        url = urljoin(final_url, link)
        if not https(url) or SKIP.search(urlparse(url).path):
            continue
        if url in seen:
            continue
        seen.add(url)
        candidates.append({"url": url, "description": desc, "score": bonus})
    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates[:22]


def validate_photo(url):
    data, final_url, mime = download(url, MAX_IMAGE, ("image/",))
    if mime in ("image/svg+xml", "image/gif"):
        raise ValueError("SVG/GIF unsuitable for email thumbnail")
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError) as e:
        raise ValueError("Cannot decode image") from e
    w, h = image.size
    if w < 420 or h < 230 or w / h > 5 or h / w > 4:
        raise ValueError("Too small or unusual image dimensions")
    return data, image, final_url, (w, h)


def prepare(data, image):
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((1120, 880), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    image.save(out, "JPEG", quality=83, optimize=True, progressive=True)
    return out.getvalue()


def run(data_path, report_path, write=False, asset_base="https://fixingman.github.io/stockholm-guide/assets"):
    guide = json.loads(Path(data_path).read_text(encoding="utf-8"))
    results = []
    for item in guide["top3"]:
        outcome = {"title": item["title"], "status": "fallback", "source_pages": []}
        pages = [item["url"]] + item.get("image_source_pages", [])
        pages = list(dict.fromkeys(pages))[:4]
        approved = item.get("image_reuse_approved") is True
        # An already approved cached asset need not be replaced.
        if item.get("image_verified") and item.get("image_cache_file") and (ROOT / "assets" / item["image_cache_file"]).is_file():
            outcome.update(status="existing_cached", asset=item["image_cache_file"])
            results.append(outcome)
            continue
        winner = None
        for page in pages:
            attempt = {"page": page, "status": "unavailable", "candidates": []}
            outcome["source_pages"].append(attempt)
            try:
                candidates = discover(page)
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as e:
                attempt["error"] = str(e)[:180]
                continue
            attempt["status"] = "searched"
            for candidate in candidates:
                check = {"url": candidate["url"], "origin": candidate["description"], "status": "rejected"}
                attempt["candidates"].append(check)
                try:
                    blob, image, url, dims = validate_photo(candidate["url"])
                    check.update(status="valid_image", dimensions=list(dims))
                    # Match to the exact official event page; the source media itself
                    # may be on the organizer's CDN. The organizer must be the input.
                    if winner is None:
                        winner = (blob, image, url, page, candidate["description"])
                except (HTTPError, URLError, TimeoutError, OSError, ValueError) as e:
                    check["error"] = str(e)[:150]
            if winner:
                break
        if winner is None:
            outcome["reason"] = "No technically usable image found on supplied official pages"
        elif not approved:
            outcome["status"] = "needs_rights_review"
            outcome["candidate_url"] = winner[2]
            outcome["candidate_source_url"] = winner[3]
            outcome["reason"] = "Candidate loads; permission to cache or redistribute not approved"
        else:
            blob, image, url, page, desc = winner
            encoded = prepare(blob, image)
            digest = hashlib.sha256(encoded).hexdigest()
            filename = "featured-" + digest[:20] + ".jpg"
            target = ROOT / "assets" / filename
            outcome.update(status="cached" if write else "ready_to_cache",
                           asset=filename, sha256=digest, source_url=page, image_url=url)
            if write:
                target.parent.mkdir(exist_ok=True)
                target.write_bytes(encoded)
                item.update(image_verified=True, image_cache_file=filename,
                            image_cache_sha256=digest,
                            image_url=asset_base.rstrip("/") + "/" + filename,
                            image_source_url=page,
                            image_alt=item.get("image_alt") or ("Official event artwork for " + item["title"]))
        results.append(outcome)
    if write:
        Path(data_path).write_text(json.dumps(guide, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {"issue": guide.get("issue_number"), "total": len(results),
              "cached_or_approved": sum(r["status"] in ("cached", "existing_cached", "ready_to_cache") for r in results),
              "events": results}
    Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "guide_data.json"))
    ap.add_argument("--report", default="image-report.json")
    ap.add_argument("--write", action="store_true", help="Write only explicitly reuse-approved images to assets and data JSON")
    ap.add_argument("--asset-base-url", default="https://fixingman.github.io/stockholm-guide/assets")
    args = ap.parse_args()
    report = run(args.data, args.report, args.write, args.asset_base_url)
    for event in report["events"]:
        print(event["status"].upper(), event["title"], event.get("asset", event.get("candidate_url", event.get("reason", ""))))
    print(f"Image coverage: {report['cached_or_approved']}/{report['total']}; full audit: {args.report}")


if __name__ == "__main__":
    main()
