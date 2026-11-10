# Minimal Editorial delivery guard

The newsletter must use **one newly generated issue JSON and one rendered HTML file** for discovery, preflight, Gmail send and sent-message verification. Never use an old sent message as the source of a new issue.

## Required local pre-send sequence

```bash
python -m pip install 'Jinja2>=3.1.6,<4' 'Pillow>=11,<14'
python image_pipeline.py --data FRESH_ISSUE.json --report image-report.json --write
python render_minimal.py --data FRESH_ISSUE.json --output OUTGOING.html
python delivery_guard.py --data FRESH_ISSUE.json --html OUTGOING.html --manifest delivery-manifest.json --network
```

`--network` performs an anonymous HTTPS GET without cookies or credentials and decodes **each of the three selected featured photos**. Only supported image formats and dimension checks pass; it does **not** simulate Gmail's image proxy or prove every reader will see the image. Where an image fails, first re-source the exact same event's official artwork; then regenerate the issue and HTML, rerun preflight, and only then send. Never silently substitute generic stock photography.

A JSON result with `ready_for_delivery: false` is a **hard stop**. The preflight checks issue identity, date range, all four black section headers, every event URL, clickable full event row, clickable Top 3 image slots, three distinct featured URLs, old placeholder URLs, fallback count, 100 KB conservative HTML size limit, and actual remote image downloads when `--network` is enabled. A missing image may intentionally use an HTML placeholder with a warning; an invalid referenced photo is an error.

The manifest includes `html_sha256`, `data_sha256`, three featured image URLs, image GET results, event row count, issues/warnings, and an audit timestamp. The HTML digest ignores only MIME newline normalization / an added terminal newline.

## Gmail send and read-back

**The sender must send exactly the bytes of `OUTGOING.html`**, not regenerate HTML or use an old email message. Include a matching plain-text fallback, send only on the regular authorized schedule to the current To/BCC recipients (accounting for opt-outs), and do not use any BCC for tests, rehearsals, resends or backfills without explicit user approval.

After sending, read the Gmail Sent copy including raw RFC822 MIME. Save the raw MIME as `sent.eml`, then run:

```bash
python delivery_guard.py --manifest delivery-manifest.json --verify-sent-mime sent.eml
```

Exit code zero means the normalized sent HTML exactly matches the preflight manifest. Exit code one means a mismatch, missing HTML part, or invalid MIME. **A failure is NOT a reason to send the newsletter twice**; report it for investigation. Verify To/BCC/subject separately in Gmail metadata. The post-send check must not itself send emails.

If the automation execution environment cannot access Python, the repository's generated HTML file, or the Gmail raw MIME artifact, do not claim this full gate has executed. Inspect the actual outgoing and sent HTML to the extent possible, and explicitly report which verification stages were not possible.

## CI

`pages.yml` runs the delivery guard offline against the canonical sample and publishes `minimal-delivery-manifest.json`. The isolated `e2e-test-email.yml` additionally tests anonymous network image fetching, never sends to a recipient and publishes its own manifest artifact. Neither CI workflow sends mail.

Because the weekly scheduled automation can generate its own *fresh* issue outside GitHub, passing CI on the old sample doesn't prove the Sunday runtime invoked these gates. The scheduled sender must run the preflight against **its own newly generated issue**, not the static `guide_data.json` fixture.
