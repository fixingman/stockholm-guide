# Featured image workflow

Required for every new Stockholm Guide edition, before HTML rendering.

1. For **each of the three featured events**, search the exact event title, year and Swedish spelling. Visit the exact official organizer/event page (not the venue homepage), then linked festival, artist, press and ticketing pages. Inspect embedded images and og:image.
2. Prefer official photography or same-event promotional artwork. A poster is fine if captioned as artwork, never misrepresented as a documentary photograph. Never substitute last year's festival poster, unrelated stock images, an old image of a different edition, or AI-generated depictions.
3. Verify identity, exact edition/date, HTTPS image URL, successful image response, cropping, attribution and **permission to use/embed**. Public display alone does not establish reuse rights. Only host assets in this repository when reuse permission allows it. Do not modify signed URL query parameters or assume third-party hotlinks will stay available.
4. For each verified picture, provide all of: `image_verified: true`, `image_url`, `image_source_url`, `image_alt`. Add `image_cache_file` only when the named asset already exists in the approved assets directory and corresponds to the exact event. Keep credit and qualifiers in alt/records.
5. When no safe image is found, omit image fields and keep the neutral placeholder, **reporting which event needs an image**. Never invent a verified flag. Image selection is by event identity, never by list position.

Pre-send: Run `python render_minimal.py --data FRESH_ISSUE.json --output EMAIL.html --asset-base-url https://fixingman.github.io/stockholm-guide/assets`. Its output reports Top 3 verified image coverage and missing-image titles; rendering rejects broken/incomplete verified-image metadata and missing cached files. A missing image does not prevent sending a valid edition.

Audit notes: `IMAGE_AUDIT.md`. In sample edition #002 the previously authorized Verkligheten production press photo is restored; the other two remain placeholders until individually verified, including reuse permissions.
