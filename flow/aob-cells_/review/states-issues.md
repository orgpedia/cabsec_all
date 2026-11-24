# What the cells still find in the states, traced by doc/aob.md §A11

**Date:** November 22, 2026 · **From:** the cells task (`flow/aob-cells_`), after rebuilding `cells.json` on the states
of November 21 (15:35). Segment C1 (1–173) still fails its basic checks: every change not applied is under a known
issue, but **10 units missing** and **4 reading problems** are under none (`known-issues.json`). Each is traced here
to its file, change and words, with the fix §A11's table names. Nothing upstream was changed: the `doc` repository,
the GovDoc files (for the word ids an edit needs) and the PDFs are not on this machine, so the fixes below are
proposals for the studio or for an agent in the repositories.

## 1. Reader: a remark's departments keep the remark's joining words — fix in the reader (`tasks/legal.py`)

A First Schedule entry with a remark ("Ministry of Defence (with a Department of Defence Production and a Department
of Defence Supplies within the Ministry)") is split into the ministry and its departments, but the departments'
headings keep the remark's words around them, so they do not match the Second Schedule's units.

| Series | File, change | Headings as exported | Should be |
|---|---|---|---|
| 43–45 | 1_Upload_76 (S.O. 3545, 1965), seq 1 | "Department of Defence Production and a"; "Department of Defence Supplics within the Ministry)" | Department of Defence Production; Department of Defence Supplies |
| 120–134 | 1_Upload_157 (S.O. 291(E), 1977), seq 2 | "Department of Official Language (Rajbhasha Vibhag) and Ɑ"; "Department of Personnel and Administrative Reforms (Karmik nur Prashasanık Sudhar Vibhag) within the Ministry (Mantralaya)]" | Department of Official Language; Department of Personnel and Administrative Reforms (Hindi names in `heading_hi`) |
| 121–122 | 1_Upload_158 (S.O. 378(E), 1977), seq 1 | "Department of Textiles (Vastar Vibhag ) Wwlthin the Ministry (Mantralaya)" | Department of Textiles |

The same remark in 1_Upload_123 (1971) splits cleanly, so the rule exists; it misses when the joining words are
misread ("Wwlthin", "Ɑ") or the remark is cut ("and a" at the end). Proposed rule: cut a remark department's heading
before " and a"/" and", before "within the Ministry" (also misread: one letter wrong), and drop a trailing ")" "]" and
the Hindi name in brackets into `heading_hi`. The misread letters left ("Supplics", "nur", "Prashasanık") are minor
for the coverage check (spelt apart). **Closes 4 of the 10 missing units.**

## 2. Reader: a heading runs on into page furniture or the next unit — fix in the reader, or edits

| Series | File, change | Heading as exported | What runs on |
|---|---|---|---|
| 6–14 | 1_Upload_39 (S.O. 1276, 1962), seq 2 | "Department of Community Development and Panchayati Raj. (945) [PART II" | the page number and the running head |
| 106–116 | 1_Upload_143 (S.O. 607(E), 1974), seq 5 | "Department of Cil Supplies and Cooperation (Nagrik Poorti aur Sahkarita Vibhag). it" | a stray word; "Cil" for Civil |
| 89 | 1_Upload_123 (S.O. 2319, 1971), seq 1 | "Planning Commission (Yojana nyog)" (in the states, `(Yojana Ayog).";`) | the quote's closing marks |
| 89 | 1_Upload_123, seq 1 | "Department of Science and Technology ☐ 28. Department of Supply" | **two units in one**: Supply lost |
| 89 | 1_Upload_123, seq 1 | "Department of Industrial Development i) Department of Internal Trade" | **two units in one**: Internal Trade lost |
| 89 | 1_Upload_123, seq 1 | "Department of Social Welfare 2/-.. i"; "Ministry of Shipping and Transport 3/m."; "* Ministry of Tourism and Civil Aviation" (typed a department) | marks from the scan |

Proposed rule: end a heading at a page's running head ("[PART II", "THE GAZETTE OF INDIA"), at a bracketed page
number, and before a following "NN. Department"/"(i) Department"/"i) Department", which starts a new unit; drop a
leading footnote mark and trailing marks. The words themselves ("Cil", "nyog") are edits. **Closes 2–3 missing units
(Community Development's department, Civil Supplies and Cooperation, the Planning Commission at 89) and puts back
Supply and Internal Trade in 1971.**

## 3. Reader: a department's heading merged with its unnumbered subject

| Series | File, change | Heading as exported |
|---|---|---|
| 8–11 | 1_Upload_41 (S.O. 1896, 1962), seq 2 (Second Schedule) | "Department of Special Economic Co-ordination. Specific matters of economic co-ordination as may be assigned by the Prime Minister from time to time." |

The heading ends at its first full stop; the rest is the department's one subject, unnumbered. **Closes 1 missing
unit** (the First Schedule's "Department of Special Economic Co-ordination", seq 1, is right).

## 4. The Second Schedule lags a First Schedule rename — a person's rename, or a known issue (a decision)

| Series | First Schedule | Second Schedule | Note |
|---|---|---|---|
| 6–14 | "Ministry of Community Development, Panchayati Raj and Co-operation" (1_Upload_39 renames entry 2) | "MINISTRY OF COMMUNITY DEVELOPMENT & COOPERATION", department "DEPARTMENT OF COMMUNITY DEVELOPMENT" | the S1 name goes back at series 15 |
| 88–100 | "Department of Labour and Employment" within the Ministry of Labour and Rehabilitation (from the 1971 renames) | the ministry alone, no department | |

If no amendment renames the Second Schedule's heading in these years, these are candidates for `renames:` in
`aob-states_/src/states.yml` (as the PMO's), or for `known.yml`. Draft, for Mukund's decision:

```yaml
    - series: 6
      schedule: 2
      from: "MINISTRY OF COMMUNITY DEVELOPMENT & COOPERATION"
      to: "MINISTRY OF COMMUNITY DEVELOPMENT, PANCHAYATI RAJ AND CO-OPERATION"
      note: "the Second Schedule follows the First's 1962 rename (1_Upload_39); decided by …"
```

**Closes 2 missing units.**

## 5. Changes the reading missed — the studio's Relations view, or a paid re-read

| Series | File | Problem | Cause found |
|---|---|---|---|
| 16 | 1_Upload_49 (1963) | clause (2) says a change is made, none found; change 2 missing between 1 and 3 | the model's change 2 has a path ending in an entry with **no number**, under "Depart- ment of Expenditure" (the word broken at a line's end), and "points at p2, not in the file": `core:model_invalid`, so it was dropped (lineage) |
| 97 | 1_Upload_131 (1974) | clause 3(h) says a change is made, none found; changes 27–28 missing | not traced: the GovDoc text is not here |

Fix: add the change in the Relations view (free), or edit "Depart- ment" and let Gemini re-read the notification (a
paid call; batch it, §A11 step 5).

## 6. Second Schedule units with no numbered subjects (the cells' check, R2)

| Series | Unit | Note |
|---|---|---|
| 89–173 | Department of Electronics | headed in the Second Schedule, no numbered entries under it: its entries not read, or put under another heading |
| 19–29 | Department of Technical Development | no entries; at series 30 (the 1964 re-issue) it is gone from the top level: check whether it moved into a ministry |

## 7. Railways missing from the Second Schedule, 1985–1986

At the 1985 re-issue (series 174) the Ministry of Railways has no Second Schedule unit until series 188, so its few
subjects show as "joining" the Ministry of Transport in 1985 and coming back out of it ("Ministry of Transport splits
into Surface Transport, Civil Aviation and Railways") in 1986. Check the re-issue's reading (1_Upload_212, from page
34) for the Railways' heading.

## Done in the cells task (not a data fix)

The cells' corrections file (`src/cells-names.yml`, `spelling:`) shows five First Schedule names as they should read
— "Home Affaus" (120–134), Personnel's lost commas (167–173), Law's Hindi name without "Mantralaya" (217–231),
"Implementa tion" (217–242), and the Railway Board run on into Railways' name (5–216) — and the cells' name cleaning
now drops a leading footnote mark ("* Ministry of Tourism and Civil Aviation", which also made it count as a
department) and a trailing ":-". Five false events went (renames that were only spellings) and one came right: at
series 243 (1999) the Ministry of Planning and Programme Implementation splits into Statistics and Programme
Implementation and Planning. When the states mend these names, the `spelling:` lines can go.
