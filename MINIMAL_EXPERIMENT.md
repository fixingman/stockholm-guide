# Minimal editorial design experiment

This is a **parallel layout** created from the first monochrome design option. Nothing in the existing newsletter's main renderer or automation is replaced. The new template uses the same `guide_data.json` and keeps every event, event date, description, price, booking status, venue and original link.

Design: bold three-line serif masthead, monospaced descriptor and date strip, thin horizontal rules, round black section dots, date-led Top 3, compact image-free event rows with **no arrows**, and the genuine approved `milestone_skyline.png` footer.

Files: `minimal_template.html.j2` and `render_minimal.py`. To preview locally: `python render_minimal.py --output minimal-preview.html`. A PR check also uploads a rendered HTML preview artifact.

It is deliberately a **separate experiment**: the old `template.html.j2`, `render.py`, `index.html`, existing GitHub Pages site and scheduled automation are untouched. A GitHub Pages side-by-side URL can be added later if the user chooses to promote this direction.


## Reader feedback and unsubscribe (no backend)

Three outlined email-safe `mailto:` links appear immediately above the original skyline: 👍 Like, 👎 Dislike, and Unsubscribe. A click opens the reader's email composer, prefilled with an issue-specific `Stockholm Guide #NNN | LIKE/DISLIKE` subject or the exact `Stockholm Guide | UNSUBSCRIBE` subject. The reader **must send the message**; opening a link does not record a vote or remove anyone. Replies arrive at `cankilicbay@gmail.com`, where subjects can be searched or counted in Gmail. This is intentionally not a one-click unsubscribe endpoint and doesn't supply a `List-Unsubscribe` header. Unsubscribe requests must be processed manually by removing the address from the weekly automation's BCC list before its next send. No external tracking or server is involved.


### Gmail compose prefill compatibility

Like and Dislike now use Gmail's HTTPS compose URL (`https://mail.google.com/mail/?view=cm&fs=1&to=...&su=...&body=...`) with an issue-specific subject and plain-text body. This avoids email apps that open an empty message when processing a `mailto:` URL with query parameters; it may open the Gmail website rather than the phone's default mail app, and requires the reader to be signed in and press Send. Unsubscribe continues to use `mailto:` so readers can identify their sending address. No vote is recorded simply by opening the link; only sent messages count.
