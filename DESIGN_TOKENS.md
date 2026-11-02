# Stockholm Guide — type and spacing tokens

Edit `design_tokens.json`, not scattered inline CSS values. `render.py` injects the token values into the fixed Jinja layout. This preserves email-compatible inline CSS without depending on unsupported CSS custom properties or an external framework in Gmail.

Typography: body 14/20, hero description 15/22, event headlines 18/23, feature headline 23/28, hero headline 31/36, section headline 31/40, metadata 12/18 (px font/line height). Spacing: 11–12px event row pad, 14px under section headings, 30px before sections, 22–24px hero padding. A restrained 4px rhythm guides choices rather than rigidly forcing every measurement onto a 4px grid.

Do not alter the approved masthead, image sources, event content, links, hero/supporting-card structure, or stacked sections. GitHub Pages builds the static preview from the canonical Jinja template on each main-branch deployment. Review both desktop and 320/390px mobile; browser checks are not a substitute for a Gmail client test.
