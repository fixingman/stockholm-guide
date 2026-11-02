# Minimal editorial design experiment

This is a **parallel layout** created from the first monochrome design option. Nothing in the existing newsletter's main renderer or automation is replaced. The new template uses the same `guide_data.json` and keeps every event, event date, description, price, booking status, venue and original link.

Design: bold three-line serif masthead, monospaced descriptor and date strip, thin horizontal rules, round black section dots, date-led Top 3, compact image-free event rows with **no arrows**, and the genuine approved `milestone_skyline.png` footer.

Files: `minimal_template.html.j2` and `render_minimal.py`. To preview locally: `python render_minimal.py --output minimal-preview.html`. A PR check also uploads a rendered HTML preview artifact.

It is deliberately a **separate experiment**: the old `template.html.j2`, `render.py`, `index.html`, existing GitHub Pages site and scheduled automation are untouched. A GitHub Pages side-by-side URL can be added later if the user chooses to promote this direction.
