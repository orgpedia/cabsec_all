# Requirements: the cells chart and video

**Version:** 0.5 · **Date:** November 24, 2026 · **Status:** requirements only, agreed with Mukund before coding. The data is specified in `requirements.md`; this document specifies what is drawn from it. The look and the event animations follow the storyboard (`ui/storyboard.html`).

---

## 1. Purpose and scope

- **U1. Two outputs, one engine.** An interactive web page and a short video for LinkedIn and X are drawn by the same code from the same data, so they never differ.
- **U2. Two periods.** The page plays the whole run from the Rules of 14 January 1961 (`timeline.json`: 387 frames, 352 events, 28 salient) or from the 2004 re-issue (`timeline-2004.json`: 116 frames, 61 events, 16 salient), chosen by a switch above the stage ("1961–2026" / "2004–2026"; the second's link ends `#from-2004`). Before 2004 the readings of the scanned gazettes still have known gaps (`review/states-issues.md`), noted under the stage. A cell's size is scaled to the period's largest frame, so the government fits the stage in every year (864 subjects in 1961, 1,846 at most).
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
| Header | orgpedia's black bar and wordmark, the page title |
| Left: event list | A scrollable list of every event, grouped by year, each with its kind badge and caption. The current event is highlighted and the list scrolls with the animation. Clicking an event jumps there. Salient events are marked. |
| Centre: stage | The cells (§6) |
| Stage, top left | The year, large and faint; under it, very faint, the count of units: "44 ministries · 7 departments & offices" |
| Stage, top right | "In office" (§8): the President, the Prime Minister and the Cabinet Secretary as three small circles |
| Stage, bottom | The caption card (Story), or the badges (Full run) |
| Under the stage | Play/pause, the timeline scrubber with year ticks and a mark for each event, step to the previous or next event, speed, the Story / Full run toggle, sound on/off (off by default) |
| Under the controls | The kinds of change shown (§4a), then the sector legend. There is no other chart: the cells are the whole picture. |

- **U13. Hover or tap a cell:** its full name, subjects, sector, and its names over time.
- **U14.** The page works on a phone: the event list moves under the stage, and the "In office" strip shrinks.
- **U15. Hosting.** A self-contained static page, with no server. For now a published page; later on orgpedia.in.

## 4a. Search and the kinds shown

- **U37. Search.** A search box above the event list finds every unit whose names, at any time, hold all the words typed ("education" finds HRD; "jal shakti" finds Water Resources). It shows:
  - the units found, each with its years ("Planning Commission (2004–2015)", "Defence (since 2004)");
  - the number of matches, "2 of 7": each shown change that involves a unit found, in time order, or the unit's first appearance if it has none;
  - ▲ / ▼ (and Enter / Shift+Enter) to go to the previous or next match, which moves the playhead there.

  While searching, the units found are lifted above a veil, and the event list shows only their changes.
- **U38. The kinds shown.** A row of chips, one per kind of change (merged, absorbed, split, spun off, created, abolished, moved, renamed, size changes) and "In office", each with its count. A kind turned off is **not shown**, but it still happens, because the cells must stay true to the Rules:
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
- **U30.** A build step (`make timeline`) writes `ui/timeline.json` (from 1961) and `ui/timeline-2004.json`: per year, its events in order, the frames' sizes, the salient flags and captions, and the in-office changes. The web page and the video both read it.
- **U31.** `people.json`, as in §8.

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

- **Follow:** a button on a search result that keeps the camera on that cell through the whole run.

## 13. Open

- Review of the drafts in `cells-names.yml`: the sectors of the 77 units, the short names, and the 16 salient events and their captions.
- The Presidents' term dates in `src/people.json` (the official page gives names only).
- The photos for the "In office" circles (§8): `src/people.json` names each file (`ui/people/<name>.jpg`); a circle shows initials until its file is there.
