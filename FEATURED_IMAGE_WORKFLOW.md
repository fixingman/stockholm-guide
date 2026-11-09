# Featured image workflow

Required for every new Stockholm Guide edition, before HTML rendering.

1. For **each of the three featured events**, search the exact event title, year and Swedish spelling. Visit the exact official organizer/event page (not the venue homepage), then linked festival, artist, press and ticketing pages. Inspect embedded images and og:image.
2. Prefer official photography or same-event promotional artwork. A poster is fine if captioned as artwork, never misrepresented as a documentary photograph. Never substitute last year's festival poster, unrelated stock images, an old image of a different edition, or AI-generated depictions.
3. Verify identity, exact edition/date, HTTPS image URL, successful image response, cropping, attribution and **permission to use/embed**. Public display alone does not establish reuse rights. Only host assets in this repository when reuse permission allows it. Do not modify signed URL query parameters or assume third-party hotlinks will stay available.
4. For each verified picture, provide all of: `image_verified: true`, `image_url`, `image_source_url`, `image_alt`. Add `image_cache_file` only when the named asset already exists in the approved assets directory and corresponds to the exact event. Keep credit and qualifiers in alt/records.
5. When no safe image is found, omit image fields and keep the neutral placeholder, **reporting which event needs an image**. Never invent a verified flag. Image selection is by event identity, never by list position.

Pre-send: Run `python render_minimal.py --data FRESH_ISSUE.json --output EMAIL.html --asset-base-url https://fixingman.github.io/stockholm-guide/assets`. Its output reports Top 3 verified image coverage and missing-image titles; rendering rejects broken/incomplete verified-image metadata and missing cached files. A missing image does not prevent sending a valid edition.

Audit notes: `IMAGE_AUDIT.md`. In sample edition #002 the previously authorized Verkligheten production press photo is restored; the other two remain placeholders until individually verified, including reuse permissions.

## Tested official-image URLs (8 November 2026)

A reusable diagnostic GitHub Actions workflow, `.github/workflows/featured-image-probe.yml`, fetched official event pages, discovered `og:image` candidates and tested the returned media types. [Workflow run 42480715638](https://github.com/fixingman/stockholm-guide/actions/runs/42480715638) passed. These are **technical availability results, not licenses or guarantees that email clients hotlink them**.

- Visioner av Nuet — official Fylkingen event artwork: `https://fylkingen.se/media/sites%2Fclvuuu5cs0001xwfc7ne538fo%2Fmedia%2Ff29a6c33-2b34-47e5-8359-dbaf58f21682-VaN-2-16x9.jpg`. HTTP 200, image/jpeg. Alternate Tekniska museet event artwork: `https://www.tekniskamuseet.se/app/uploads/2026/10/van-2-fb-event.jpg`, HTTP 200, image/jpeg.
- Sound of Stockholm Saturday — official Fylkingen Saturday `og:image` (Lisa Ullén): `https://fylkingen.se/media/sites%2Fclvuuu5cs0001xwfc7ne538fo%2Fmedia%2F0ad16af2-9ebe-477d-8e35-c3400eb3c1d5-lisaullen_6W7A1951.jpg`. HTTP 200, image/jpeg. Alternate official festival site `og:image`: `https://freight.cargo.site/w/1000/i/X3215576396280121608059225178842/screenshot-3340826510.jpg`, HTTP 200, image/jpeg.

Current issue #002 stores the two event-specific `image_candidate_*` fields for review but intentionally does **not** set `image_verified` or enable them in the newsletter until embedding and permission concerns are resolved. The original official event-specific links are stored rather than generic venue homepages.


## Operational implementation (9 November 2026)

The real implementation is `image_pipeline.py` (requires Pillow). It reads the **fresh issue JSON**, inspects exact official event pages, checks `og:image`, Twitter image metadata, JSON-LD, lazy images and inline photos, rejects logos/icons, verifies HTTPS/content-type/decodability/size, and creates `image-report.json` with candidates and reasons.

For an exact approved image, set both `"image_reuse_approved": true` and `"image_approved_source_url": "https://official.example/this-exact-image.jpg"` on that Top 3 entry. A mere `image_candidate_url` is NOT permission. The approval must reflect actual rights to redistribute/host; never infer it solely from an image being publicly viewable. The script then makes an optimized JPEG with a SHA-based stable filename under `assets/featured-*.jpg` and writes the corresponding `image_verified`, `image_cache_file`, `image_cache_sha256`, `image_source_url` and hosted `image_url` fields.

```sh
python -m pip install 'Pillow>=11,<14'
python image_pipeline.py --data fresh-issue.json --report image-report.json
# ONLY once source/redistribution rights have been approved:
python image_pipeline.py --data fresh-issue.json --report image-report.json --write
python render_minimal.py --data fresh-issue.json --output email.html
```

GitHub Actions: `.github/workflows/featured-image-cache.yml` runs automatically when `guide_data.json` or the pipeline changes. It audits **all** Top 3, caches and commits **only** the images with explicit matching approval, and uploads the audit report as a workflow artifact. It can also be started manually via Workflow Dispatch. Wait for the cached-assets commit and **successful Pages deployment** before emailing, or the stable URLs may return 404 temporarily. A fresh JSON file held only in an automation's runtime is NOT automatically uploaded to GitHub; the weekly workflow must explicitly publish that issue into the repository for Actions to process. If it cannot do so, retain safe HTML placeholders rather than promising an automatic cache.

Even stable HTTPS hosting cannot override a recipient's email-client image blocking settings. The Minimal Editorial no-photo fallback is an inline HTML tile, which does not depend on downloading an image.

The 8–21 Nov sample is presently **1/3 cached**, with the other two official artwork URLs found and technically validated, but not authorized for redistribution. This approval boundary is deliberate, not a broken fetcher.
