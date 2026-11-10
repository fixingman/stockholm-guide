# Sunday release integration, subscriber privacy and scanning cues

## Status: staged, not yet proven on unattended Sunday

GitHub CI and the ChatGPT Sunday automation run in separate environments. A successful build from the frozen `guide_data.json` sample must NOT be represented as a fresh Sunday delivery. The scheduled Nov 8 automation recorded a failed run despite a message being visible in Gmail Sent, so actual orchestration remains a risk.

**New production gate**: `.github/workflows/weekly-release-gate.yml` runs automatically when **`issues/current.json` is committed**, or can be manually dispatched. The trigger intentionally does NOT run on a workflow-file change with no fresh issue.

For a new issue:
1. Research all 14-day events and build `issues/current.json`. It must contain only public editorial event information, never subscribers or consent records. Include `issue_number`, `date_range`, `published_at`, Top 3 image metadata, full listing, event verification, and final review.
2. Revisit each event's actual organizer listing **within 24h before sending**. Record `final_review` with `checked_at`, `organizer_source_url`, `event_status` and `booking_status`. This is a factual editorial action performed by the editor/research assistant, NOT an automatic inference from a HTTP 200.
3. Commit fresh `issues/current.json`. Wait for the **Validate fresh Sunday newsletter (no sending)** GitHub run for that commit. It runs the actual Minimal Editorial renderer and `delivery_guard.py --network --editorial-strict --freshness-strict`. It rejects old sample issue #002, missing verified facts/identity reviews, stale event review, unavailable or cancelled events in available sections, broken remote images, missing links and unfit layout.
4. Read the run's `verified-sunday-issue-html-and-manifest` artifact. It contains `outgoing.html`, `delivery-manifest.json`, `client-qa.json` and `issue.json`. **Only that exact checked HTML** is eligible for a regular authorized send; verify issue ID, publication window and SHA-256 digest first. Do not send HTML from a previous Gmail message or a static preview.
5. Independently check the **private** subscriber/consent/suppression list. Confirm opt-outs/bounces from Gmail. Never upload recipients, consent notes, raw Gmail MIME or private credentials to GitHub.
6. Send the single normal Sunday mailing with the authorized subscriber list, then read back the Gmail Sent MIME and compare the HTML to the release manifest. Report actual delivery separately from orchestration status. Do not resend automatically after an audit mismatch.

**Important execution boundary:** The ChatGPT automation is a text-instruction workflow, not automatically wired to check out files, start GitHub builds, retrieve artifacts and compare Gmail MIME. The script infrastructure is now ready; real unattended integration is **not verified until a Sunday automation run completes all six stages**. If the runtime cannot produce or retrieve artifacts, report the blocker and do not claim the release gate passed. CI never sends email.

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
