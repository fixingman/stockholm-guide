# Stockholm Guide

A reusable HTML email renderer based on the supplied **The Stockholm Guide: Top Picks & Discoveries** milestone image. The original reference is now included as `milestone-reference.png`; its visual composition is recorded in `layout-spec.json`.

The layout uses the black masthead and brush, a single continuous photographic hero with live text, two supporting cards, compact discovery rows with thumbnail / text / date / venue columns, separate image-free reconsideration rows, rules beside the section headings, and the skyline footer. Mobile and stylesheet-free views stack the row columns. All 3 picks, 7 discoveries, 17 reconsiderations and 6 unavailable sample entries remain; the real edition is consequently taller than the illustrative reference.

The mockup is a design reference, not event evidence: its saxophone photograph, venues, descriptions, dates and issue #142 are not copied as facts. The sample retains issue #001 and verified event information, full prices/booking qualifications and all 33 event links.

## One-command build

```sh
python -m pip install -r requirements.txt
python -m playwright install chromium
python build.py --data guide_data.json --output-dir build
```

Use `CHROME_PATH=/path/to/browser` to select an installed Chromium browser. The build:

1. Clears any prior success marker and records hashes of the data, template and reference.
2. Renders a local preview, absolute-HTTPS email HTML and plain text.
3. Checks desktop 1100px, mobile 390px/320px, and stylesheet-free 390px/320px views.
4. Verifies actual production image URLs over HTTP, image decoding, and the checked photo hashes.
5. Writes `build/build-report.json` with `ready_for_delivery: true` only when every step succeeds. Any missing/changed image, layout failure or missing reference leaves a nonzero exit and a false result.

The command has **no sending step** and contains no recipient list. The existing scheduler has not been changed or connected to this command. A scheduled runner must execute this build successfully and use its generated `email.html` as the HTML body, rather than reconstructing the email from a prompt. This repository alone does not establish that the weekly automation is configured correctly.

## Files

- `template.html.j2`: fixed layout; weekly discovery supplies structured JSON, not new HTML.
- `guide_data.json`: November 1–14 sample, source/credit records and checked image hashes.
- `render.py`: requires complete title/date/description/price/booking/venue/link fields; escapes all text; rejects unverified or changed cached photos.
- `preview.html` / `index.html`: matching preview and existing Pages entrypoint.
- `email.html`: same edition with absolute HTTPS branding paths.
- `preview.txt`: full plain-text content.
- `qa.py`: checks actual images and backgrounds, content, link counts, overflow, masthead boundaries, a single-cell hero, and desktop column alignment/mobile stacking. It never substitutes a working image for a failed URL.
- `preflight.py`: independent live image/content readiness report.
- `IMAGE_AUDIT.md`: per-image provenance, credit, source limitations and publication evidence where available.
- `VALIDATION.md`: comparison findings and validation boundaries.

## Images

Every visible photo slot now has identified official event/artist/organizer imagery. The clown course uses an explicitly labeled **organizer workshop archive (Caen)**; it is not represented as a photograph of the November Stockholm session. The seven other unique event images and Adam Pultz portrait are matched to their official production/event/ticket sources.

`image_verified` records official-source provenance and visual identity; it is not a claim of a separate redistribution license. The two previously verified press images are hosted as checked copies; other newly identified images remain linked to their exact official URLs. Original URLs, source pages, credits, check dates and SHA-256 checks are retained. Do not normalize, reorder or regenerate signed image query strings: the exact Fight Symphony URL works while the earlier reordered URL returned 403.

When a future event has no identified image, retain a clearly neutral fallback in the preview and let delivery preflight report the edition incomplete. Never invent event imagery or silently substitute another production's photograph. Reconsiderations remain image-free.

## Individual commands

```sh
python render.py --output preview.html
cp preview.html index.html
python render.py --output email.html --asset-base-url https://fixingman.github.io/stockholm-guide/assets
python -m unittest test_render test_preflight test_build
python qa.py --output-dir qa-output
python preflight.py --html email.html --report delivery-report.json
```

These are browser composition and live-network checks, **not a Gmail delivery certification**. No new test email has been sent. The template uses tables, inline styles, background attributes and width media queries supported in [Google's Gmail CSS reference](https://developers.google.com/workspace/gmail/design/css); client-specific sanitization, dark mode, proxies and Outlook's Word renderer can still vary.
