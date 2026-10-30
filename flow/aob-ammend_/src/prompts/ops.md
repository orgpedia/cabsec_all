You read one notification amending the Government of India (Allocation of Business) Rules, 1961, and list
every change it makes to the Rules, so that a program can apply the changes to the Rules as they stood the
day before. You record what the text says, never what it means.

# The input

The notification as HTML. Each paragraph is `<p id="...">` and each printed line in it is
`<span id="...">text</span>`. Lines are in reading order. Only the English text is given.

# How to point at the text

Every item you return says where it is in the text:

* `line` is the id of the line where the item's words start, and `quote` is the item's words, copied
  **exactly** from the text: same spelling, capitals, punctuation and quote marks. A quote may run on to
  the following lines of the same paragraph; then copy it as the lines read, joined by single spaces.
* `lines` (for quoted text only) is `[first line, last line]`: the line where the quoted text starts and the
  line where it ends.

Quote only what the item is: the words that cite a provision, not the whole sentence. Never correct the
text, never add words to a quote, never quote words from different places together.

# What to return

**notification:** one item: the notification's number as printed in its first line, e.g. `S.O. 1813(E)`.
`number` is that number; `quote` is those words.

**commencement:** one item: the sentence saying when the rules come into force. `basis`:
* `at_once` ("They shall come into force at once"): `date` is the date printed at the head of the
  notification ("New Delhi, the 8th April, 2026" → `2026-04-08`), if it is printed; else null;
* `stated` (a date is given): that date;
* `retrospective` ("shall be deemed to have come into force on …"): that date;
* `appointed` (a date to be appointed later): `date` null.

**clauses:** every numbered clause of the notification that states a change, as numbered in print, joined
without spaces: `2`, `2(i)`, `2(a)(ii)`, `2(b)(i)(A)`. `quote` is the clause's first words, at least its
label and the five words after it. Clause 1 (the short title and commencement) is not a change.

**quoted:** every passage the notification quotes as new or current text of the Rules: the entries, headings
or words inside quote marks after "the following … shall be inserted/substituted, namely:". One item per
quoted passage, by `lines`.

**provisions:** every place in the Rules a change acts on or is positioned by. `quote` is the words that cite
it in the clause ("entry 14 relating to ‘Directorate of Sugar, New Delhi.’", "after entry 23", "in entry
20A", "for the sub-heading …"). `path` is the place, from the schedule down, **with the context the
notification gives in an enclosing clause copied in full**, so each path stands alone:

| step `kind` | identified by | example |
|---|---|---|
| `schedule` | `number`: `1` or `2` | "THE SECOND SCHEDULE" → `{"kind": "schedule", "number": "2"}` |
| `ministry` | `text`: the heading in English, as printed, without its bracketed Hindi transliteration | "MINISTRY OF PERSONNEL, PUBLIC GRIEVANCES AND PENSIONS" |
| `department` | `text`: the sub-heading as printed, without its letter or numeral and without the transliteration | "DEPARTMENT OF FOOD AND PUBLIC DISTRIBUTION" |
| `group_heading` | `text` as printed, numeral included | "XIII. Right to Information." |
| `entry` | `number` as printed | `"14"`, `"20A"` |
| `item` | `number` as printed, without brackets | `"k"` |
| `entry_range` | `number` as "first-last" | "entries 24 to 28" → `"24-28"` |
| `rule`, `sub_rule` | `number` | rules of the Order itself |

A step has a `kind` and exactly one of `number` or `text`. Entries the notification lists one by one ("24,
25, 26, 27 and 28") are separate provisions, one per number.

**changes:** every change, in the order the text states them, numbered `seq` from 1.

| the text says | `type` | fields |
|---|---|---|
| "… shall be omitted" | `repeal` | `targets`, `expect` if it quotes the current text |
| "after/before X, the following … shall be inserted" | `insertion` | `anchor` (the provision X), `position` (`after`, `before`), `content` |
| "for X, the following … shall be substituted" (a whole entry, heading or part) | `replacement` | `targets`, `content`, `expect` if quoted |
| "in X, for the words '…', the words '…' shall be substituted" | `substitution` | `targets`, `old`, `new` |
| "X shall be renumbered as Y" | `renumbering` | `targets`, `new_num` |

* `clause` is the id of the clause stating it, `clause_ref` its label (`2(iii)`).
* `targets` are the ids of the provisions it acts on; one instruction naming several ("entries 24, 25, 26,
  27 and 28 shall be omitted") is one change with several targets.
* `content` is the id of the quoted passage it inserts or puts in place.
* `expect`, `old`, `new`: the words exactly as quoted, without the quote marks around them.
* `scope`: `heading` when only a heading is replaced ("for the sub-heading …"), else null.
* `refers`: when a path refers to a part an earlier change of this notification made ("as so substituted",
  "as so inserted"), the id of that earlier change; else null.
* Renumbering that only follows from a replacement (8A, 8B becoming 8A, 8B, 8C) is not a change of its own.
* `flags`: `ambiguous_target` if a path could mean more than one part; `page_break_inside` if a page break
  falls inside the quoted text; `hindi_missing` if a new ministry or department heading has no bracketed
  transliteration. Usually empty.

Give every item an `id`: `n1`, `f1`, `k1`, `k2`…, `q1`…, `p1`…, `c1`…. Fields that do not apply are null.
Return nothing that is not in the text.
