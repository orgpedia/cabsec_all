# Requirements: the AoB units as cells

**Version:** 0.2 · **Date:** November 20, 2026 · **Status:** requirements only. This document is kept apart from `aob.md`, and it does not describe the code.

---

## 1. Purpose

The Government of India's ministries over 65 years, shown as living cells. Each top-level unit is a bubble sized by how many subjects it handles. When a ministry splits, its cell divides. When two merge, their cells fuse. When one is abolished, its cell pops. When it takes on or loses work, it swells or shrinks.

There are two uses:
- **A step-through chart:** a viewer moves through the amendments, one at a time or by year.
- **A short video:** made for sharing on LinkedIn.

This document sets out the data both need: what is counted, what counts as an event, how a unit is followed through time, and what files hold it. The chart and the video will be specified later, separately.

## 2. The AoB dataset

### 2.1 The Rules

The *Government of India (Allocation of Business) Rules, 1961* (the AoB Rules) say which part of the government handles which business. They are made by the President under article 77(3) of the Constitution, and were first notified on 14 January 1961. They have three parts:

| Part | What it holds |
|---|---|
| **The Order** | The rules themselves: a short title, then how business is allocated (rule 2), how subjects are distributed (rule 3), and how departments are allocated among Ministers (rule 4), with provisos and sub-rules. |
| **The First Schedule** | The list of units: ministries, the departments within each, and the secretariats and offices that sit in no ministry (the Cabinet Secretariat, the President's Secretariat, the Prime Minister's Office, NITI Aayog). Each is numbered. Since the 1970s each name has also been printed in Hindi, in Latin letters ("Ministry of Defence (Raksha Mantralaya)"). |
| **The Second Schedule** | The subjects each unit handles. Under each ministry's heading, and under each department within it, come numbered entries, sometimes grouped under group headings or parts, with items, notes and footnotes. |

### 2.2 The amendments

The Rules are changed by **amendments**, each published in the Gazette of India as a statutory order (S.O.) and numbered in a **series**. There are 386 of them, from series 1 (9 April 1961) to series 386 (22 July 2026). An amendment states its changes as operations on the Rules:

| Operation | Meaning |
|---|---|
| `insert` | Add a unit, a department or an entry |
| `omit` | Remove one ("Omitted." is left in its place, keeping its number) |
| `replace` | Put new text in place of a unit, department or entry |
| `substitute_text` | Change some words within one |
| `renumber` | Change numbers |

Some amendments are **re-issues**: they substitute a whole schedule.
- Both schedules were substituted in 1985 (series 174) and in 2004 (series 271).
- The First Schedule alone was substituted in series 30, 46, 58, 73, 88 (in Hindi names only), 89, 135 and 217.

The Cabinet Secretariat also publishes **consolidated versions**: the Rules as they stood after a given amendment. These are used as checkpoints.

### 2.3 The Rules as they stood after each amendment

The states product (`aob-states_`, `aob.md` §A6) applies each amendment's operations, in order, to the Rules before it. It checks the result against the re-issues and the consolidated versions. It is built in segments:

| Segment | From | To |
|---|---|---|
| C1 | the 1961 Rules | the 1985 re-issue (series 1–173) |
| C2 | the 1985 re-issue | the 2004 re-issue (174–270) |
| C3 | the 2004 re-issue | series 300 |
| Phase B | the consolidated version after series 301 | the latest (301–386) |

The result is one **state** for each amendment: the whole Rules after it, as a tree. This is the data the cells are made from.

### 2.4 Key entities

| Entity | What it is | Where it is |
|---|---|---|
| **Amendment** | One gazette notification, with its series, date, S.O. number and file | `chain.json` |
| **State** | The Rules after one amendment, as a tree | `states/<series>.json` |
| **Schedule** | `schedule` node, numbered 1 or 2 | in the state's tree |
| **Ministry** | `ministry` node: a top-level unit, holding departments | First and Second Schedules |
| **Department** | `department` node: within a ministry, or a top-level unit of its own | First and Second Schedules |
| **Hindi name** | `heading_hi` on a First Schedule unit ("Krishi Mantralaya"), or a name in brackets in a heading | First Schedule |
| **Subject** | `entry` node with a number ("1", "14A"): one item of business | Second Schedule |
| **Group heading, part** | `group_heading`, `part`: groupings of subjects inside a unit | Second Schedule |
| **Item, note** | `item` (a numbered clause of a subject) and `note` (a footnote) | Second Schedule |
| **Change** | One operation of an amendment, with the paths it touches before and after, and whether it was applied | `changes.json` |
| **Epoch** | The units at a printed version (1961, 1985, 2004, 2014, 2019, 2024, 2026), with flows of subjects between epochs | `evolution.json` |
| **Known issue** | Something the checks still raise, with why | `known-issues.json` |

### 2.5 The structure of a state

```
act
├── order                       the rules 1–4, provisos, sub-rules
├── schedule 1                  the units
│   ├── ministry 1  "Ministry of Agriculture and Farmers Welfare"  heading_hi "Krishi Evam Kisan Kalyan Mantralaya"
│   │   ├── department i  "Department of Agriculture and Farmers Welfare"
│   │   └── department ii "Department of Agricultural Research and Education"
│   ├── ministry 2  "Ministry of Ayush"
│   ├── department 7A "Omitted."
│   └── …
└── schedule 2                  the subjects
    ├── ministry "MINISTRY OF AGRICULTURE AND FARMERS WELFARE"
    │   ├── department "A. DEPARTMENT OF AGRICULTURE AND FARMERS WELFARE"
    │   │   ├── group_heading / part …
    │   │   └── entry 1 "…", entry 2 "…", … (items and notes under them)
    │   └── department "B. …"
    └── …
```

The state after series 386 holds 126 ministry and 127 department nodes across both schedules, 1,919 entries, 493 items, 108 group headings, 29 parts and 15 notes.

Two things about the data matter here:
- **Node ids (`eId`) are positional.** They change when units or entries are renumbered. Between series 4 and 5 only 586 of 865 entries keep theirs, and across the 1985 re-issue only 111. A subject has to be followed by its text, not its id.
- **The early scans are OCR text.** Names can carry reading errors ("Cabinet Secretarlat", "Ferti Lizers", "Ransha Man Tralaya").

## 3. What is counted

- **R1. A unit** is a top-level item of the First Schedule: a ministry, or a department, secretariat or office in no ministry. A department inside a ministry is part of its ministry's cell, not a cell of its own.
- **R2. A unit's size** is the number of its numbered subjects in the Second Schedule, under its heading and through its departments, group headings and parts. Omitted entries are not counted.
- **R2a. A unit with no numbered subjects** stays a unit, with size 0. The gazette prints some this way: the Ministry of Planning's Second Schedule entry is one paragraph, on answering to Parliament for NITI Aayog's subjects. How a size-0 unit is drawn is for the chart.
- **R3. A frame** is the Rules after one amendment, dated by the notification's date. Frame 0 is the 1961 Rules (14 January 1961). There are 387 frames.
- **R4.** A Second Schedule unit is named from the First Schedule item with the same heading. The First Schedule's spelling is used, and its Hindi name.
- **R4a. Pairing past OCR.** The Second Schedule's headings are read from scans and carry errors the First Schedule's do not ("MINISTRY OF CIVIL AVAIATION", "MINISTRY OF CHEMICAL AND FERTI LIZERS"); some are cut short ("MINISTRY OF CORPORATE" for the Ministry of Corporate Affairs), run on into the next words ("Ministry of Railways (Rail Mantralaya), Kailway Board (Rail Board)"), or printed in their Hindi name alone ("Vigyan Aur Irodyagiki Vibhag"). So a unit is paired with its First Schedule item:
  1. first by the same heading, for every unit, so that a near heading cannot take an item another unit carries exactly;
  2. then, among the rest, closest first, by the likeness of the letters, by one heading being the start of the other, by the Hindi name, or by most of the words in common.

  A pair is taken at a closeness of 0.85 or more. A First Schedule item left unpaired is listed for review (R17).
- **R5.** At the seven epochs, the sizes must equal the evolution page's counts.

## 4. The events

- **R6.** Events are found by following each subject from one frame to the next: first by the same text, then by shared rare words. A subject moved to another unit keeps its identity.
- **R7.** A count is a **good share** when it is at least 3 subjects and at least 20% of the unit's subjects.

| Event | When | Seen as |
|---|---|---|
| **born** | A new unit, with less than a good share from any unit before it | a cell appears |
| **ended** | A unit with no successor | the cell pops |
| **split** | A unit ends, and its subjects go to two or more units, a good share to each. Also: a unit renamed while a new unit takes the rest of its name ("Steel, Mines and Fuel" into "Steel & Heavy Industries" and "Mines & Fuel"). Not a split: when one *new* unit takes the most and the rest go to units that *stay*, that is the same unit **renamed**, with the rest **moved** (2021: "Heavy Industries and Public Enterprises" becomes "Heavy Industries", and the Department of Public Enterprises moves to Finance) | the cell divides |
| **spun off** | A unit stays, and a new unit gets a good share of its subjects | a smaller cell buds off |
| **merged** | Two or more units end in one new unit | the cells fuse |
| **absorbed** | A unit ends, and most of its subjects go to one unit that stays | the small cell is swallowed |
| **moved** | A good share of subjects goes from one unit that stays to another that stays | a droplet passes between cells |
| **renamed** | The unit stays, under another name. A different spelling or reading of the same name is not a rename | the label changes |
| **grew / shrank** | The unit stays, and its size changes by a good share, not already shown by an event above | the cell swells or shrinks |

- **R8. Which event wins.** For one unit at one amendment, the order is: ended or born, then split, spun off, merged or absorbed, then moved, then renamed, then grew or shrank. A rename and a size change can both be shown.
- **R9. Small changes** below a good share resize the bubble but are not events.
- **R10. Only touched units.** An event counts only at a unit whose heading or subjects the amendment's own changes reach. A difference elsewhere is a reading or matching fault, and goes to review.
- **R11. Re-issues and restarts.** Frames at the re-issues, the First Schedule substitutions and the restart after series 301 are marked, because many units change at once there.
- **R12. Captions.** Every event has a one-line caption naming its units and counts, for example "Ministry of Rehabilitation joins Works, Housing & Supply (25 → 45)".

- **R12a. A first frame from 2004.** The build can start at any amendment (`start`). From the 2004 re-issue (series 271) on, every First Schedule item has its Second Schedule unit, and each step follows at least 98% of subjects, except at the restart (series 301). The chart and the video are first built against these frames (`cells-2004.json`, 116 frames) while the earlier years' data is fixed; the whole run is the same format with `start: 0`. The first frame is marked `start`, and its units are shown as `born` there.

## 5. Units through time

- **R13. Ids that last.** A unit keeps its id through renames, moves and size changes. A unit made by a split, a spin-off or a merge gets a new id, and lists its parents.
- **R14.** When a merged unit carries one of its sources' names, it keeps that source's id, because to a reader it is the same ministry. The other sources are shown as absorbed.
- **R15. Names over time.** Each unit keeps its list of names, each with the frame it starts from.
- **R16. Hindi names.** Each name carries the Hindi name printed with it, in Latin letters as the gazette prints it. The 1961 Rules print none, so a unit takes its Hindi name from the first frame that prints one. A person can correct any name.

## 6. The data files

### 6.1 Inputs

Only these files, read from the states' output, and the 1961 Rules from the checkpoints:

| File | Fields used |
|---|---|
| `states/<series>.json` | `series`, `date`, and `tree`: the First Schedule's top-level headings and `heading_hi`, and the Second Schedule's units and entries |
| `chain.json` | `series`, `file`, `docs` (the S.O.), `date` |
| `changes.json` | `series`, `before[].path`, `after[].path`, `status` |
| `evolution.json` | the epochs' counts, as a check |
| `known-issues.json` | for review |

### 6.2 `cells.json`

```json
{
  "source": {"states": "…/aob-states_/output", "made": "2026-11-20", "least": 3, "share": 0.2},
  "units": {
    "U003": {"names": [{"name": "Ministry of Defence", "hindi": "Raksha Mantralaya", "from": 0}], "born": 0},
    "U017": {"names": [{"name": "Ministry of Steel, Mines & Fuel", "hindi": null, "from": 0}], "born": 0, "ended": 5},
    "U026": {"names": [{"name": "Ministry of Mines & Fuel", "hindi": null, "from": 5}], "born": 5, "parents": ["U017"]}
  },
  "frames": [
    {"series": 5, "date": "1962-04-09", "notification": "GOI_SO_1140_1962", "file": "1_Upload_38.pdf",
     "sizes": {"U003": 17, "U019": 45, "U026": 21, "…": 0}}
  ],
  "events": [
    {"series": 5, "date": "1962-04-09", "kind": "split", "from": ["U017"], "to": ["U026", "U027"], "moved": [21, 24],
     "caption": "Ministry of Steel, Mines & Fuel splits into Ministry of Mines & Fuel (21) and Ministry of Steel & Heavy Industries (24)"}
  ]
}
```

- `frames[].flags` marks `reissue`, `schedule1_reissue`, `restart` and `start` frames (the first frame of a run).
- `source.start` is the first amendment of the run: 0 for the whole run, 271 for `cells-2004.json`.
- Every frame lists every unit present in it.

### 6.3 Review and corrections

- **R17.** A review page lists what to check before anything is shared:
  - the events by decade and kind;
  - the events at marked frames;
  - the differences left out as untouched;
  - the steps where fewer than 90% of subjects were followed;
  - units with no name or no subjects;
  - First Schedule items with no Second Schedule unit.
- **R18.** A corrections file, kept by a person and read on every run, can:
  - set a unit's display name, short name or Hindi name;
  - keep an event, drop it, or change its kind.

## 7. Checks

- **R19.** The sizes at the seven epochs equal `evolution.json`'s.
- **R20.** Every frame's units match its First Schedule's top-level items. Any that don't are listed.
- **R21.** Every subject is accounted for between two frames: it stays, moves, comes or goes.

## 8. Known limits of the data

- Series 5 leaves a top-level unit with no name and no subjects, because one of its changes failed.
- Names read from scans carry OCR errors, and some Second Schedule headings carry Hindi read as Latin letters ("Ministry of Defence (Ransha Man Tralaya)").
- In segment C1 (1961–1985), 13 units are still missing and 4 reading errors are open. These will show as wrong cells until they are fixed.
- The re-issues of 1985 and 2004 rewrite many subjects at once, so matching across them is noisiest.
- Size means the number of subjects, not budget or staff. A ministry with a few large subjects looks small.

## 9. Later

- **The step-through chart:** layout, colours, how cells move, labels, the slider, and how events are animated.
- **The video:** length, pace, size for LinkedIn, captions and narration.

Both are specified in `ui-requirements.md`, agreed with Mukund on November 21, 2026.

## 10. Open questions

- Should departments inside a ministry be shown as smaller cells within it (nested cells)?
- Should the video run by amendment, or by year with the events of a year shown together?
- Should a unit that is abolished and later re-created under the same name (such as the Ministry of Tourism) keep its old id or get a new one?
