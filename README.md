# Stockholm Guide

A fixed, table-based HTML email template for the November 1–14, 2026 sample. The design described in the earlier milestone uses a black editorial masthead, a dark hero plus two supporting cards, separate discoveries and reconsideration lists, and a skyline footer.

**Reference limitation:** the earlier README claimed `milestone-reference.png` was included. It is absent from every repository commit. The available prior-chat history also does not contain the screenshot. The existing `assets/milestone_*` fragments are retained, but a screenshot-level comparison with the approved composition remains pending retrieval of the original reference. Do not describe this build as a verified visual match.

## Build

```sh
python -m pip install -r requirements.txt
python render.py --data guide_data.json --output preview.html
cp preview.html index.html
python render.py --data guide_data.json --output email.html \
  --asset-base-url https://fixingman.github.io/stockholm-guide/assets
```

- `template.html.j2`: fixed presentation source; populate it rather than recreating the layout weekly.
- `guide_data.json`: sample content, with 3 picks, 7 discoveries, 17 reconsiderations and 6 unavailable items. `hero_pick_index: 1` retains the sample's hero choice.
- `preview.html` and `index.html`: identical browser previews with local branding paths. `index.html` is the existing GitHub Pages entrypoint.
- `email.html`: populated email HTML with absolute HTTPS branding URLs. Use this artifact as the HTML body when a send is explicitly requested; do not paste or attach the browser preview as a substitute. This repository does not send email.
- `preview.txt`: full plain-text content. The renderer also produces a text sibling for other output paths.

## Email layout

The shell is fluid with a 650px maximum width. Narrow-screen rules stack only the intended feature columns, not every nested table cell. Cards stack by default when a client removes styles; desktop media rules restore the columns. Header columns and brand sizes are constrained for desktop, narrow mobile, and an inline-only fallback. A table spacer separates the feature cards. All factual descriptions, date/price/booking details and original links are retained without truncation; reconsiderations remain image-free.

Jinja autoescaping is enabled explicitly because the source ends in `.html.j2`. Browser QA checks text boundaries as well as document overflow.

## Images

[IMAGE_AUDIT.md](IMAGE_AUDIT.md) records the official source, publication evidence and unresolved candidates. Two verified editorial press images are enabled: Verkligheten and Borda, with visible credits. Remaining event image slots deliberately use neutral abstract artwork. Do not infer image identity from a subject keyword or list position.

A photo requires `image_url`, `image_source_url`, `image_verified: true` and descriptive `image_alt`. Check identity and publication terms before setting the flag; record `image_rights_url`, `image_credit` and `image_checked_at`. Unverified proposed images fail rendering. Exact downloaded press-image snapshots support reproducible QA; production HTML uses the official HTTPS image URLs.

## Validation

```sh
python test_render.py
python -m playwright install chromium
python qa.py --output-dir qa-output
```

Set `CHROME_PATH` to use an existing browser executable. QA captures 1100px desktop, 390px mobile, 320px mobile, plus 390px/320px inline-only views. It asserts image loading from exact checked snapshots, all event links and metadata, no document overflow, no brand crossing its column, and HTML size below 100 KB. It writes screenshots and a JSON report.

These are Chromium and inline-only resilience tests, **not actual Gmail/Outlook delivery tests**. Gmail sanitization, dark mode, image proxying and Outlook's Word renderer can still differ. No email was sent to validate this change. The existing Pages workflow, weekly automation, schedule and recipients were not changed.
