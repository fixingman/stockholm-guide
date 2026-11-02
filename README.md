# Stockholm Guide — approved milestone reproduction (v2)

This is a reusable, responsive HTML email layout built **against the exact monochrome milestone screenshot**, not redesigned from a loose visual prompt. The reference screenshot is included as `milestone-reference.png` for direct comparison.

## Structure intentionally locked

- Black editorial header, stacked white Georgia brand, issue/date line, brush illustration, and torn-paper transition.
- One integrated black Top 3 hero card plus two supporting image-strip cards. Event photos appear only if source-verified; otherwise neutral abstract artwork preserves the geometry.
- Separate, full-width **New discoveries** list with event-specific verified official images when available; otherwise a neutral abstract illustrated placeholder. Complete event text is always retained.
- Separate, full-width, **image-free Worth reconsidering** list.
- Complete **Unavailable / sold out** list.
- The photographed/illustrated Stockholm skyline from the approved reference, as the terminal footer.
- Generous margins between the sections, no collapsible content, no ticket/free/price status pills and no repeated arrow icons.
- All items show event title, descriptions, dates/time, price, booking status, and original booking URL. Content naturally wraps: there is no text truncation.

## Files

- `template.html.j2` — fixed presentational source; **do not rewrite it each week**.
- `guide_data.json` — 1–14 Nov 2026 sample with 3 Top Picks, 7 new discoveries, 17 worth reconsidering, 6 unavailable. `hero_pick_index` controls which of the 3 picks is the large visual hero (1 for the approved sample; default 0 for future issues).
- `render.py` — deterministic source-to-email rendering; refuses missing title/date/price/booking/link, malformed event URLs, or a different number of picks.
- `preview.html` — populated preview. Open locally with its adjacent `assets/` directory.
- `preview.txt` — same content in plain text.
- `desktop.png` / `mobile.png` — full browser snapshots; `desktop-top.png` / `mobile-top.png` — convenient top crops.
- `assets/milestone_*` — image fragments derived directly from the approved screenshot, not new AI visual interpretations.
- `qa.py` — automated desktop/mobile Chromium smoke tests.

## Render

```
python render.py --data guide_data.json --output preview.html
python qa.py
```

In production, image assets must be published at stable HTTPS URLs. Render with `--asset-base-url https://your-host/assets` after publishing the files. Do **not** send with local image paths: recipients would see missing images. Event-specific imagery requires **all** of `image_url`, `image_source_url` (official event/organizer page), `image_verified: true` (explicitly checked for identity and reuse rights), and descriptive `image_alt`. Invalid or unverified combinations fail rendering, rather than quietly showing a wrong image. For absent photos, the neutral abstract `event-placeholder.jpg` / `event-placeholder-thumb.jpg` are used. Do not recycle another event's image or auto-rotate thumbnails.

## Important limitations

- This is a faithful **HTML adaptation**, not a pixel-identical screenshot: the approved reference had compressed/invented event text; the real email uses longer accurate descriptions and will therefore be taller. Email-client rendering can vary (Gmail, Outlook, Apple Mail) even with fallback-safe tables.
- The downloaded preview uses local image files. The existing weekly automation does **not** yet have durable access to this package. Nothing has been sent or changed in the automation by this build.
- The sample issue number is 001, **not** the illustrative '#142' in the concept screenshot.
- The old cropped mockup event photographs are **not used by the renderer anymore**. Event photo slots without verified official photos now show neutral abstract graphic fallbacks, never images implying a particular artist or performance.

## Weekly image verification contract

Do not select images by list index, inferred topic, stock-photo keyword, or last week's event. For every proposed event image, first open the official event/organizer listing; verify the image visually depicts that exact event, show/artist, and that reuse is allowed. Record its verified HTTPS image URL, exact official source page, concise description, and `image_verified: true`. If any check fails, omit `image_url` entirely; the visual template renders its neutral artwork. Worth reconsidering remains image-free regardless. The design template and full factual metadata must never be rewritten during discovery.
