#!/usr/bin/env python3
"""Use verified smaller organizer-hosted variants; never rehost without permission.

This is an optional render-time transformation of public issue JSON. The original
photo URL and human identity review remain intact for editorial provenance.
The optimizer does not send email or modify committed source data.
"""
import argparse
import io
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from PIL import Image, ImageChops, ImageOps, ImageStat

from image_pipeline import https, validate_photo

TARGET_WIDTH = 1024
TARGET_BYTES = 350_000
MIN_WIDTH = 640
MAX_VISUAL_RMS = 22.0


def candidate_urls(url, dimensions):
    """Only organizer/CDN-supported resize conventions, never third-party proxies."""
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    width, height = dimensions
    if width <= TARGET_WIDTH:
        return []
    result = []
    if host.endswith(".sanity.io"):
        for w in (960, 768):
            params = dict(parse_qsl(parsed.query, keep_blank_values=True))
            params.update({"w": str(w), "q": "75", "fm": "jpg"})
            params.pop("auto", None)
            result.append(urlunparse(parsed._replace(query=urlencode(params))))
    elif re.search(r"/_next/image$", parsed.path):
        for w in (1080, 828, 750):
            params = dict(parse_qsl(parsed.query, keep_blank_values=True))
            params.update({"w": str(w), "q": "70"})
            result.append(urlunparse(parsed._replace(query=urlencode(params))))
    elif "/wp-content/uploads/" in parsed.path and re.search(r"\.(?:jpg|jpeg|png)$", parsed.path, re.I):
        stem, ext = parsed.path.rsplit(".", 1)
        if not re.search(r"-\d+x\d+$", stem):
            for w in (1024, 768):
                h = round(height * w / width)
                result.append(urlunparse(parsed._replace(path=f"{stem}-{w}x{h}.{ext}")))
    return [v for v in dict.fromkeys(result) if v != url and https(v)
            and urlparse(v).hostname == parsed.hostname]


def visual_difference(original, variant):
    """Pixel check guards against a same-site URL returning unrelated artwork."""
    a = ImageOps.exif_transpose(original).convert("RGB")
    b = ImageOps.exif_transpose(variant).convert("RGB")
    if abs(a.width / a.height - b.width / b.height) > .035:
        return float("inf")
    a = a.resize((128, 128), Image.Resampling.LANCZOS)
    b = b.resize((128, 128), Image.Resampling.LANCZOS)
    return max(ImageStat.Stat(ImageChops.difference(a, b)).rms)


def optimize_entry(item, checker=validate_photo):
    url = item.get("image_url")
    if not (item.get("image_verified") is True and url and https(url)):
        return {"status": "skipped", "reason": "no_verified_source"}
    if item.get("image_cache_file"):
        return {"status": "skipped", "reason": "already_approved_cached"}
    # Re-running on already optimized editorial data must be idempotent.
    if item.get("image_original_url"):
        return {"status": "skipped", "reason": "already_optimized"}
    try:
        original, img, final, dimensions = checker(url)
    except (ValueError, OSError, TimeoutError) as exc:
        return {"status": "unchanged", "reason": "source_unavailable", "detail": str(exc)[:160]}
    if len(original) <= TARGET_BYTES and dimensions[0] <= TARGET_WIDTH:
        return {"status": "unchanged", "reason": "already_efficient", "bytes": len(original)}
    best = None
    attempts = []
    for candidate in candidate_urls(url, dimensions):
        try:
            blob, picture, resolved, size = checker(candidate)
            if urlparse(resolved).hostname != urlparse(url).hostname:
                raise ValueError("cross_host_redirect")
            if size[0] < MIN_WIDTH or size[0] > 1200:
                raise ValueError("unsuitable_variant_width")
            if len(blob) >= len(original) * .75:
                raise ValueError("insufficient_byte_savings")
            difference = visual_difference(img, picture)
            if difference > MAX_VISUAL_RMS:
                raise ValueError("photo_identity_mismatch")
            attempts.append({"url": candidate, "status": "verified", "bytes": len(blob)})
            if best is None or len(blob) < best[0]:
                best = (len(blob), candidate, size, difference)
            if len(blob) <= TARGET_BYTES:
                break
        except (ValueError, OSError, TimeoutError) as exc:
            attempts.append({"url": candidate, "status": "rejected", "reason": str(exc)[:140]})
    if best is None:
        return {"status": "unchanged", "reason": "no_matching_smaller_official_variant",
                "bytes": len(original), "attempts": attempts}
    size_bytes, chosen, size, difference = best
    item["image_original_url"] = url
    item["image_url"] = chosen
    item["image_optimization"] = {
        "source_bytes": len(original), "optimized_bytes": size_bytes,
        "original_dimensions": list(dimensions), "optimized_dimensions": list(size),
        "max_pixel_rms": round(difference, 2), "method": "same-host-cms-variant",
    }
    return {"status": "optimized", "before_bytes": len(original),
            "after_bytes": size_bytes, "selected_url": chosen, "attempts": attempts}


def optimize_issue(issue, checker=validate_photo):
    results = []
    for event in issue.get("top3", []):
        result = optimize_entry(event, checker)
        results.append({"title": event.get("title", ""), **result})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report")
    args = parser.parse_args()
    source = Path(args.data)
    target = Path(args.output)
    if source.resolve() == target.resolve():
        parser.error("Use a separate output: committed source JSON must remain unchanged")
    issue = json.loads(source.read_text(encoding="utf-8"))
    results = optimize_issue(issue)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(issue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {"optimized": sum(r["status"] == "optimized" for r in results), "results": results}
    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
