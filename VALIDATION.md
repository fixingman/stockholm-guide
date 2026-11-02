# Validation — reference-based revision, 2 November 2026

## Reference comparison

The user supplied `The Stockholm Guide_ Top Picks & Discoveries.png` directly. It is preserved as `milestone-reference.png`, with its SHA-256 recorded in `layout-spec.json` and every build manifest.

The previous implementation diverged in composition: detached hero photo, paragraph-style discovery/reconsideration lists, dates and venues below the prose, no ruled section headings, and incorrect masthead proportions. The revised template reproduces the reference's composition with:

- A stacked serif brand, vertical tagline separator, brush background, issue line and torn-paper edge.
- One continuous photographic hero background with readable live text, followed by two equal-height image-strip cards.
- Compact discovery rows: thumbnail, title/description, date/time and venue in separate desktop columns.
- Separate image-free reconsideration rows: title, description, date/time and venue columns.
- Section heading rules, monochrome image blending and the original skyline footer.
- Stacked mobile/stylesheet-free layouts, with protected text backgrounds in the narrow masthead.

The reference's fictional/inaccurate event photographs, venues, descriptions and issue #142 are not copied as factual content. All 33 entries/links and their complete descriptions, price/booking qualifications remain, so the actual edition is taller than the concept image. The unavailable section remains complete.

## Image verification

All ten visible slots now have identified official event, artist or organizer imagery. Sources were opened, image files loaded and inspected visually, and the exact bytes hashed. The clown photograph is explicitly labeled **Organizer workshop archive (Caen)** rather than represented as the November Stockholm session. See IMAGE_AUDIT.md for all nine unique source records.

The exact signed Fight Symphony URL works; the earlier parameter-reordered URL returned 403. The organizer's exact workshop-image tag also works where the cached reordered candidate failed. URL parameter order and encoding are preserved. Known press-image copies remain self-hosted; newly identified images link to their original official hosts and make no independent redistribution-license claim.

The organizer's workshop page additionally verifies 3, 5, 10 & 12 November, 10:00–14:00 and 3,200 SEK. Those replace the sample's unknown course timetable/price, with the supporting source retained.

## Checks

- Eight regression tests cover escaping, unverified/modified photos, absolute URLs, network failures, placeholders, signed/background URLs and clearing a stale successful build marker.
- Five browser views: 1100px desktop, 390px/320px mobile, and 390px/320px with the stylesheet removed. Tests assert full metadata, all 33 links, images/backgrounds loading, no document overflow, masthead boundaries, the integrated hero and the desktop/mobile row-column structure.
- Browser QA uses actual URLs and local published files, without request interception or substitute photos. One browser context shares its normal network cache across viewport checks.
- Live preflight fetches and decodes production image URLs, compares checked image hashes and verifies the recorded reference hash. It reports missing or changed image sources and exits nonzero on failure.
- `build.py` renders preview/email/plain text, runs browser QA and live preflight, and records input/template/reference/email hashes. It clears the old success marker before checking inputs and never marks an interrupted/failed build ready.
- Preview and Pages entrypoint are identical. Email HTML differs only in absolute branding/hosted-image URLs and remains below the 100 KB clipping guard.

## Execution boundaries

No new test email has been sent. No recipient, schedule, weekly automation, provider, proxy or routing setting was changed. The repository build command contains no sending code. Connecting/verifying the existing Sunday scheduler is separate from validating this edition; a successful build does not establish that the scheduler invokes it.

Google's [Gmail CSS reference](https://developers.google.com/workspace/gmail/design/css) documents the table, width media-query, background, object-fit and blend-mode properties used. Browser and live-network checks are not certification of actual Gmail delivery, image proxy behavior, dark mode or Outlook's Word renderer.
