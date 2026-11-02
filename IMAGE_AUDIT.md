# November image audit — 2 November 2026

The original test email contained ten deliberate placeholder URLs. All ten visible image slots now have identified official imagery, spanning nine unique events/productions. No mockup event crops or generated event images are used.

| Event | Exact source and identity | Credit / qualification |
| --- | --- | --- |
| Adam Pultz & The Spectral Parrot | [Goethe event page](https://www.goethe.de/ins/se/de/ver.cfm?event_id=27371285), inspected in browser; its published JPEG variant loads and depicts the named artist | © Carina Khorkhordina; artist portrait, not a saxophone performance |
| Verkligheten | [Official production page](https://kontrar.se/en/show/verkligheten/) and its linked press photo; studio camera operator and performers | Julia Mård; [venue press policy](https://kontrar.se/en/press/) permits editorial use in related articles |
| Fight Symphony | [Organizer's Billetto event](https://billetto.se/en/e/fight-symphony-seungwoo-park-biljetter-2023053), inspected in browser; airborne martial-arts promotional photograph | Supplied on Galleri Steinsland Berliner event listing; no photographer name invented |
| SELF | [Fotografiska event](https://stockholm.fotografiska.com/en/events/self-artist-talk-and-opening); published SELF image combines a portrait and eye close-up | Fotografiska / SELF source attribution |
| Clown and Le Jeu | [Organizer's workshop page](https://jonassodergrenschool.com/workshops.html); source file explicitly identifies an archive workshop group in Caen | Rendered caption: **Organizer workshop archive (Caen)**. Not claimed to show the November Stockholm session. The same source verifies 3, 5, 10 & 12 Nov, 10:00–14:00, 3,200 SEK |
| Chamber / Cacti | [Royal Swedish Opera production page](https://www.operan.se/en/productions/chamber-cacti); Chamber production photograph of dancers on a blue-lit stage | Royal Swedish Opera / Chamber source attribution; not the mockup's cactus image |
| Borda | [Official event](https://dansenshus.se/en/program/lia-rodrigues-bra-borda/) and [specific press record](https://press.dansenshus.se/media/377195/borda-lia-rodrgues-foto-sammi-landweer1); figure surrounded by translucent material | © Sammi Landweer; press record labels **Media use** |
| Open Studio — Ink & Line | [Actual Tickster session](https://www.tickster.com/se/en/events/3k1f32bajd91041/2026-11-06/oppen-atelje); published ink portrait drawing | Organizer session artwork, not a photo of participants |
| Art of: Drag × Admira | [Official Fotografiska ticket page](https://tickets-stockholm.fotografiska.com/productDetail/240623?lang=en), which names November Nights and the Christmas edition; Admira in a white costume before a pink curtain | Fotografiska / Art of: Drag source attribution; this accessible source replaces reliance on the intermittently unavailable event-page image |

## URL integrity

Every enabled image was loaded and visually inspected. The exact source bytes have a recorded SHA-256 value, checked by live preflight. The two licensed press snapshots remain hosted on the guide's asset host; newly found official images are linked to their original hosts, with no new redistribution-license claim. `image_verified` means source and visual identity checked, not that all images share the press images' license terms. Credits and source attribution are kept distinct from license evidence.

Two failed candidates were caused by altered URLs, not absent pictures: the earlier Fight Symphony image had signed query parameters reordered, and a cached workshop image URL also differed from the organizer's actual tag. Exact DOM/HTML-published URLs, including their original parameter order and encoding, returned HTTP 200. Do not rebuild these URLs from a query dictionary.

The official archive qualification for the clown photo is preserved in alt text, its visible caption and `image_kind`. No image is presented as documentary evidence of future November attendance. Reconsideration rows do not render event images even when the underlying event also appears in Top 3.
