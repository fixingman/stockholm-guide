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
