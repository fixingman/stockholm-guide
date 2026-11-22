# Sunday release integration, subscriber privacy and scanning cues

## Status: staged, not yet proven on unattended Sunday

GitHub CI and the ChatGPT Sunday automation run in separate environments. A successful build from the frozen `guide_data.json` sample must NOT be represented as a fresh Sunday delivery. The scheduled Nov 8 automation recorded a failed run despite a message being visible in Gmail Sent, so actual orchestration remains a risk.

**New production gate**: `.github/workflows/weekly-release-gate.yml` runs automatically when **`issues/current.json` is committed**, or can be manually dispatched. The trigger intentionally does NOT run on a workflow-file change with no fresh issue.

For a new issue:
1. Research all 14-day events and build `issues/current.json`. It must contain only public editorial event information, never subscribers or consent records. Include `issue_number`, `date_range`, `published_at`, Top 3 image metadata, full listing, event verification, and final review.
2. Revisit each event's actual organizer listing **within 24h before sending**. Record `final_review` with `checked_at`, `organizer_source_url`, `event_status` and `booking_status`. This is a factual editorial action performed by the editor/research assistant, NOT an automatic inference from a HTTP 200.
3. Commit fresh `issues/current.json`. Wait for the **Validate fresh Sunday newsletter (no sending)** GitHub run for that commit. It runs the actual Minimal Editorial renderer and `delivery_guard.py --network --editorial-strict --freshness-strict`. It rejects old sample issue #002, missing verified facts/identity reviews, stale event review, unavailable or cancelled events in available sections, broken remote images, missing links and unfit layout.
4. After SUCCESS, GitHub publishes the checked files onto dedicated branch `validated-sunday`, paths `verified/outgoing.html`, `verified/delivery-manifest.json`, `verified/issue.json`, and `verified/client-qa.json`. Fetch these exact files with the connected GitHub `fetch_file` action using `ref='validated-sunday'` — no ZIP extraction. Check `manifest.release_channel == 'production'`, `ready_for_delivery`, `source_commit_sha` equal to the fresh issue commit SHA, strict editorial/freshness checks, matching issue ID and SHA-256 HTML digest. **Only that exact checked HTML** is eligible for a regular authorized send. Do not send HTML from a previous Gmail message or a static preview. The original `verified-sunday-issue-html-and-manifest` ZIP is retained as a separate audit artifact.
5. Independently check the **private** subscriber/consent/suppression list. Confirm opt-outs/bounces from Gmail. Never upload recipients, consent notes, raw Gmail MIME or private credentials to GitHub.
6. Send the single normal Sunday mailing with the authorized subscriber list, then read back the Gmail Sent MIME and compare the HTML to the release manifest. Report actual delivery separately from orchestration status. Do not resend automatically after an audit mismatch.

**Integration evidence (2026-11-10):** The GitHub smoke workflow successfully published a separately marked TEST-only branch `validated-sunday-smoke`. The connected GitHub action successfully fetched its actual HTML and manifest, and an owner-only `[TEST]` email was sent by Gmail using precisely that HTML, with zero CC/BCC. A read-back of the decoded Sent MIME confirmed normalized HTML byte-for-byte matches the validated file (four section strips, four image elements). No subscription recipients were contacted. This proves the GitHub-branch-to-Gmail handoff can work in the current interactive environment; it does NOT prove that the scheduled November 15 automation can execute fresh research, commit, wait for the CI run, fetch the matching production branch and send unattended. That remains unverified until the actual scheduled run completes all six stages. CI never sends email.

## Enforced five-stage release protocol — 2026-11-16

This protocol supersedes earlier direct-to-BCC delivery advice. **No subscribers are involved in staging.**

1. **Research/build**: Saturday prep is a draft; Sunday performs new research and compiles an unrehearsed current issue. Original organizer verification is still required.
2. **Automated preflight**: GitHub checks organizer evidence, final 24-hour freshness, links and three authentic, identity-reviewed HTTPS photographs. Any missing photo or HTTP error is a hard failure.
3. **Automated visual release**: The **actual release HTML** is rendered in Playwright Chromium with image loading ENABLED (390px light and dark, 650px light), requiring three complete natural-size photos, zero fallbacks and no horizontal overflow. A separate images-blocked responsive QA suite remains mandatory. Screenshots and both QA reports are retained in the GitHub Actions artifact; the validated production branch contains visual-qa.json and client-qa.json. This is browser rendering, NOT a real Gmail or Apple Mail client rendering guarantee.
4. **Private staging inbox**: Only after all gates pass, the connected Gmail automation sends the **exact production-validated HTML** once with a [TEST] subject to the owner only, To=owner, CC=[], BCC=[]. Look up an existing test before sending. Confirm the message was actually found in the owner's Inbox and that received MIME decoded HTML matches the validated production digest, plus the exact To/CC/BCC headers. Store the stage receipt privately in the automation's execution context, keyed by issue, source commit and HTML hash; **never on the public repository**. A Sent-only check is insufficient.
5. **Production delivery**: Only after the private inbox receipt passes, separately check suppression/consent and existing Gmail Sent for duplicates. Then, and only then, send the SAME validated production HTML once to the authorized subscriber list. Audit outgoing MIME; do not resend automatically after uncertain delivery.

The pure `release_authorization.py` policy and `test_release_authorization.py` regression suite require: a matching immutable source SHA, approved editorial/freshness gates, 3/3 live image checks, zero fallbacks, owner-only staging proof, matching received HTML digest and no duplicate production send. The implementation is fail-closed by design.

**Caveat**: GitHub CI does not have private Gmail credentials or subscribers, and therefore cannot itself prove the inbox step. The connected Sunday/Recovery automation owns stages 4–5; staging and production still need to succeed in an actual unattended Sunday run to count as fully proven. No third-party email-client preview service is connected. If Gmail Inbox read-back cannot be completed, production must remain unsent and the user receives an actionable warning.

## Test types and release evidence (2026-11-16)

Treat these as separate proofs, not interchangeable green checks:

1. **Functional/resilience CI**: fixed historical fixture checks HTML semantics, image-blocked legibility, two live archival images plus one honest fallback, deliberately broken-image failures, and MIME digest matching. Passing this does NOT certify the visual experience of a current issue.
2. **Owner-only visual E2E**: a newly researched issue declares `rehearsal: true` and `visual_test: true`, receives independent source/identity review for each Top 3 photo, and runs the real GitHub strict release gate with **three downloadable real images and zero fallback thumbnails**. Only the matching validated smoke HTML may be sent once to the owner, with a [TEST] subject, zero CC/BCC, after checking Gmail Sent for duplicates; then compare decoded Sent HTML to the release manifest hash. A fallback-only smoke run is a transport test, NOT visual E2E.
3. **Normal subscriber production**: the same three-photo and current event/editorial/freshness gate plus recipient/suppression checks, matching production manifest and verified Gmail Sent audit. Never let an owner test use the real BCC list.

Pre-send HTTP image checking detects currently broken source links, but cannot guarantee future email-client proxy behavior; Litmus or Email on Acid can provide representative Gmail/Outlook/Apple Mail screenshot QA, while Playwright is useful for deterministic browser/mobile/dark-mode regression (not a real email-client emulator). Keep image-blocked resilience tests despite production zero-fallback requirement.

## Discovery breadth and featured-image release policy (updated 15 November 2026)

Read the live source registry at `discovery_sources.json` (use live registry count dynamically (40 sources as of 2026-11-22), including Luma); derive the count dynamically rather than trusting older snapshots. Both Saturday preparation and independent Sunday research should consult the full registry, aim to review 12 distinct source domains across 5 cultural categories, and record which sites were actually visited and where coverage was impossible. Those are **research coverage targets**, not quotas for publishing events. Featured picks and listings are chosen by editorial fit, not artificially distributed evenly among venues. Direct organizer pages remain authoritative for details.

**Production quality safeguard**: Production releases invoke `delivery_guard.py --require-featured-photos` and reject missing / unverified Top 3 photographs. A production issue must have **three independently identity-reviewed authentic event/year images**, HTTPS links that successfully load and decode, and **zero** visual fallback tiles. First search organizer/artist event pages for a valid real photo; if the image cannot be verified, select a comparably strong event with a verified image for the Top 3, while retaining the original worthy event in the full lists. Never use unrelated stock/festival art, reuse expired verification timestamps, or fake image review. If three images cannot be found, **block subscriber delivery and report the issue**. Earlier text fallback support remains available for drafts and owner-only smoke tests, but must not become the normal BCC release. Running late on Sunday is preferable to compromising these checks; no extra resends are authorized.

## Final 24-hour freshness schema

```json
"final_review": {
  "checked_at": "2026-11-15T08:20:00+01:00",
  "organizer_source_url": "https://organizer.example/events/real-event",
  "event_status": "scheduled",
  "booking_status": "required_unverified",
  "notes": "Event still listed; remaining ticket inventory unavailable to verify"
}
```

Allowed `event_status`: `scheduled`, `rescheduled`, `cancelled`, `unknown`. Allowed `booking_status`: `available`, `sold_out`, `required_unverified`, `not_required`, `unknown`. If sold out, cancelled or rescheduled, correct the listing or move it to the unavailable section; don't silently send a stale recommendation. Timestamp alone does not prove the event was checked.

## Visual scanning cues — conservative and optional

The renderer now computes a short inbox preheader from **the real Top 3 titles**, instead of recycling the generic intro. Each event may display up to **two** quiet uppercase inline cues **above its title**, never colorful badges and never at the expense of event rows:

- `THIS WEEKEND`: requires issue `published_at` and timezone-aware `event_start` falling on the next Saturday/Sunday in Europe/Stockholm.
- `BOOK AHEAD` or `LIMITED PLACES`: requires explicit `booking_signal` (`advance_required` / `limited`) **and** confirmed booking evidence in `verification.booking.status`. Do not infer urgency from loose prose.
- `JUST FOUND`: requires `first_seen_issue` to equal the current `issue_number` and `new_discovery_verified: true`. Check historical newsletters before declaring it new.

If evidence is absent, render **no cue**, not an unverified assumption. The familiar black section strips and full-length editorial list remain unchanged. The sample issue lacks this structured metadata, so its layout remains visually stable and won't show synthetic cues.

## Privacy and consent

`.gitignore` ignores `private/`, `subscriber*.json`, `recipient*.json`, `consent*.json`, and `suppression*.json`. Pages CI fails if private subscriber files are accidentally tracked. Gitignore does not remove already committed data; use private external storage and provider access controls. `recipient_guard.py` requires explicit private consent information and opt-out exclusions. Do not fake consent or publish names/addresses. Existing mailto unsubscribe requires manual follow-through; one-click unsubscribe is not configured. Test emails: owner only, no CC or BCC.

## Screenshots

The email-client browser test stores six light/dark, 320/390/650-pixel, images-blocked screenshots as a **downloadable ZIP artifact** under GitHub Actions → run details → Artifacts. Artifacts expire after their retention period; they are not permanent files in the code repository.


## Executable private authorization boundary

Immediately before any subscriber send, execute `release_authorization.py` with
`--manifest`, `--issue`, `--html`, `--client-qa` and `--visual-qa` pointing at the
exact fetched production artifacts. Supply a JSON object on stdin with `owner`
and `receipt` (the private Inbox receipt described above). Keep these inputs
outside the public repository. Require exit 0 and `authorized: true`; inability
to execute or missing evidence blocks delivery. Never manufacture a receipt.
The command sends nothing. It recomputes outgoing HTML's digest, requires both
QA reports to be bound to that digest with all required scenarios passing, and
checks the matching owner-only Inbox receipt. Pass `--duplicate-sent` whenever
an existing production send was found; this must fail. Recipient suppression
and consent checks remain a separate mandatory private gate.

This guard is called by the private mail agent; it is not a transport-level lock
on the Gmail connector. End-to-end Inbox delivery remains unproven until an
actual authorized staged release completes. Do not equate historical-fixture CI
with that proof.

## Featured-image performance optimization (17 November 2026)

Before rendering a newly committed fresh issue, the no-email GitHub release gate now runs `optimize_issue_images.py` to create an **ephemeral** `release/optimized-issue.json`. It fetches each verified original featured photograph, tries smaller variants from the **same organizer or image-CDN host** (supported WordPress, Sanity and Next.js resize URL conventions), and compares decoded pixels to reject unrelated or cropped images. It prefers images around 1024px wide / 350 KB, and only switches when the source-hosted variant is sufficiently smaller and its identity matches. The committed source issue and original image metadata remain unmodified; successful variants retain `image_original_url` and optimization evidence. The renderer, delivery guard, browser QA, artifact issue JSON, and email must all use the **same optimized output**.

If a host cannot serve a matching smaller original, the pipeline keeps the verified original and emits the existing `large_image` warning rather than making a broken link or silently copying copyrighted imagery. A warning is **not** proof that the photo was optimized. An editor can select a different organizer-supported size where available. Separately, **explicitly authorized** hosted copies produced by `image_pipeline.prepare()` are constrained to roughly 1024×800 pixels with a JPEG compression budget; unapproved organizer photos are never rehosted automatically.

All existing three-photo identity, anonymous HTTPS image loading, zero-fallback, responsive, and images-enabled Chromium requirements remain in force. No-email regression tests cover URL host preservation, image similarity, fallback, and idempotence.

## Owner consent attestation and repeated-feature safeguard (22 November 2026)

The owner explicitly confirmed that **the existing seven previously mailed subscribers** gave consent through other channels. Treat that as the owner's current attestation for that unchanged recipient group; previous messages in Gmail are not required as supporting records. This attestation does **not** authorize adding a new subscriber or ignoring a later opt-out. Continue to reconcile the intended recipient group against the previous scheduled mailing, check suppression/opt-out and delivery-failure signals, exclude anyone who opted out, and verify there is no production duplicate before sending. Never publish recipient addresses or private consent records to this repository.

The final executable `release_authorization.py` remains separate from consent: it checks actual validated HTML, production manifest, source SHA, successful fresh editorial/image/visual gates, verified owner-only Inbox receipt, and duplicate-send status. It **must actually run and return exit 0 and authorized=true** in the private delivery environment; passing GitHub CI or reviewing the files manually does not count as its execution. Do not put a private receipt into GitHub CI or logs. If no execution environment can run this command with the matching private receipt, delivery remains blocked; give an explicit reason instead of treating it as an ambiguous failure.

The previously validated issue **005** reused all three TEST-006/TEST-008 Top Picks (and Aliquī was already in production issue 004). This was an editorial regression, not a photo-validity failure. From **issue 006 onward**, strict production CI reads `issues/featured-history.json` and fails repeated Top 3 selections using normalized title **or exact organizer event URL**. The history includes earlier owner-only highlighted emails as well as published editions. Seek authentic new images for genuinely fresh picks; move worthwhile repeats to **Worth reconsidering** instead. After each accepted release, append its Top 3 titles and exact organizer event URLs to the public **title-only (no recipients)** history. Do not retrofit or invalidate old test receipts by pretending they are a new issue.
