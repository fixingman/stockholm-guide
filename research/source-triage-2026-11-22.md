# Stockholm Guide — 49-source discovery examination

**As of:** 22 November 2026 (Europe/Stockholm)  
**Current published issue:** 005, 22 November–5 December 2026 (historical, already sent; do not edit).  
**Registry:** 49 active sources.  
**Raw anonymous sweep:** 2026-11-22T20:39:43.354532+00:00. All 49 source entrypoints attempted, 47 reachable, 2 blocked, 558 raw unverified candidate links.  
**Editorial status:** This is a complete **source-by-source triage**, NOT a verified complete per-event review of all 49. HTTP 200 and extracted links must not be counted as completed editorial review.

## Important results

- The missed-source problem is real: official public pages expose distinctive dated events not included in already-sent Issue 005 (Filmform, MDT, Cyklopen, Rönnells, FRIM, Luma, Cinemateket). Never retrofit Issue 005 or silently resend subscribers.
- Some registries overlap: Rönnells and FRIM advertise the same Blomsterunge date; FRIM also lists the Changing Landscape feature already in Issue 005; ThirdPlace's events are on Luma. Deduplicate by original event and date, not organizer count.
- Luma city / arts / tech / design entrypoints were all reached by HTTP, but raw HTML link extraction yielded too few event links; use public rendered browser/search and original Luma pages rather than concluding there are no events.
- Resident Advisor and NATTÖGA returned HTTP 403 to the Python source sweep. Their public RA pages and event details are discoverable via search/browser, so use that alternative and record the original blocked attempt truthfully.
- Pages with only past links or generic navigation (Värmeverket, Eken Marknad, Klubb Kaprifol, Richter Holtermann) cannot be deemed current just because HTTP 200. Explicitly report no verified upcoming programme if none established.
- Several festival/one-off sources have short seasons: Stockholm Film Festival closed around 22 November; Bonniers main gallery reopens 9 December; Lumen Project's later 2027 programmes are advance-booking leads, not within Issue 005.
- Primary event pages, dates, locations, eligibility, booking conditions and event identity require Sunday final verification. Avoid any made-up status or mass "reviewed" records.

## Selected missed leads for manual final verification

| Candidate | Date (2026 unless noted) | Original / public organizer source | Editorial assessment |
|---|---|---|---|
| MDT · A Study of Men | 26–27 Nov | [Open](https://mdtsthlm.se/kalender) | Dance and artist conversation; not in Issue 005 |
| Konsthall C · Who Stole the Lovely Grey Garden From the Goose? | 21 Nov–6 Dec | [Open](https://www.konsthallc.se/en/program/kif-2026) | Ongoing exhibition with near closing date |
| Mint · Indoors, Outdoors – Tbilisi | 17 Oct–18 Dec | [Open](https://m-i-n-t.se/en/guram-tsibakhashvili-2/) | Visit by appointment; not drop-in |
| Cyklopen · Open studio and library | 24 Nov, 18:00–21:00 | [Open](https://cyklopen.se/events/oppen-atelje-oppet-bibliotek/2026-11-24/) | Participatory creative option, recurring |
| Filmform · BUSINESS AS USUAL | 3 Dec | [Open](https://www.filmform.com/calendar/business-as-usual-screening-at-filmform-on-thursday-december-3rd/) | Experimental film; official date |
| FRIM · The Electrics / Nils Agnas | 27 Nov | [Open](https://frim-stockholm.se/en/events/the-electrics-nils-agnas) | Musical improv; check overlap with other festivals |
| Rönnells · Maya Bennardo and Leah Asher live | 26 Nov | [Open](https://ronnells.se/?events=maya-bennardo-och-leah-asher-live) | Intimate unusual concert |
| Rönnells / FRIM · Blomsterunge 50 år | 30 Nov–1 Dec | [Open](https://frim-stockholm.se/en/events/blomsterunge-50-ar) | Same performance across two sources; deduplicate |
| Luma · THE RED STRING | 28 Nov | [Open](https://luma.com/ypu61hv5) | Immersive art and fashion; registration unknown |
| Luma / ThirdPlace · Sweeney Todd Croquis | 26 Nov | [Open](https://luma.com/86iayxvq) | Participatory life drawing; original event on Luma |
| Cinemateket · Metropolis | 5 Dec | [Open](https://www.filminstitutet.se/sv/se-och-samtala-om-film/cinemateket-stockholm/program/) | Special screening; verify ticket status |
| ArkDes · Themed tour: Without Borders | 24 Nov | [Open](https://arkdes.se/en/calendar/themed-tour-without-borders/) | Guided architectural perspective |
| Resident Advisor · Mall Call at Stinsen | 27–28 Nov | [Open](https://ra.co/events/2520566) | RA index returns 403 to anonymous Python; individual public listing via alternate route |
| Resident Advisor · Bella Boo + Aasthma | 27 Nov | [Open](https://ra.co/events/2564565) | Verify original organizer listing and exact ticket conditions |
| Visit Stockholm · Roof of Reflection | 16 Nov–18 Dec | [Open](https://www.visitstockholm.com/events/roof-of-reflection/2026-11-16/) | Immersive art/science film, verify Wisdome host |
| Kollektivet Livet · Dekis Records Pop-Up | 24 Nov | [Open](https://kollektivetlivet.se/) | Free entry listed on venue homepage; unique social format |
| Nattljud · Jazz Lounge: Connecting with Erykah Badu | 28 Nov | [Open](https://nattljud.se/en/event/jazz-lounge-connecting-with-erykah-badu-with-anderson-waltman-boman-djeridi-quartet-feat-waltman-biocaf-tellus-2026-11-28) | Cross-index; verify at actual venue |
| OPI Lab · Course onsite sessions | 30 Nov–4 Dec | [Open](https://www.of-public-interest.com/opi-lab) | Course, may require prior application; do not treat as public drop-in |
| Fållan · Omah Lay | 24 Nov | [Open](https://www.fallan.nu/whats-on/omah-lay) | Larger concert, lower novelty priority |
| Bonniers Konsthall · Upcoming grants exhibition | 9 Dec opening | [Open](https://bonnierskonsthall.se/) | Outside issue window; gallery closed before 9 Dec |
| Selam · no confirmed new Stockholm date | After 22 Nov | [Open](https://selam.se/eng/events) | November 6 concert already passed; don't infer from 'coming soon' |
| NATTÖGA · no new current public date confirmed | Not established | [Open](https://ra.co/promoters/131068) | RA public page available via alternative search; automated probe 403 |

## All 49 registered sources: raw index probe evidence

The last column is an **unverified link from the source index**, not an event acceptance decision. Some entries will be navigation or historical: that is precisely why editorial follow-through is required.

| # | Source | HTTP probe | Raw links | Example unverified link |
|---:|---|---|---:|---|
| 1 | Reimersholme Hotel | Reachable | 15 | [Candidate link](https://reimersholmehotel.se/event/julbord/) |
| 2 | Fylkingen | Reachable | 12 | [FÖRENINGEN FYLKINGEN EMS Kursavslutningskonsert Tuesday 24 November 2026 19:00 FREE](https://www.fylkingen.se/en/events/ems-avslutningskonsert) |
| 3 | Fotografiska Stockholm | Reachable | 18 | [Exhibitions](https://stockholm.fotografiska.com/en/exhibition) |
| 4 | MDT Moderna Dansteatern | Reachable | 7 | [EN](https://mdtsthlm.se/en/calendar) |
| 5 | Konträr | Reachable | 18 | [Boka plats](https://kontrar.se/forestallning/kontrar-julshow-3/) |
| 6 | Weld | Reachable | 5 | [Arkiv](https://www.weld.se/program/past/sv) |
| 7 | Dansens Hus | Reachable | 10 | [Kalender](https://dansenshus.se/program/) |
| 8 | Kulturhuset Stadsteatern | Reachable | 18 | [Utställningar](https://kulturhusetstadsteatern.se/utstallningar) |
| 9 | Accelerator | Reachable | 9 | [Utställningar](https://acceleratorsu.art/utstallning/) |
| 10 | Bonniers Konsthall | Reachable | 10 | [Utställningar](https://bonnierskonsthall.se/utstallningar/) |
| 11 | Färgfabriken | Reachable | 1 | [Lokal och event](https://fargfabriken.se/sv/lokal/) |
| 12 | Stockholm International Film Festival | Reachable | 6 | [www2.stockholmfilmfestival.se](https://www2.stockholmfilmfestival.se/) |
| 13 | Sound of Stockholm | Reachable | 6 | [Festival Pass](https://secure.tickster.com/sv/u0457bk67t0b9be/products) |
| 14 | ANDETAG | Reachable | 18 | [Find Tickets](https://www.andetag.museum/en/stockholm/) |
| 15 | Visit Stockholm events index | Reachable | 18 | [To main content](https://www.visitstockholm.com/events/) |
| 16 | Konsthall C | Reachable | 3 | [EXHIBITION 21 NOVEMBER–6 DECEMBER 2026 Who Stole the Lovely Grey Garden From the Goose?](https://www.konsthallc.se/en/program/kif-2026) |
| 17 | Index — The Swedish Contemporary Art Foundation | Reachable | 8 | [Exhibitions](https://indexfoundation.se/exhibitions) |
| 18 | Mint Stockholm | Reachable | 18 | [SV](https://m-i-n-t.se/program/) |
| 19 | Lumen Project | Reachable | 18 | [Lumen Project / Spring 28.2 Upcoming Sunday, February 28, 2027 · 15:00-21:00 · Eric Ericsonhallen · Stockholm](https://lumenproject.se/events/lumen-project-spring-282/) |
| 20 | Fållan | Reachable | 18 | [What's on](https://www.fallan.nu/whats-on) |
| 21 | Nattljud Stockholm | Reachable | 18 | [SF Folk Music and Dance SKEPPSHOLMENS FOLKHÖGSKOLA/FÖRENINGEN FOLKMUSIKHUSET](https://nattljud.se/en/event/folk-music-and-dance-skeppsholmens-folkh-gskola-f-reningen-folkmusikhuset-2026-11-22) |
| 22 | Resident Advisor — Stockholm | HTTP blocked | 0 | No useful dated link surfaced in probe |
| 23 | Evenemang Stockholm | Reachable | 18 | [Candidate link](https://www.evenemangstockholm.se/november) |
| 24 | Slakthusguiden | Reachable | 18 | [Where to eat before and after the concert in Slakthusområdet?](https://slakthusguiden.se/en/guide/fore-och-efter-konserten) |
| 25 | Luma — Stockholm public events | Reachable | 4 | [Discover Events](https://luma.com/discover) |
| 26 | Meetup — Stockholm | Reachable | 18 | [Rust Meetup @Lovable Thu, Nov 26 · 5:30 PM CET by Stockholm Rust](https://www.meetup.com/stockholm-rust/events/317161063/?eventOrigin=city_most_popular_event) |
| 27 | Tickster — Stockholm calendar | Reachable | 18 | [Hoppa till innehåll](https://www.tickster.com/se/sv/events/in/stockholm) |
| 28 | Stockholm Events — cross-platform index | Reachable | 4 | [Visit Stockholm](https://www.visitstockholm.com/see-do/events/) |
| 29 | Kollektivet Livet | Reachable | 18 | [Hoppa till innehåll](https://kollektivetlivet.se/evenemang-biljetter/) |
| 30 | Richter Holtermann | Reachable | 1 | [Past Exhibitions](https://www.richterholtermann.com/gallery) |
| 31 | Stadsgårdsterminalen | Reachable | 18 | [Hoppa till innehåll](https://stadsgardsterminalen.com/program/) |
| 32 | Bio Fågel Blå | Reachable | 18 | [Hoppa till innehållet](https://biofagelbla.se/program/) |
| 33 | Of Public Interest (OPI) Lab | Reachable | 1 | No useful dated link surfaced in probe |
| 34 | NATTÖGA | HTTP blocked | 0 | No useful dated link surfaced in probe |
| 35 | The Well Zone | Reachable | 4 | [Private sessions](https://www.thewellzone.se/private-sessions) |
| 36 | Eken Marknad | Reachable | 0 | No useful dated link surfaced in probe |
| 37 | STHLM Baile | Reachable | 18 | [Kalender](https://debaser.se/kalender) |
| 38 | Värmeverket | Reachable | 14 | [28 aug Ammouris Festival Linje 13 presenterar Ammouris Festival – två dagar fyllda med konst, musik, kreatörer och gemenskap.](https://www.varmeverket.com/evenemang/ammouris-festival-2026-08-28) |
| 39 | Klubb Kaprifol | Reachable | 0 | No useful dated link surfaced in probe |
| 40 | Selam Music | Reachable | 7 | [Candidate link](https://selam.se/events/music/Waylon_Thornton_-_01_-_Bronco_Romp.mp3) |
| 41 | Cyklopen Stockholm | Reachable | 8 | [Meny](https://cyklopen.se/kalender/) |
| 42 | Rönnells Antikvariat | Reachable | 18 | [Boksläpp av Dragomanen 2026: Judiska minoriteter i Mellanöstern](https://ronnells.se/?events=bokslapp-av-dragomanen-2026-judiska-minoriteter-i-mellanostern) |
| 43 | Filmform — The Art Film & Video Archive | Reachable | 8 | [HIDE](https://www.filmform.com/calendar-upcoming/) |
| 44 | FRIM — Association for Free Improvised Music | Reachable | 18 | [Concert Calendar](https://frim-stockholm.se/en/events) |
| 45 | Moderna Museet Stockholm — Calendar | Reachable | 18 | [På svenska](https://www.modernamuseet.se/sv/stockholm/kalender/) |
| 46 | ArkDes — Events and Public Programme | Reachable | 17 | [Exhibitions](https://arkdes.se/en/exhibitions/) |
| 47 | Cinemateket Stockholm — Swedish Film Institute | Reachable | 18 | [Stöd till filmprojekt baserat på bruttobiljettintäkter - PRS](https://www.filminstitutet.se/sv/sok-stod/produktionsstod/ovriga-stod/publikrelaterat-stod-prs22/) |
| 48 | ThirdPlace Stockholm — ArtCafe & SoberBar | Reachable | 2 | [Discover Events](https://luma.com/discover) |
| 49 | Startskott — Stockholm Cross-Platform Events | Reachable | 18 | [Alla event](https://startskott.com/) |

## Next editorial handoff

1. Use `source-audit:research/source-probe.json` to cover **all 49 source IDs**, beginning with missed independent and participatory opportunities. Reinspect original public event pages and dates for the new upcoming 14-day issue window, rather than copy prior Issue 005 dates.
2. Record a truthful `issues/next-draft.json:research_coverage.source_scans` per ID, including Luma city and all category URLs; then carry forward and recheck into the next issue's production `issues/current.json`. A source checked with no worthwhile event still counts as reviewed; a crawler-probed source does not.
3. Retry blocked sources with documented alternate routes. Don't fabricate reviewer identity or event facts; check final URLs and booking only against original organizer.
4. Source-coverage production gate in `source_coverage.py` is enforced for Issue 006+, on top of the photo, final freshness, recipient and mail safeguards.

**Data provenance:** current GitHub registry and source-audit sweep, plus direct public organizer/calendar web lookups on 22 November 2026. This file does not claim a genuine human/AI assessment of each full indexed event listing.
