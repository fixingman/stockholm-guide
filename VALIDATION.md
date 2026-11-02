# Validation — 2 November 2026

## Findings and correction

- All event images were fallbacks because the sample JSON contained no image metadata. Enabled two verified official press photographs and retained neutral artwork for unresolved events; see IMAGE_AUDIT.md.
- The 650px fixed-width shell was dependent on a media query to shrink. It is now fluid inline, with a desktop maximum.
- Header percentage widths, padding and a fixed 196px brush competed for space. The brush is now fluid; header type and column widths have narrow-screen and inline-only fallbacks.
- The former mobile selector changed every nested feature-table cell to a full-width block. Stacking is now limited to the feature columns.
- Supporting-card spacing now uses a table spacer instead of relying on a table margin.
- `.html.j2` was not covered by the previous autoescape extension list. Explicit autoescaping prevents event text from injecting markup.
- Regenerated the Pages entrypoint and added a distinct email artifact with absolute branding paths.

## Checks

- Renderer preserves all 3 / 7 / 17 / 6 items, metadata and original event links.
- Regression tests reject an unverified photo and escape markup in event titles.
- Browser checks at 1100px, 390px and 320px, plus 390px and 320px with the stylesheet removed. Assertions cover image loads, all 33 event links, content presence, document overflow, masthead text crossing columns and HTML size.
- Official Verkligheten and Borda image endpoints returned HTTP 200 image/jpeg; exact photographs were visually inspected. Offline layout tests use byte-identical snapshots, not silent fallback images.
- `index.html` equals `preview.html`; `email.html` differs only in absolute branding paths.
- No email-send code or workflow was run. No recipient, schedule, weekly automation or routing configuration was changed.

## Limits

The full approved milestone screenshot could not be retrieved: it is absent from repository history and the available prior chat. Only existing image fragments and the documented section composition could be compared. An exact visual match is not established.

No actual Gmail message was sent or opened in a Gmail client during this validation. Chromium screenshots and stylesheet-removal checks are evidence of browser layout and fallback resilience, not a Gmail rendering certification. Unresolved event image slots remain abstract rather than inventing a photograph.

## Follow-up: delivery checks

The original sent test message was inspected read-only through Gmail. Its HTML contains the previous template and ten placeholder-image URLs; the missing event photos were in the sent source, not diagnosed as a Gmail network failure.

The November 2 deployed Pages artifact and both hosted press-image files returned HTTP 200. Delivery HTML now uses those hosted copies, checked against recorded SHA-256 hashes, while retaining official source URLs as provenance. Browser QA no longer intercepts photo requests to serve alternate snapshots. Production checks use actual network requests and decode the received image bytes.

A new `preflight.py` exits nonzero for missing event photography, relative/broken image URLs, changed published photo bytes, excessive HTML size, or a missing milestone reference. Tests ensure a loaded placeholder cannot produce a ready result and a network failure stays a failure. Renderer validations use explicit exceptions, which remain enabled under optimized Python execution.

The sample remains **not ready for unattended delivery**: eight visible slots across seven distinct events still lack verified photos. The newly supplied shared image URL opens a titled but empty message body in the available browser, so the reference image still needs to be attached directly. This follow-up adds no layout redesign and no scheduler/send/recipient changes. The preflight is repository tooling, not an already-connected scheduler guarantee.
