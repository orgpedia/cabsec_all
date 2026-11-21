# Plan: fixing the pre-2004 Schedule 1 and 2 issues

**Date:** November 21, 2026 · **Status:** done on 21 Nov, except where noted below. Code commit e7d896c in doc (local). 26 more changes apply and none fewer (176 to 150 not applied). C1's missing units went from 34 to 27 and its uncovered items from 17 to 14. C2, C3 and Phase B still pass.

The UI agent's list (groups A, B and C) traced back through the states, the changes and the amendments' readings. The 20-odd symptoms come down to **eight causes**. Each fix below is one of four kinds:

| Kind | Where | Costs a paid call? |
|---|---|---|
| **Cells** | `flow/aob-cells_` (its pairing and names) | No |
| **Reader** | `doc`: how an amendment's quoted content is turned into units and entries (`tasks/legal.py`, `content_nodes`) | No: the export re-runs from the call cache |
| **States** | `doc`: a new inference rule in the states, with a call on it in `decisions.yml` | No |
| **Studio** | a person's edit to an amendment's reading or its ops (`aob-ammend_/conf/*.edits.yml`) | Possibly: an edit that reaches the ops step calls Gemini, so these are batched into one run |

## 1. One misread Hindi word keeps Science and Technology out of reach

**Done, 21 Nov:** "Irodyagiki" corrected to "Prodyogiki" in 1_Upload_122 (one Gemini call by batch). 13 changes now apply: 91/7, 95/3, 97/32, 98/21, 107/7, 147/7, 155/20, 157/15, 160/4, 164/65–67 and 170/4. None stopped applying. C1's missing units went from 34 to 30, and its uncovered items from 17 to 16.

**Symptoms:**
- Department of Space (95–173)
- Department of Sports (155–163)
- Department of Supply (157–163)
- Department of Youth Affairs and Sports (164–173)
- most of C1's 11 "unit not found at the top level" changes

**The chain, with the gazette's words:**

| Series, date (file) | What the amendment says | What the states do |
|---|---|---|
| 88, 3 May 1971 (1_Upload_122, S.O. 1914, p. 9; clause 3(s)) | "after the heading "Company Karya Vibhag" and the entries thereunder" insert three units, headed by their Hindi names only: SANSKRITI VIBHAG, SANSADIYA KARYA VIBHAG and **Vigyan Aur Prodyogiki Vibhag** (Science and Technology), with its 9 entries (p. 11) | Applied, but OCR read the heading as "Vigyan Aur **Irodyagiki** Vibhag" (word r1.w3649) |
| 89, 17 June 1971 (1_Upload_123, S.O. 2319; clause 3(a)) | "for the name of any department, the name of that department in the First Schedule … shall be substituted" | The `hindi_name` rule renames every Hindi heading to its First Schedule name (SAMAJ KALYAN VIBHAG to Department of Social Welfare, KARMIK VIBHAG to Department of Personnel…). It can't match "Irodyagiki" to the First Schedule's "Vigyan Aur Prodyogiki Vibhag", so Science and Technology keeps its misread Hindi heading until 1985 |
| 95, 18 July 1972 (1_Upload_129, S.O. 498(E); clause 3(b)) | "after the heading "DEPARTMENT OF SCIENCE AND TECHNOLOGY (VIGYAN AUR PRODYOGIKI VIBHAG)" and the entries thereunder" insert DEPARTMENT OF SPACE | Not applied: no such heading |
| 147, 4 Dec 1980 (1_Upload_185; (D)) | "under the heading "DEPARTMENT OF SPACE"", after entry 8 | Not applied: no Space |
| 155, 6 Sept 1982 (1_Upload_193, p. 10) | after "the heading "DEPARTMENT [OF] SPACE (ANTARIKSH VIBHAG)" and the entries thereunder" insert DEPARTMENT OF SPORTS | Not applied: no Space |
| 157, 30 June 1983 (1_Upload_195, p. 5; (g)) | "after the heading "DEPARTMENT OF SPACE (ANTARIKSH VIBHAG)" and the entries thereunder" insert DEPARTMENT OF SUPPLY (POORTI VIBHAG) | Not applied: no Space |
| 164, 4 Jan 1985 (1_Upload_202, p. 24) | under DEPARTMENT OF SPORTS: "for the existing heading" put DEPARTMENT OF YOUTH AFFAIRS AND SPORTS; "after entry 3" insert entries; "(23) the heading "DEPARTMENT OF SUPPLY (POORTI VIBHAG)" and the entries thereunder" omitted | Not applied: no Sports, no Supply |
| 170, 31 July 1985 (1_Upload_208; (iv)) | "under the heading DEPARTMENT OF SPACE", after entry 9 | Not applied: no Space |

Science and Technology was never missing. It has been in Schedule 2 since May 1971, but under a heading nothing can find. In the states it shows as a separate unit named "Vigyan Aur Irodyagiki Vibhag" until the 1985 re-issue. Series 124 (1977) inserts a second Science and Technology from the Ministry of Planning, which is the one the cells saw "arrive" in 1977.

**Fix:**
- **Studio (one word):** in 1_Upload_122, page 11, correct "Irodyagiki" to "Prodyogiki". Then series 89's rename applies, and series 95 and everything after it follow. This is the real fix. If the edit reaches the ops step, it re-reads that one document with Gemini.
- **States (free, if you'd rather not re-read):** let the `hindi_name` rule match a Hindi heading loosely, allowing up to 2 misread letters, the way the `loose` rule does for English headings. Such a match would be noted, and listed in `decisions.yml` as unreviewed. This is broader than the one-word fix, so I'd only use it if other Hindi headings turn out to be misread the same way.

## 2. An op that was never read

**Symptoms:** Ministry of Civil Supplies (144–156), and change 11 of series 157 ("no ministry MINISTRY OF CIVIL SUPPLIFS").

**Cause:** amendment 144 (1_Upload_182) adds the Ministry of Civil Supplies to the First Schedule and moves Civil Supplies out of Commerce (changes 11–12). But no op inserts the new ministry into Schedule 2. The model's reading missed it. Series 157 then tries to omit a unit that was never there.

**Fix (studio):** add the missing insert op to 1_Upload_182 in the studio's Relations view, and correct "SUPPLIFS" in 157's reading. Both go in one batch.

## 3. Quoted content read as one block of text

**Symptoms:**
- Cabinet Secretariat with 0 subjects (120–147 and 154–173)
- Department of Technical Development with 0 subjects (19–173)

**Cause:** the content of a replace or insert came out as a single `text` node, not a unit with entries:
- **1_Upload_157, change 8:** "CABINET SECRETARIAT (MANTRIMANDAL SACHIVALAYA) 1 Secretarial assistance to the Cabinet … 2 Rules of Business." The entries are numbered "1 …" with no full stop after the number, after a heading that carries a Hindi name.
- **1_Upload_52, change 19:** "DEPARTMENT OF TECHNICAL DEVELOPMENT The Development Wing." Here the content reads as only the heading and a sub-heading. Its entries were either cut off at the page break or not quoted.

**Fix:**
- **Reader:** in `content_nodes`, a unit heading in capitals, with or without a Hindi name in brackets, followed by "1 … 2 …", becomes a unit with numbered entries. A test goes in `test_legal.py`.
- **Studio:** look at 1_Upload_52's pages. If entries follow, widen the quoted content. If none do, the department really had none in 1963, and nothing needs fixing.

## 4. A department's label misread, so it lands at the top level

**Symptom:** Department of Information Technology at the top level (257–270), headed `C". DEPARTMENT OF INFORMATION TECHNOLOGY`.

**Cause:** in 1_Upload_298 change 4, the department C inserted into the Ministry of Communications and Information Technology is read with the label `C".`, so its content is typed as a ministry and lands at the top level. The ministry's own department C stays "Omitted."

**Fix (reader):** the misread-label rule that already strips such labels in the First Schedule (`^\S{1,3}\.\s+` before "Ministry" or "Department") is applied to Schedule 2 content headings too, allowing a stray quote. A heading that starts "Department of" inside a ministry's insert is then typed as a department.

## 5. A department nested at the wrong level

**Symptom:** Department of Irrigation at the top level with 0 subjects (164–173), and the Ministry of Irrigation and Power holding the department's entries.

**Cause:** in 1_Upload_202, change 45 replaces the Ministry of Irrigation with "Ministry of Irrigation and Power", and change 46 inserts department B (Power) after entry 11. Department A (Irrigation) is read as a heading of its own and placed beside the ministry, not inside it. Its entries stay on the ministry.

**Fix (reader):** in a ministry's replaced content, a "Department of …" heading followed by entries becomes a department holding those entries. This is the same nesting the reader already does for First Schedule content. A test goes in `test_legal.py`.

## 6. Subjects printed without numbers

**Symptom:** Department of Electronics with 0 subjects (89–173).

**Cause:** its single subject ("Development of Electronics and coordination amongst its various users") is printed with no number, so it is read as a `paragraph`. The cells count only numbered subjects. Separately, the old "Department of Electronics" inside the Cabinet Secretariat was never omitted.

**Fix:**
- **Cells:** a unit with no numbered subjects counts its unnumbered subject paragraphs. This is noted in the requirements as an exception to R2.
- **Studio (to check):** find the change that moved Electronics out of the Cabinet Secretariat in 1971 (series 89) and see whether its omit was read.

## 7. Real one-amendment gaps between the schedules

**Symptoms:**
- Ministry of Food Processing Industries, missing for one frame (196)
- Planning Commission, missing in Schedule 2 for one frame (89)
- Prime Minister's Office (135–173)

**Cause:** these are not reading errors. The gazette changed the two schedules in different notifications:
- **Food Processing:** added to the First Schedule in 196 and to Schedule 2 in 197.
- **Planning Commission:** in the First Schedule re-issue at 89, and in Schedule 2 from 90.
- **Prime Minister's Office:** renamed in the 1977 First Schedule (135), but Schedule 2 kept "Prime Minister's Secretariat" until the 1985 re-issue.

**Fix (cells):**
- Pair a Schedule 1 item and a Schedule 2 unit through an alias in `cells-names.yml` (Prime Minister's Office ↔ Prime Minister's Secretariat, 135–173).
- Mark one-frame gaps as `lag`, not as missing.

No change to the states.

## 8. Schedule 1 headings: Hindi-only re-issue and OCR spellings

**Symptoms:**
- series 88 (Hindi names only)
- "Min'stry of Energy : Department of Power" (134)
- "Ministry of Rehablitation" (from 28)
- "Ministry of Education (Shiksha Mantrala-" (from 164)
- Railways not pairing (188–216): "…Railway Board (Rail Board)" in Schedule 1, "…Kailway Board" in Schedule 2

**Cause:**
- **Series 88** is the gazette's Hindi-only First Schedule (1_Upload_122), re-issued in English a month later (89). The states already leave it off the First Schedule page (`page_skip: [88]`).
- **The rest** are OCR errors in headings.

**Fix:**
- **Cells, now:** frame 88 keeps 87's English names, the way the states' page skips it. Display names for the OCR spellings go in `cells-names.yml`. The Railways pairing gets an alias. None of this costs a paid call.
- **Studio, later:** correct the spellings in the amendments' readings, in the same batch as cause 2, so the states carry the right names too.

## C. C1's open list

C1's 17 uncovered items and its `top_level` cluster (11 changes) mostly come from causes 1 and 2 (the cluster's pattern in `known.yml` names exactly Space, Sports, Science and Technology, Electronics and Supply), so fixing those should close most of them. Home Affairs (33), Agriculture (17), Planning (5) and Finance/Revenue (4) are separate clusters, already explained in `known.yml`, and this plan does not touch them.

## Order

1. **Cells fixes** (causes 6, 7 and 8): free, and the UI agent can rebuild at once.
2. **Reader fixes** (causes 3, 4 and 5): free, with a guarded refresh and new tests.
3. **Cause 1:** the one-word fix in 1_Upload_122 (or the looser `hindi_name` rule, if you prefer it).
4. **One studio batch** (causes 2, 3 and 8, and the checks in 1 and 6): the only step that may call Gemini, so I'll say before running it which documents it re-reads.

After each step: the checks, `known-issues.json`, and a rebuilt `cells.json`, with the before and after counts of missing and empty units.
