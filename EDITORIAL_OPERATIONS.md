# Editorial and subscription operations — Stockholm Guide

The current `guide_data.json` is **a legacy sample**, not a live or approved Sunday issue. The strict checks are intended for **new** editions. CI on sample data uses baseline mode to surface missing evidence without fabricating confirmations.

## 1. Verified editorial facts

For every event in the new 14-day guide, collect fresh organizer evidence separately for:
- date/time (including time zone or explicitly variable schedule)
- venue/address
- ticket booking/availability (unknown is allowed but must be declared)
- price (unknown is allowed but must be declared)

Use the item's `verification` field, e.g.:

```json
{
  "title": "Example event",
  "url": "https://organizer.example/events/example",
  "organizer_url": "https://organizer.example/events/example",
  "event_start": "2026-11-20T19:00:00+01:00",
  "verification": {
    "checked_at": "2026-11-19T08:00:00+01:00",
    "date": {"status": "confirmed", "source_url": "https://organizer.example/events/example"},
    "venue": {"status": "confirmed", "source_url": "https://organizer.example/events/example"},
    "booking": {"status": "unknown", "source_url": "https://organizer.example/events/example", "note": "Tickets listed; live availability not checked"},
    "price": {"status": "confirmed", "source_url": "https://organizer.example/events/example"}
  }
}
```

For exhibitions with variable times use `schedule_note` rather than inventing `event_start`. A source URL and status record are audit metadata, **not** proof the underlying facts are true; the editor must actually inspect official pages. Refresh checks within seven days of send. Keep source URLs and machine-readable dates. Unknown or unavailable statuses must not be presented as confirmed.

```bash
python editorial_quality.py --data FRESH_ISSUE.json --history LAST_ISSUE.json --strict --report editorial-report.json
```

Strict mode blocks missing evidence or invalid photo identity review; source concentration and repeats produce editorial warnings and should trigger human reconsideration without arbitrarily deleting relevant experiences.

## 2. Diversity and novel discovery

Discover from at least several distinct organizer classes: small venues and independent promoters; participatory studios and workshops; experimental theatres; exhibition and sound-art spaces; and official institution/event calendars. Treat aggregators as leads, then navigate to official organizer event pages. Research a sufficiently broad pool before filtering; do not invent event dates or availability.

```bash
python discovery_ranker.py --candidates researched-candidates.json --history LAST_ISSUE.json --output shortlist.json --limit 24 --organizer-cap 4
```

Candidates are researcher-supplied JSON, with fields `title`, `url`, optional `organizer_url`, `evidence_url`, `novelty` (e.g. `unusual`), `participatory`, and `image_candidate_url`. The ranker penalizes repeats, deprioritizes generic aggregators, deduplicates normalized titles, and limits any one organizer to four entries by default. The cap is an editorial heuristic, not a coverage limit; the full issue must include all relevant experiences. Inspect deferred items and override the cap when necessary.

## 3. Featured photography identity and email robustness

An HTTP 200, successful JPEG decode, or matching `og:image` tag only proves technical validity. It does **not** confirm that the photo depicts the actual event. Manually review exact event artwork; for an organizer-wide festival graphic, explicitly verify that the festival graphic is an appropriate representation of the named performance, rather than treating all festival images as interchangeable.

Add to each Top 3 entry:
```json
"image_identity_review": {
  "event_match": true,
  "reviewer": "Editor",
  "source_page": "https://organizer.example/events/example",
  "checked_at": "2026-11-19T08:00:00+01:00"
}
```

The source page must match the exact event page or an explicit organizer-owned alternate in `image_source_pages`. Never set `event_match: true` simply because a crawler returned an image; this requires real review. Keep `image_alt` descriptive and accurate. Respect embedding and reuse restrictions. Don't rehost copyright-protected photos unless separately approved.

Pre-send `delivery_guard.py --network --editorial-strict` checks actual HTML, HTTPS image downloads, and the editorial review records. This **does not certify Gmail's image proxy**. Design remains useful with images disabled: alt text for real photos, neutral HTML fallback cards for missing photos, visible event text and links. Preview light/dark mode and Gmail/iOS behavior manually when the visual design changes; never promise an automated screenshot test unless one is installed.

## 4. Private subscriptions and deliverability

**Do not store subscriber addresses, consent records, opt-out lists, or Gmail credentials in the PUBLIC GitHub repository, its CI artifacts, or commit history.** Maintain a private list of subscribers and a persistent suppression list with unsubscribe timestamps. Process opt-outs *before* the next send. A visible mailto unsubscribe is currently manual; this is **not** an automated one-click unsubscribe service. Respect opt-outs immediately. Do not add a `List-Unsubscribe` header unless it points to a functioning removal handler.

A local/private sender configuration can be validated using:

```bash
python recipient_guard.py --config /private/stockholm-recipients.json --report /private/recipient-check.json
```

Expected keys: `to`, `cc`, `bcc`, `consented`, `suppressed`, `unsubscribe_mailbox`, `mode` (`scheduled` or `test`). With `mode: test`, every BCC and CC recipient is blocked; tests are only for the owner address. For scheduled sends, require exactly one owner To, no duplicate addresses, active consent, and no suppressed recipients. If consent evidence is unavailable, do not fake it: verify permission with the sender before relying on the consent gate. The owner's standing authorization to send the existing scheduled list is not evidence of individual third-party opt-in.

Check sender identity, Gmail account authentication (SPF/DKIM/DMARC as relevant), bounce notices and unsubscribe requests separately from this local script. No analytics pixels or open tracking are included. Gmail Sent MIME read-back and receipt confirmation are distinct from successful inbox placement. If mail delivery bounces, remove or investigate that address; do not retry to a suppressed address.

## Mandatory fresh-send checklist

1. Find candidate events and run diversity shortlist; verify each final event against organizer sources.
2. Review the three selected event images for **identity** and anonymous HTTPS download reliability.
3. Render the full new issue HTML and run `delivery_guard.py --data FRESH_ISSUE.json --html OUTGOING.html --manifest manifest.json --network --editorial-strict --history LAST_ISSUE.json`.
4. Run private `recipient_guard.py` on the actual authorized recipient list and current unsubscribe records. Never use BCC for tests without explicit permission.
5. Only if both gates pass, send **exactly OUTGOING.html**. Read Gmail Sent MIME and compare against the manifest; log any mismatch **without automatically resending**.

The scheduled ChatGPT automation may not have the same runtime/files as GitHub CI. If it cannot run a gate, disclose that honestly instead of reporting it as passed. No CI job in this repository sends email.
