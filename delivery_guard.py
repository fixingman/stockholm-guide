#!/usr/bin/env python3
"""Strict pre-send / sent-message audit for Minimal Editorial newsletters.

No Gmail credentials, no recipients, and no network writes. Image GET checks
are optional and intentionally report client-proxy uncertainty separately.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

from image_pipeline import validate_photo
from editorial_quality import audit as editorial_audit

SECTIONS = ("top3", "new_discoveries", "worth_reconsidering", "unavailable")
MAX_HTML_BYTES = 100_000
MAX_REMOTE_IMAGE_BYTES = 9_000_000
PLACEHOLDER_MARKER = "event-placeholder-thumb.jpg"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def html_digest(html):
    # MIME libraries commonly append one terminal newline and normalize CRLF.
    # Ignore only that transport-level variation; preserve all interior content.
    return sha(html.replace("\r\n", "\n").rstrip("\n").encode("utf-8"))


class EmailStructure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.images = []
        self.sections = []
        self.clickable_items = []
        self.black_strips = 0
        self.placeholder_tiles = 0
        self._in_heading = False
        self._heading = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = a.get("class", "").split()
        if "background:#161616;" in a.get("style", ""):
            self.black_strips += 1
        if tag == "a":
            self.links.append(a.get("href", ""))
            if "event-card-link" in classes or "top-thumb-link" in classes:
                self.clickable_items.append((classes[0], a.get("href", "")))
        if tag == "img":
            self.images.append({"src": a.get("src", ""), "alt": a.get("alt", "")})
        if "section-heading" in classes:
            self._in_heading = True
            self._heading = ""
        if a.get("aria-label") == "No verified event photo available":
            self.placeholder_tiles += 1

    def handle_data(self, data):
        if self._in_heading:
            self._heading += data

    def handle_endtag(self, tag):
        if tag in ("div", "h2") and self._in_heading:
            self.sections.append(self._heading.strip())
            self._in_heading = False


def image_delivery_check(url, checker=validate_photo):
    """Anonymous HTTPS fetch; no cookies or credentials. Not a Gmail proxy simulation."""
    if urlparse(url).scheme != "https":
        return {"url": url, "ok": False, "reason": "not_absolute_https"}
    try:
        blob, im, final, dims = checker(url)
        # Small total image payloads are preferable, but not a hard failure.
        mime = (im.format or "").upper()
        if mime not in {"JPEG", "PNG", "WEBP"}:
            return {"url": url, "ok": False, "reason": "unsupported_image_format", "format": mime}
        return {
            "url": url, "ok": True, "bytes": len(blob),
            "format": mime, "dimensions": list(dims), "resolved_url": final,
            "sha256": sha(blob), "warning": "large_image" if len(blob) > 1_000_000 else None,
        }
    except (ValueError, HTTPError, URLError, TimeoutError, OSError) as exc:
        return {"url": url, "ok": False, "reason": str(exc)[:200]}


def assess(data, html, *, network=False, checker=image_delivery_check):
    errors, warnings = [], []
    audit = EmailStructure()
    audit.feed(html)
    sections = ["Top 3 picks", "New discoveries", "Worth reconsidering", "Unavailable / sold out"]
    expected_events = sum(len(data.get(k, [])) for k in SECTIONS)
    if not data.get("issue_number") or not data.get("date_range"):
        errors.append("Missing issue number or date range")
    if data.get("date_range", "") not in html:
        errors.append("Date range does not match HTML")
    if len(html.encode("utf-8")) >= MAX_HTML_BYTES:
        errors.append("HTML too large for conservative Gmail clipping limit")
    if "<script" in html.lower():
        errors.append("Scripts in email HTML")
    if audit.sections != sections or audit.black_strips != 4:
        errors.append("Missing or altered black section-title strips")
    if len([x for x in audit.clickable_items if x[0] == "top-thumb-link"]) != 3:
        errors.append("Expected three clickable Top 3 image slots")
    rows = [x for x in audit.clickable_items if x[0] == "event-card-link"]
    if len(rows) != expected_events - len(data.get("unavailable", [])):
        errors.append("Incomplete clickable event rows (possible truncated issue)")
    if PLACEHOLDER_MARKER in html:
        errors.append("Remote generic placeholder image found")
    for section in SECTIONS:
        if not data.get(section):
            errors.append("Empty section: " + section)
        for item in data.get(section, []):
            url = item.get("url", "")
            if url and url not in audit.links:
                errors.append(f"Missing event link: {item.get('title', '?')}")
    rendered_imgs = [x["src"] for x in audit.images]
    top = data.get("top3", [])
    if len(top) != 3:
        errors.append("Expected exactly three featured picks")
    selected = []
    for i, item in enumerate(top):
        name = item.get("title", f"top3[{i}]")
        photo = item.get("image_url")
        cached = item.get("image_cache_file")
        if cached:
            # The template renders the hosted URL in image_url with default asset_base_url.
            photo = "https://fixingman.github.io/stockholm-guide/assets/" + cached
        if item.get("image_verified") and photo:
            if not photo.startswith("https://"):
                errors.append(f"Image is not HTTPS: {name}")
            if photo not in rendered_imgs:
                errors.append(f"Featured image not present in outgoing HTML: {name}")
            if photo in selected:
                errors.append(f"Duplicate featured image: {name}")
            selected.append(photo)
        else:
            warnings.append(f"HTML fallback instead of verified image: {name}")
    if audit.placeholder_tiles != 3-len(selected):
        errors.append("Incorrect HTML fallback thumbnail count")
    if len(audit.images) != len(selected)+1:  # 1 skyline
        errors.append("Unexpected image count in outgoing HTML")
    if not rendered_imgs or not rendered_imgs[-1].endswith("/milestone_skyline.png"):
        errors.append("Skyline footer image missing")
    checks = [checker(x) for x in selected] if network else []
    if network:
        for c in checks:
            if not c.get("ok"):
                errors.append(f"Featured image failed anonymous download: {c['url']}: {c.get('reason')}")
            elif c.get("warning"):
                warnings.append(f"Image load warning: {c['url']}: {c['warning']}")
    else:
        warnings.append("Anonymous live image checks not performed; use --network before delivery")
    if any(item.get("image_cache_file") for item in top):
        warnings.append("Hosted images must already be deployed before sending")
    return {
        "ready_for_delivery": not errors, "errors": errors, "warnings": warnings,
        "issue_number": data.get("issue_number"), "date_range": data.get("date_range"),
        "total_event_rows": expected_events, "section_titles": audit.sections,
        "featured_images": selected, "image_checks": checks, "inline_fallbacks": audit.placeholder_tiles,
        "html_sha256": html_digest(html), "html_bytes": len(html.encode("utf-8")),
        "image_proxy_certified": False,
    }


def create_manifest(data_file, html_file, *, network=False, checker=image_delivery_check):
    data_bytes = Path(data_file).read_bytes()
    html_bytes = Path(html_file).read_bytes()
    data = json.loads(data_bytes)
    html = html_bytes.decode("utf-8")
    report = assess(data, html, network=network, checker=checker)
    report["data_sha256"] = sha(data_bytes)
    report["rendered_html_file"] = Path(html_file).name
    report["preflight_timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    return report


def extract_html_from_mime(mime_bytes):
    message = BytesParser(policy=policy.default).parsebytes(mime_bytes)
    parts = [p for p in message.walk() if p.get_content_type() == "text/html"]
    if len(parts) != 1:
        raise ValueError(f"Expected exactly one text/html part, got {len(parts)}")
    return parts[0].get_content()


def verify_sent_html(sent_html, manifest):
    digest = html_digest(sent_html)
    valid = digest == manifest.get("html_sha256")
    return {"matched": valid, "expected_sha256": manifest.get("html_sha256"),
            "sent_html_sha256": digest, "reason": None if valid else "Sent HTML differs from preflight"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", help="Fresh issue JSON")
    parser.add_argument("--html", help="The exact outgoing HTML, not a preview from another issue")
    parser.add_argument("--manifest", help="Output manifest JSON")
    parser.add_argument("--network", action="store_true", help="Perform anonymous image GET/decode checks")
    parser.add_argument("--editorial-strict", action="store_true", help="Block unverified event facts or unreviewed photo identities")
    parser.add_argument("--history", action="append", default=[], help="Prior issue JSON for repeat detection")
    parser.add_argument("--verify-sent-mime", help="Optional downloaded raw Gmail RFC822 MIME file")
    args = parser.parse_args()
    if args.verify_sent_mime:
        if not args.manifest:
            parser.error("--verify-sent-mime requires --manifest")
        manifest = json.loads(Path(args.manifest).read_text())
        try:
            result = verify_sent_html(extract_html_from_mime(Path(args.verify_sent_mime).read_bytes()), manifest)
        except (ValueError, OSError) as exc:
            result = {"matched": False, "reason": str(exc)}
        print(json.dumps(result, indent=2))
        return 0 if result["matched"] else 1
    if not (args.data and args.html and args.manifest):
        parser.error("--data, --html and --manifest are required for pre-send checks")
    report = create_manifest(args.data, args.html, network=args.network)
    if args.editorial_strict:
        history = [json.loads(Path(p).read_text(encoding="utf-8")) for p in args.history]
        editorial = editorial_audit(json.loads(Path(args.data).read_text(encoding="utf-8")),history,strict=True)
        report["editorial_quality"] = editorial
        report["errors"].extend("EDITORIAL: "+e for e in editorial["errors"])
        report["warnings"].extend("EDITORIAL: "+w for w in editorial["warnings"])
        report["ready_for_delivery"] = not report["errors"]
    Path(args.manifest).write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n")
    print(json.dumps({"ready_for_delivery":report["ready_for_delivery"],
                      "errors":report["errors"],"warnings":report["warnings"],
                      "featured_images":len(report["featured_images"]),
                      "html_sha256":report["html_sha256"]}, indent=2))
    return 0 if report["ready_for_delivery"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
