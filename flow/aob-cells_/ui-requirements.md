# Requirements: the cells chart and video

**Version:** 0.18 · **Date:** November 24, 2026 · **Status:** requirements only, agreed with Mukund before coding. The data is specified in `requirements.md`; this document specifies what is drawn from it. The look and the event animations follow the storyboard (`ui/storyboard.html`).

---

## 1. Purpose and scope

- **U1. Two outputs, one engine.** An interactive web page and a short video for LinkedIn and X are drawn by the same code from the same data, so they never differ.
- **U2. The whole run, or one Prime Minister's term.** The page plays the whole run from 15 August 1947 (`timeline.json`: 392 frames, 379 events, 33 salient; the years before the Rules of 14 January 1961 from the cabinet lists, U24b), or one Prime Minister's term, chosen in a row of chips above the stage (it scrolls sideways; a fading edge and ‹ › arrows show there is more, and move it): "All", then one per term in order, each with the photo, the name, the years and the number of changes. A repeated term is its own chip (Indira Gandhi 1966–1977 and 1980–1984; Vajpayee 1996 and 1998–2004); a term with no change stays, faded. The link names the term (`#pm-manmohan-singh`, `#pm-indira-gandhi-1980`). Before 2004 the readings of the scanned gazettes still have known gaps (`review/states-issues.md`), noted under the stage. A cell's size is scaled to the whole run's largest frame in every term, so sizes compare across terms (864 subjects in 1961, 1,846 at most).
- **U2a. A term** is cut from the whole run in the page: it opens on the government as it stood on the day of swearing-in, plays the changes notified in the term (from the day of swearing-in to the day before the next Prime Minister's), and ends on the day before the next one, with a card for its last seconds: "Under Manmohan Singh: 42 → 51 ministries · 4 created, 2 abolished, …". A change belongs to the term in which it was notified, even if the government before decided it. In the whole run, a thin band under the scrubber marks the terms; clicking one plays it.
- **U3. Top-level units only.** A cell is a top-level unit of the First Schedule (requirements R1). Departments inside a ministry are not drawn.
- **U4. English only** for now. The data keeps the Hindi names for later.

## 2. The engine

- **U5. Deterministic.** The animation is driven by a timeline clock, not the wall clock: fixed physics steps (60 a second) and seeded randomness. The same time `t` always draws the same picture, live or frame by frame.
- **U6. Seekable.** Play, pause, scrubbing and jumping to a year or an event are all "go to time t".
- **U7. One script, two directors.** A timeline (§9) lists every year's events with their timing. The **Full run** and the **Story** (§3) are two ways of timing the same script.

## 3. The two views

- **U8. Full run.** The cell chart alone, as one continuous animation from the first frame to the last: every year and every event, at a steady pace of about 1.5–2 seconds a year, with no stops. The camera stays wide. Each event plays its animation where it happens, with a small badge beside the cell ("+ AYUSH", "Coal & Mines splits") instead of a caption card, so the whole government is seen changing over the years.
- **U9. Story.** The same run, but time slows at the **salient** events: the camera eases in, a veil fades the other cells, and a caption card names the change. Between salient events, the years pass quickly with small badges, as in the Full run.
- **U10. Salient events** are chosen by a person in the corrections file (`cells-names.yml`), each with an optional caption of its own. The rest are captioned from the data (requirements R12).
- **U11. Year by year.** Events are grouped by calendar year. Within a year they play in date order; events on the same date play one after the other, in the order of requirements R8.
- **U12. Small changes** below a good share resize a cell smoothly at the year's change, without a badge (requirements R9).

## 4. The web page

| Area | What it shows |
|---|---|
| Header | A slim black bar: orgpedia's mark and wordmark, then "Evolution of Ministries"; no other links, no breadcrumb and no introduction, so the stage and its controls fit on a laptop screen without scrolling. Under it, one line: the page title, and "All ministries and their histories →" |
| Left: event list | As tall as the chart's card beside it. Its count and a "Show ▾" menu of checkboxes, one per kind of change (§4a), then the search, then a scrollable list of every event, grouped by year, each with its kind badge and caption. The current event is highlighted and the list scrolls with the animation. Clicking an event jumps there. Salient events are marked. |
| Centre: stage | The cells (§6) |
| Stage, top left | The year, large and faint; under it, very faint, the count of units: "44 ministries · 7 departments & offices" |
| Stage, top right | "In office" (§8): the President, the Prime Minister and the Cabinet Secretary as three small circles |
| Stage, bottom | The caption card (Story), or the badges (Full run) |
| Under the stage | Play/pause, the timeline scrubber (as long as the row allows) with year ticks and a mark for each event, the clock, and a button that reads as one ("⚙ Story · 1× ▾", tinted blue) opening a menu with the Story / Full run toggle, the speed and sound on/off (off by default). The previous or next change is the ← → keys; there are no buttons for them |
| Under the controls | One line: "Size of a cell = the number of subjects the Allocation of Business Rules give it", the Rules linking to cabsec.gov.in/documents/rules-of-business, and "About the data", folded: a short list (what a subject is, the sector colours, before 1961, before 2004, the terms, the sources of In office). There is no other chart: the cells are the whole picture. |
| Footer | As on orgpedia.in: the black bar with the wordmark, Disclaimer, Report an error, View on GitHub, CC BY 4.0 |

- **U13. Hover or tap a cell:** its full name, subjects, sector, and its names over time.
- **U14.** The page works on a phone: the event list moves under the stage, the "In office" strip is hidden, and the caption card is one line (cut with "…").
- **U15. Hosting.** A self-contained static page, with no server. For now a published page; later on orgpedia.in.

## 4a. Search and the kinds shown

- **U37. Search.** A search box above the event list finds every unit whose names, at any time, hold all the words typed ("education" finds HRD; "jal shakti" finds Water Resources). It shows:
  - the units found, each with its years ("Planning Commission (2004–2015)", "Defence (since 2004)");
  - the number of matches, "2 of 7": each shown change that involves a unit found, in time order, or the unit's first appearance if it has none;
  - ▲ / ▼ (and Enter / Shift+Enter) to go to the previous or next match, which moves the playhead there.

  While searching, the units found are lifted above a veil, and the event list shows only their changes.
- **U38. The kinds shown.** In the "Show ▾" menu of the Changes panel, a checkbox per kind of change (merged, absorbed, split, spun off, created, abolished, moved, renamed, size changes) and "In office", each with its count. A kind turned off is **not shown**, but it still happens, because the cells must stay true to the Rules:
  - it plays quietly and faster: no badge, caption, zoom, ring or sound; a renamed label changes without the scramble;
  - it leaves the event list, the scrubber's marks and the previous/next steps;
  - in the Story, a salient event of a hidden kind gets no pause;
  - a hidden change does not hold up a shown one on the same unit.

  "In office" turned off hides the three circles and their lines in the list.
- **U39. Quiet years pass quickly.** A year with no shown change takes 0.5 seconds in the Full run and 0.35 in the Story, instead of 1.8 and 1.05, so hiding kinds shortens the run.
- **U40.** The choice of kinds is remembered in the viewer's browser. The video uses its own fixed choice.

## 5. The video

| | |
|---|---|
| Size | 1080 × 1350 (4:5). The same file is posted to LinkedIn and X. A 16:9 version (1920 × 1080) can be rendered from the same timeline if wanted. |
| Length | Under 2 minutes 20 seconds (X's limit for accounts without Premium). Target 60–90 seconds. |
| View | The Story (§3), from January 2004 to the latest amendment |
| Frame rate | 30 frames a second |
| Format | MP4: H.264 video, AAC audio |
| Captions | Burned into the picture, since both feeds autoplay muted; an `.srt` file from the same timeline too |
| Sound | The event sounds (§7) only, rendered from the timeline so they land on the frames. No music. |
| Not in the video | The event list, the controls and the hover |

- **U16.** Fonts are larger and margins wider than on the web, so the video reads on a phone. Text stays inside a safe area away from the edges.
- **U17.** The video opens with a title card (the question it answers) and ends with a card naming the source and orgpedia.in.

## 6. The look

- **U18. Professional, calm, trustworthy, modern.** orgpedia's page style (Tailwind's defaults): light grey page (`#f3f4f6`), white cards with grey-200 borders, the system sans-serif font, headings `#111827`, text `#333333`, and blue-600 (`#2563eb`) for buttons, links and the caption's edge.
- **U19. Sectors** colour the cells, in muted mid-tones. White labels pass 4.5:1 contrast on every one:

| Sector | Fill | Membrane |
|---|---|---|
| Economy & industry | `#3D5A80` | `#2F4663` |
| Infrastructure & energy | `#5B5788` | `#46436A` |
| Land, water & rural | `#4A7766` | `#395C4F` |
| Social & culture | `#9C6B3F` | `#795331` |
| Security & external | `#93525A` | `#723F46` |
| Science | `#3C7480` | `#2E5A63` |
| Centre of government | `#5A6472` | `#464E58` |

  Each unit's sector is kept in the corrections file and set by a person. A spin-off or a split takes its parent's sector unless the file says otherwise.
- **U20. A cell's area is its number of subjects:** radius = k·√subjects, with a smallest radius so that a unit of 0–2 subjects (the Ministry of Planning, NITI Aayog) is still a visible dot.
- **U21. The cells are soft:** a gooey blob with a darker membrane, a faint nucleus and a faint highlight. They breathe slightly and jostle in a loose physics field, clustered by sector.
- **U22. Labels** are the short name ("Ministry of" and "Department of" left off; "and" as "&"), kept in the corrections file where the data's name is long. A label sits inside its cell when it fits; a cell in focus that is too small gets its label beside it.
- **U23. Focus:** a veil fades the other cells and the camera eases in, zooming no more than 1.75×.

## 7. The event animations

| Event | Animation | Sound |
|---|---|---|
| split | Mitosis: the cell stretches, pinches at the waist and snaps into two, each with its own nucleus | snap |
| spun off | Budding: a bump grows on the parent and pinches off | snap |
| merged | Two cells drift together, a bridge forms, they flow into one | squelch |
| absorbed | The big cell engulfs the small one, which fades inside it | squelch |
| moved | A droplet travels along a short bridge from one cell to the other; both resize | soft pop |
| born | Pops in from a speck with a springy overshoot and two rings | rising blip |
| ended | Trembles, then bursts into droplets | burst |
| renamed | The label scrambles into the new name; a ring pulses | chime |
| grew / shrank | A spring to the new size, with a jelly wobble | soft swell |

- **U24a. The safety net.** At every frame the stage holds the frame's units, whatever the events say: a cell whose unit is not in the frame fades out; a unit with no cell fades in; while an event on the unit is still playing, it is left to the event. A unit's absence, not its size, decides it: a unit with 0 subjects (the Ministry of Planning) stays, a dot. Checked by a test: with no event playing, the cells on stage are the frame's units, in both periods and both views.
- **U24.** At a re-issue (requirements R11: 1985, 2004), one caption first ("Re-issue", its date, and what it did, from `reissue_notes`), held for about 3 seconds in both views, then its structural changes; its size changes are plain resizes.
- **U24b. Before the Rules (requirements R12).** The run from the start begins in 1947. While the date is before 14 January 1961, the count under the year adds "sizes approximate". At 14 January 1961 one caption, "The Rules begin", says that sizes are counted from here, held like a re-issue's (U24). Before 26 January 1950 the first circle of the In office strip is the Governor-General (U25); there is no Cabinet Secretary before February 1950, so that circle is empty.

## 8. In office

- **U25.** Three small circles, top right: the **President**, the **Prime Minister** and the **Cabinet Secretary** in office on the frame's date. Each has a photo, the name and the title. The three in office today are shown in colour; those before them in greyscale, to match the palette. A photo is cropped near its top, where the face is, unless `people.json` gives it a `crop`. When the office-holder changes, the circle crossfades, and the change is listed in the event list (not as a cell event).
- **U26.** The office-holders are kept in their own file, `src/people.json`, not in `cells.json`, so that the AoB data stays the Rules alone. The names and dates come from the official lists (pmindia.gov.in, presidentofindia.gov.in, cabsec.gov.in), each named in the file:

```json
[{"office": "pm", "name": "Manmohan Singh", "from": "2004-05-22", "to": "2014-05-26", "image": "people/manmohan-singh.jpg"}]
```

- **U27.** Until a photo is given, the circle shows the person's initials. Photos are supplied by Mukund, from sources he has the right to use; the build does not fetch them.

## 9. The data the UI reads

- **U28.** `cells-2004.json` (later `cells.json`), as in requirements §6.2, with these additions:
  - each unit's **kind** (ministry, department, or secretariat/office), from its First Schedule item, for the count under the year;
  - each unit's **sector** and **short name**, from the corrections file.
- **U29.** The corrections file (`cells-names.yml`) names units by their name as the data prints it, not by id, so one file serves the 2004 build and the whole run. It holds `sectors` (each sector's list of names), `short` (a label per long name), and `events`, keyed `"<series> <kind> <short name>"` (as in `events[].key`), each `keep`, `drop`, another kind, or `{salient: true, caption: …}`. A call that names no event is listed in the review (`unused_calls`); a unit with no sector too (`no_sector`).
- **U30.** A build step (`make timeline`) writes `ui/timeline.json` (from 1947, with `src/prologue.yml` in front of the Rules; the page cuts the terms from it, so `ui/timeline-2004.json` is no longer read): per year, its events in order, the frames' sizes, the salient flags and captions, and the in-office changes. The web page and the video both read it.
- **U31.** `people.json`, as in §8.

## 9a. Links to the documents

Every change on the page leads to the document that made it, and every cell to the Rules it stands for. Both pages open in a new tab, so the animation keeps its place. Nothing here is drawn before 1961: the cabinet lists have no pages.

- **U41. The amendment behind a change.** Under each change in the event list, a line: "Amendment #106 ↗ · change 3, 5". "Amendment #106" (the series) links to the amendment page; each "change n" to that change on it (`/amend/106/#c3`, U48). A change is one of the change objects detected from the document (its op: insert, omit, replace, substitute_text, renumber); the ones listed are those whose target or result touches the event's units (a heading or a subject), found through their eIds in `changes.json`. If none does, only "Amendment #106". At a re-issue the line says "Re-issue #174". In the Story, the caption card of a change links to its amendment too ("Amendment #106 ↗").
- **U42. A cell leads to its ministry.** Clicking any cell pauses the animation and opens a small card by it: its name, its years and its subjects now, and three choices: **Follow it here** (U66), **Its history ↗** (its ministry page, §9b) and **Its subjects in the Rules ↗** (the Rules as they stood on that date, at its section of the Second Schedule: `/rules/106/#U004`). Before 1961 there is no Rules page, so that choice is left out. The hover says "Click: follow it, its history, its subjects".
- **U66. Following a ministry.** "Follow it here" turns the chart into that ministry's own run (U54) in place, within the run in hand: the whole run, or the Prime Minister's term chosen (U2), so "Culture under Manmohan Singh" can be watched. A chip above the stage says "Following Ministry of Culture · 6 changes here" (or "no change in this run"), with its history link and "✕ Stop following", which goes back to every ministry at the same date. Choosing another term keeps the ministry followed. The search results have a "Follow" button by each ministry found. The link names both: `#pm-manmohan-singh&follow=culture`. In the Changes list, each change names its ministries, each linking to its history; beside the page's lede, a link to all the ministries' histories.
- **U43. The amendment page: header.** "Amendment #106", the S.O. number, the date issued and the date in force, a link to the PDF on cabsec.gov.in, the previous and next amendment, and the Rules before and after it (links to U47). Under it, the count of its changes: the total, how many to the First Schedule and how many to the Second (and to the Order's rules, or not placed), and how many were applied.
- **U44. The amendment page: the pages and the changes.** For each page of the document, two panels side by side:
  - left, the page image, with each change's words boxed and numbered (from the word boxes in the extracted data);
  - right, the change objects on that page, in order: the number, the clause ("2(a)(i)"), the op, what it cites (schedule, entry), its new text, and what it did to the Rules (before → after, and whether it was applied, from `changes.json`).

  Hovering or clicking a change on either side marks it on the other. Each change has its anchor (`#c3`). On a phone the panels stack, the image first.
- **U45. How the document was read.** Under the pages, every edit made to get the data from this document, in order, each with who and when: the word edits (before → after), the edits to fields and relations, the inference rules applied to its changes (the rule, its status, its note), and its known issues. From the task's `conf/<file>.edits.yml`, the states' `decisions.yml` and `inferences.json`, and `known.yml`.
- **U46. Re-issues** (174, 1985; 271, 2004) are not amendments: their page has the header (U43) and the changes they made, says that it is a re-issue, and shows no page images.
- **U47. The Rules page.** `/rules/N/`, the Rules after amendment N (`/rules/0/`: the Rules of 1961 as made):
  - a header: "The Rules after amendment #N", the dates it was in force ("In force from 27 September 1973 to 9 November 1973", "… to today", "… replaced the same day"), the amendment that made it and the one that replaced it (links), the previous and next version, and a link on cabsec.gov.in to the consolidated Rules it was built from;
  - a note that the text is inferred, not official: worked out by applying the amendments (#k to #N), as read from the gazettes, to the consolidated Rules (or the Rules of 1961), so that where an amendment could not be placed it may differ from the real text;
  - the whole First Schedule, numbered as printed, each ministry, department and office linking to its section of the Second Schedule;
  - the whole Second Schedule, each unit's section with its numbered subjects. A section's anchor is the cell's id (`#U004`), which lasts through renames, so the same link works in every version; its eId works too. Each heading has a link mark to copy.

  No page images.
- **U48. The pages are written out.** `make site` writes each amendment page (`/amend/<n>/`) and each Rules version (`/rules/<n>/`) as its own HTML file, with its text in the HTML (U58), so it can be found and shared; the page images are separate files (`pages/<file>/<page>.webp`). What needs script (the marks linking image and changes, U44) is added in the browser. The query links of U41–U42 are these paths: `/amend/106/#c3`, `/rules/106/#U004`.
- **U49. The page images** are made from the PDFs by `make page-images` (pdftoppm, then WebP), about 1,400 pixels wide; the build does not fetch the PDFs.
- **U50. Size.** The whole site stays under GitHub Pages' 1 GB: about 2,000 page images at about 100–120 KB (≤ 250 MB); the 387 Rules pages, written out, about 200 MB (each about 0.5 MB, with no styles or scripts repeated inline); the amendment, ministry and term pages and the photos a few MB. If the total nears 700 MB, the Rules pages before 2004 are written for the versions the site links to only.

- **U51. One look.** Every page of the site (the chart, the amendment, Rules and ministry pages, the index) follows orgpedia's style (U18): its black header bar with the wordmark and the blue rule under it, the breadcrumb, the light grey page and white cards, the system font, the same colours for text, links and the sectors (U19). Dates are written "14 February 1969"; numbers as in the documents.

## 9b. Ministry pages

One page for each top-level unit (requirements R1), about 180, telling its story through its own changes. Departments inside a ministry have no page (later). Built by `make site` (`cells/ministry.py`): U52–U57a.

- **U52. Named by today's name.** A unit's page is named and addressed by its name today, or its last name if it was abolished: "Ministry of Education", `/ministry/education/`. Under the title, its earlier names with their years: "Human Resource Development 1985–2020 · Education and Social Welfare 1971–1985 · Education 1947–1971". Each earlier name has a small page that sends the reader on (`/ministry/human-resource-development/`), and every name is in the page's title and text, so a search by any of them finds it. One page per unit id, which lasts through renames (requirements §5).
- **U53. The family.** "Came from" and "Gave rise to": the units it took subjects from or gave them to, each linking to its page; for an abolished unit, "succeeded by" (Planning Commission → NITI Aayog), and back. Where a merger kept this unit's id because it brought the larger share, the page says so.
- **U54. Its own animation.** The chart itself, embedded in the page (`index.html?unit=U142`, the stage and controls only): from just before the unit began to its end (or today), every change of the government still happens, so the picture stays true, but only the unit's own changes play visibly, each structural one with its caption (Story); the others are muted, so the years without its changes pass quickly (U39). Only the unit and the units it dealt with keep their sector colours; every other cell is plain grey. The unit is held at the middle of the stage, its kin drawn in around it, and the camera stays with it. The other changes go by as fast as they can (a year without one of its changes takes 0.12 seconds), and a re-issue's caption shows only where it touched the unit. Clicking a cell opens its Rules (U42). It can be rendered as the unit's own video (§5).
- **U67. Its line.** A ministry carries on the units before it: its line, worked out from the changes (`cells/lineage.py`). From the unit, step back to the unit that fed it most when it was made: the unit split, or of a merger the units merged, and any unit absorbed into it the same day; of these, the one whose names share most words with the ministry comes first, then the one that brought the most subjects. A unit created from nothing, or spun off from another, begins a line of its own. The corrections file's `lines` sets a step by hand (`U109: U014`, Railways from 1986 carries on Railways 1957–1985) or cuts it (`stop`). The page shows "Its line" (Information Technology 1971–2001 → Communications & IT 2001–2016 → Electronics & IT since 2016), its title "since 2016 · its line since 1971"; its changes, family and animation (U54, U66) follow the whole line, the camera handing over from unit to unit. An earlier unit's page says where its line goes on.
- **U55. Size over time.** Shown by the cell itself in U54 (an earlier bar chart of subjects by year was dropped as dull).
- **U56. Its changes.** Every change of the unit, in time order: the date, the Prime Minister, what happened in words ("Takes 4 subjects from the Ministry of Labour and Employment"), the other units (links), and the amendment and its changes (U41). Each change shows the subjects it moved, by their text; not at a re-issue (174, 271), where every subject is reworded (R11). Each change links to the Rules after it, at this unit's section (U47).
- **U57. Its subjects.** The unit's subjects today (or when it ended), in full, in a list that opens and closes, linking to its section of the current Rules. The subjects at another date are a link to that version of the Rules, not repeated. Before 1961 there are no subjects, only names and changes; before 2004 the known gaps of the data are noted, as on the chart.
- **U57a. The index.** `/ministry/`: every unit, today's first and then the abolished ones, grouped by sector, each with its years and its number of changes.

## 9c. Publishing

- **U58. Text in the HTML.** Every page carries its content as HTML, not only as what the script draws: the chart page a short summary and the list of changes; a term page its summary card (U2a) and its changes; the amendment, Rules and ministry pages all their text. A reader without script, and a search engine, reads the same facts.
- **U59. A real address for each thing.** Besides the chart, `/pm/<term>/` for each Prime Minister's term (U2), `/ministry/<name>/`, `/amend/<n>/` and `/rules/<n>/`, each a written page (U48) with its own title and description. The `#pm-…` links of U2 still work and lead to the same view.
- **U60. Previews.** Every page has Open Graph and Twitter card tags: title, description and a 1200 × 630 image. The chart, each term and each ministry get an image rendered from the engine (the cells, the name and one line, "42 → 51 ministries"); the amendment and Rules pages share one.
- **U61. For search engines.** `sitemap.xml` (every page), `robots.txt`, a canonical address on every page, and schema.org data in JSON-LD: `Dataset` for the data (U62), `Legislation` for the amendments and the Rules, `GovernmentOrganization` for the ministries.
- **U62. The data, to download.** `timeline.json`, and CSV files of the units, their names and their changes, under a stated licence, with "How to cite" on the page. A release can be archived for a DOI.
- **U63. Address.** The site moves from `orgpedia.github.io/site.cabsec-aob` to an orgpedia.in subdomain (a `CNAME` file), and is linked from orgpedia.in and ministry.orgpedia.in.
- **U64. Fast and accessible.** Page images load as they come into view; each image has alt text naming the document and page; the pages pass a Lighthouse check for performance and accessibility; a viewer who asks for reduced motion gets the Full run without the jelly and the zooms.
- **U65. Later:** a Hindi version (`/hi/…`, the data has the Hindi names), an embed of one term or one ministry for other sites, a privacy-friendly visit counter, and the launch posts (a video per Prime Minister).

## 10. Technology

| Part | Technology |
|---|---|
| Data, timeline | Python, in this folder's build |
| Engine | Plain JavaScript modules, no build step: fixed-step physics, seeded randomness, the timeline clock |
| Cells | WebGL, with a small shader for the gooey blobs (smooth at 1080p and above) |
| Labels, captions, controls | HTML and CSS over the canvas on the web; drawn onto the canvas for the video |
| Video frames | Node and Playwright drive headless Chrome; the page exposes `renderFrame(t)`, stepped 30 times a second |
| Encoding | ffmpeg: frames and the sound track to MP4 |
| Sound | Web Audio; for the video, rendered offline from the timeline to a WAV file |

- **U32.** `make video` renders the MP4 (and the `.srt`) from `timeline.json`, with no hand steps.

## 11. Checks before sharing

- **U33.** Every event in `cells-2004.json` appears in the event list and plays in the Full run.
- **U34.** At every year's end, each cell's size equals the frame's size.
- **U35.** The video is under 2:20, 1080 × 1350, plays on a phone with the sound off, and every caption stays on screen long enough to read (about 3 words a second).
- **U36.** No label overlaps another in the focus of a salient event.

## 12. Later

- **Follow:** a button on a search result that keeps the camera on that cell through the whole run (a ministry page's animation, U54, is the first step).

## 13. Open

- Review of the drafts in `cells-names.yml`: the sectors of the 77 units, the short names, and the 16 salient events and their captions.
- The Presidents' term dates in `src/people.json` (the official page gives names only).
- The photos for the "In office" circles (§8): `src/people.json` names each file (`ui/people/<name>.jpg`); a circle shows initials until its file is there.
