# November sample image audit — 2 November 2026

The original JSON had no `image_url` fields. All ten visible event image slots therefore intentionally rendered neutral artwork; this was not ten broken image downloads. Seven discoveries plus three picks cover nine distinct events.

## Enabled

- **Verkligheten:** the [official production page](https://kontrar.se/en/show/verkligheten/) links the exact `Verkligheten_PRESS_03-Foto_-Julia-Mard-1.jpg` photograph. Download returned HTTP 200, image/jpeg. Visually inspected: film camera operator and performers on a studio stage. Credit: Julia Mård. The [venue press policy](https://kontrar.se/en/press/) permits publication of press images in related articles/reviews. Used as an editorial event illustration; not a general image license.
- **Borda:** the [official event page](https://dansenshus.se/en/program/lia-rodrigues-bra-borda/) identifies the production; the [official press-image record](https://press.dansenshus.se/media/377195/borda-lia-rodrgues-foto-sammi-landweer1) explicitly labels this image **Media use**, credits © Sammi Landweer, and identifies the November production. Its actual image URL is `https://cdn.filestackcontent.com/auto_image/dWBAdpO8R9RXrGpe64Ko` (not the press page's generic social header image). Download returned HTTP 200, image/jpeg. Visually inspected: a figure surrounded by translucent material on a dark stage.

The JSON records direct official image URLs, event/source URLs, rights evidence, credit, check date and alt text. Byte-identical downloaded snapshots in `assets/*-press.jpg` make local browser QA deterministic. QA serves those snapshots only for the matching official URLs; it never replaces failed images with placeholders. Production HTML links the official image URLs. Publication terms and upstream availability should be rechecked for future editions.

## Retained neutral artwork

| Event | Finding | Reason not enabled |
| --- | --- | --- |
| Adam Pultz & The Spectral Parrot | Goethe event endpoint returned 403 | Could not verify exact image and publication terms |
| Fight Symphony | Organizer's Billetto page identifies event; page request returned 403, cached listing exposes a candidate | Identity/rights of the candidate image not independently verified |
| SELF | Official page publishes a Sanity-hosted candidate | Publication permission for that exact artwork not established |
| Clown and Le Jeu | Listing publishes `https://nupagang.se/fb-og/90556.jpg` | Aggregator social preview is insufficient official identity/rights evidence |
| Chamber / Cacti | Official production page publishes a Chamber photograph | Exact publication permission not established |
| Open Studio — Ink & Line | Tickster listing publishes a CDN candidate | Exact image identity/publication permission not established |
| Art of: Drag × Admira | Sample event URL returned 404 | No verified event-specific image obtained |

No stock images, generated event imagery, old mockup event crops or photographs of unrelated productions were added. Worth reconsidering remains image-free.
