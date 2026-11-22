# Use Case: The Allocation of Business Rules Over Time

**Version:** 0.12 (phase C: the readings and rules of November 21; how to debug a change) · **Date:** November 22, 2026

**Changes in 0.12:** what the November 21 fixes built, written down: the export's reading of the scans' quoted schedules (§A5, how the export reads quoted schedules); four more patcher rules (§A6, the patcher); the inference `after_its_ministry`, the series 88 English headings, and a person's renames (`renames:`, rule `renamed_by_decision`) (§A6, inferences; a person's renames); how to debug a change that does not apply, for an agent in the repository and for a person in the studio (§A11); and the ops spec, until now a separate requirements file, merged in and brought up to the code (§A12).

**Changes in 0.11:** each document's lineage, one JSON gathering what made its reading and what became of it: its source, a person's edits, the steps and model calls, the reviews, the issues, the rules used, its changes' outcome (§A6, lineage); the changes not applied each with a cause, and the collection's known issues in a file of their own like the decisions file (§A6, known issues); the re-issues listed (§A6, phase C).

**Changes in 0.10:** the basic checks after every series (§A6, the basic checks); the patcher's inferences, each a listed rule, noted, with the call on it in the collection's decisions file (§A6, inferences); the 1971 Hindi and English notifications (§A6, phase C); the Second Schedule's reading rules (§A6, the patcher).

**Changes in 0.9:** a schedule substituted alone by an ordinary amendment (the First Schedule, by S.O. 452(E) of 1991, Series 217) is read by the versions task as a re-issue's is, its reading the change's content; it is not a check (§A6, phase C).

**Changes in 0.8:** a heading put in place of a numbered one, quoted without a number, keeps the number it had, marked and noted (§A6, the patcher).

**Changes in 0.7:** a version that renumbers headings with no amendment doing it raises one issue, `new_renumbered`, for all the headings under one part moved by the same amount, not one each; taking the version's text takes their numbers (§A6, issues by stage).

**Changes in 0.6:** phase C, the amendments before 301, in three segments split by the two amendments that substitute both schedules whole (1985, 2004): each starts from a base and ends checked against the next re-issue, or the first version (§A6, phase C). The footnotes are not compared with the changes: the compilers' footnotes are another format to read and are not kept with care.

**Changes in 0.5:** the issue codes are named by the stage they are found at, `read_`, `old_`, `states_`, `new_`, and the studio groups them so; decisions made under the earlier codes are read under the new ones (§A6, issues by stage).

**Changes in 0.4:** the states' problems go back to the studio as issues: on the change they belong to, else on the consolidated version's part they are about; dismissed with a note, they are counted apart; a difference that is the version's own correction is verified instead, and the states take the version's text there from that amendment on. A rename in one schedule that a later change refers to by its new heading in the other is made there too (§A6).

**Builds on:** GovDoc 3.4 (`govdoc.md`: §6.4 divisions, §6.6 quoted text and amendments, §10.4 the AoB example, §12.4 Akoma Ntoso), the Document Pipeline 0.12 (`docflow.md` Part P), the reviewer (`studio.md` Part R), `docflow.md` Part M (the model tagger), and *AoB Amendment Extraction – Requirements* (Oct 30, the ops an amendment states; called **the ops spec** here). Sections are numbered §A1, §A2…

---

## A1. Goal

The Government of India (Allocation of Business) Rules, 1961 list the ministries and departments (the First Schedule) and the subjects each handles (the Second Schedule), after the Order's own rules. 386 amendments have changed them since 1961. The goal: the Rules as they stood on any date, built from the gazette notifications.

Deliverables, in two parts that can change separately:

| Part | Deliverable |
|---|---|
| **The pipeline** | (a) A GovDoc file for each PDF: the 1961 Rules, the 386 amendments, the consolidated versions |
| **The data products** | (b) **The ministries over time:** a CSV of events, and a loader that makes a SQLite table answering "which ministries and departments existed on date D" |
| | (c) **The Rules on Gitea:** a git repository whose first commit is the 1961 Rules, and then one pull request per amendment, with the text it changes, the amendment in Akoma Ntoso, and the gazette's text |

Later, not in this plan: the evolution of ministries, departments and subjects (renames, splits, merges, transfers), with departments as units and Second Schedule subjects as entities. The Transaction of Business Rules are out of scope.

## A2. Decisions

| # | Question | Decision |
|---|---|---|
| 1 | Where the work lives | In `cabsec_all`, as tasks under `flow/`, with the PDFs linked from `input/documents/`. The data products are tasks too: they read the GovDoc files of the other tasks. **Data** lives in each task's `output/` and `conf/`; **code**, the data products' included, in docflow (all tasks together for now) |
| 2 | The ops | The ops spec's ops (§A12), extracted from GovDoc files (not plain text), so each op points at its words. The ops spec's `amendment` object is the amendment task's export |
| 3 | Authority | **The gazette.** The consolidated versions are checks: where they disagree with the gazette, an issue is raised |
| 4 | Order | Series-number order. Dates are in-force dates |
| 5 | Scope of the text | The Order, the First Schedule and the Second Schedule. English only; Hindi is ignored, except the English transliterations of names, kept in their own field |
| 6 | Reading scans | Google Cloud Vision |
| 7 | Extracting the ops | The model tagger (`docflow.md` Part M), built first, with Gemini 4 Argon; the model is a setting |
| 7a | Vocabulary and profiles | Written by hand in the task that uses them (`conf/`, linked where docflow reads outside data). Anything generated by a long process gets its own task, and its output is linked into `conf/` or `input/` |
| 7b | Akoma Ntoso | **The standard's own terms wherever it has them:** its elements, its naming convention for `eId`s, its `textualMod` types. `hcontainer` only where it has no element. The `legal:` relation types are named after the `textualMod` types |
| 8 | Order of work | The born-digital era first (2016–2026), where checkpoints are dense; then the 1961 base; then the scanned era |
| 9 | Units (later, for evolution) | Ministries and departments both; Second Schedule subjects as entities |
| 10 | Review | In the studio. Problems the data products find go back to the studio |
| 11 | Corrections after publishing | The Gitea repo is deleted and made again from scratch |
| 12 | Gitea | The task writes files only: one folder per commit and a JSON file listing them in order, so that pushing them one by one is trivial. Pushing comes later, with the server's details |

## A3. The sources (studied October 30)

From `cabsec_all/input/documents/` (its `SPEC.md` describes how they are fetched):

* **`aob-rules/`**: 88 versions of the Rules.
  * **The 1961 Rules** (`1_Upload_1144`, 35 pages): a scan with no text layer, clean print. One page needs a look: on printed page 54, "A—Department of Community Development" appears among the Department of Industry's entries.
  * **87 consolidated versions,** 2011 to 2026, born-digital. Each states the last amendment it includes on its first page ("As amended upto Amendment Series no. 386"); 50 also say so in the site's title. They are the **checkpoints**: the Rules after amendment N, as the Cabinet Secretariat consolidated them. They cover 299 to 386, with a few gaps. Their footnotes ("Modified vide Amendment series no. 251 dated 04.08.2000", since 1998) say which parts each amendment touched.
* **`aob-ammend/`**: 386 amendments, series nos. 1–386, one PDF each, no gaps.
  * **Scans, 1961 to about 2015.** Most have a scanner's OCR layer, readable but noisy; 46 have none.
  * **Born-digital gazettes, about 2016 on.** Hindi first, in a font whose text layer decodes wrongly, then English.
  * **Several amendments in one gazette issue:** the site has the same PDF under each of their series numbers: 6–7 (S.O. 1276, 1962), 126–127 (S.O. 128(E), 129(E), 1978), 257–259 (S.O. 1251–1253(E), 2001), 318–319 (S.O. 2492(E), 2493(E), 2015). One GovDoc file, one document per notification.
  * **Series order and date order differ** three times: 166/167 (1985), 225/226 (1994), 273/274 (2004).
  * **Retrospective:** no. 98 (an omission "with effect from the 7th February, 1973") and no. 164 ("deemed to have come into force … on the 31st day of December, 1984").
  * **No corrigenda or re-uploads** found in the site's listing or the text layers. To be checked again after OCR, for the 46 without text.

Over the decades: 76 amendments in the 1960s, 63, 67, 41, 48, 58, and 33 in the 2020s.

## A4. The tasks

```
cabsec_all/flow/
  aob-1961_/         the 1961 Rules, read three ways and reviewed in full: the base       (pipeline)
  aob-rules_/        the consolidated versions: their outline, as checkpoints            (pipeline)
  aob-ammend_/       the amendments: notifications, clauses, quoted text, ops            (pipeline)
  aob-states_/       the Rules after each amendment, checked against the checkpoints     (data product)
  aob-ministries_/   the ministries and departments over time: CSV and SQLite            (data product)
  aob-gitea_/        the Rules on Gitea: one pull request per amendment                  (data product)
```

Each has the layout of `docflow.md` §P19 (the working store; Part N §N27 once it moves, §N34): `input/` (links), `src/` (the flow, settings, prompts, expected outputs), `conf/` (edits, vocabulary, profiles), `output/`. The pipeline tasks are docflow flows, one file at a time. The data products work across files, in order: their code is in docflow beside the other tasks, run by the task's makefile; they read the pipeline tasks' GovDoc files through those tasks' `output/` links, and their exports, and write only to their own `output/`.

## A5. The pipeline

### The 1961 base (`aob-1961_`)

Every later version is built on it, so it is read three ways and reviewed in full before anything else uses it.

| Step | Task | What |
|---|---|---|
| text | `gcv_recognizer` | Cloud Vision: the words and their boxes. GovDoc's words come from here |
| readings | new | Gemini 4 Argon and Gemini 3.1 Pro (settings) each transcribe every page; answers in the call cache. They are evidence, not words: GovDoc has one reading per page |
| compare | new checker | Aligns the two transcriptions with Cloud Vision's lines. Where all three agree, nothing. Where they differ, an issue on the line, with the other readings as suggested edits (GovDoc §8.6); two models agreeing against Cloud Vision makes the first suggestion |
| page order | new checker | Pages in order by their printed numbers, and the schedules' numbering continuous across pages |
| lines, layout | existing | |
| outline | pattern rules | The Order's rules, the schedules, ministries, departments (`A—`), group headings (`I. TRADE`), entries, items: `core:division`s with their markers and headings |
| export | new | The base tree (§A6) |

A person then goes through all 35 pages in the studio, starting with the issues. The first run measures how often the two models agree and are right. If they are nearly always right, a later version may apply their agreed readings itself; the first run only suggests.

### The checkpoints (`aob-rules_`)

The consolidated versions, born-digital: `pdf_text`, then the outline by pattern rules, as for 1961. Their footnotes are tagged (`core:footnote`, `core:note_marker`, GovDoc §6.5), with the amendment each cites. The export: the version's tree (§A6), "upto N" from its first page, and per footnote the node it is attached to and the amendment it names.

### The amendments (`aob-ammend_`)

| Step | Task | What |
|---|---|---|
| import | `import_manifest` | The PDFs from `input/documents/aob-ammend/pdfs/`; `items.json` (series no., S.O., dates, the cabsec URL) as the sources file |
| text | `ocr` (`engine: textlayer`) | Born-digital text from the text layer, read by pdfium: unipdf misplaces the words of the 2019–2020 gazettes, whose Hindi is set in a legacy font. Scans: Cloud Vision (not yet) |
| language | `pdftable_finder` (`scripts: [LATIN]`) | Lines mostly in another script out of the flow, so documents hold English only. Hindi in a legacy font reads as Latin letters and stays; the model ignores it |
| lines, layout | existing | |
| split | `section_splitter` | The gazette issue (its masthead) and one document per notification, at "S.O. <n>(E)": `GOI_SO_1813E_2026`. The series number is joined later, from `items.json` |
| ops | `model_tagger`, `model_entities`, `model_relations` | One model answer per notification (`docflow.md` §M2), read by three steps: its clauses (`core:division`) and quoted text (`core:quoted_text`); the provisions it cites (`core:provision`, the ops spec's `cited` path as the `provision` value); and the ops, as `legal:` relations named after Akoma Ntoso's `textualMod` types (`legal:insertion`, `legal:repeal`, `legal:substitution`, `legal:replacement`, `legal:renumbering`) from the provision to the quoted text, with the ops spec's fields as values. The in-force date and its basis |
| ops check | `legal_ops_check` (`prefix: aob`) | The ops spec's checks (§A12): every "shall be" clause has an op, verbatim strings occur in the text, `refers` points back, `seq` runs in order; a quoted passage across a page break is seen in its words. Flags become `aob:` issue codes, `read_…` (§A6, issues by stage) |
| export | `amendment_export` | The ops spec's `amendment` object per notification, `output/<name>.json`: each op's target paths, its quoted content read into the Rules' parts, its words and boxes |

Run first on the born-digital amendments (330–386) with the ops spec's tests T1–T4 (§A12) as expected outputs (`docflow expect`): T1 = no. 385, T2 = 382, T3 = 355, T4 = 362, all four matching (204 checks). Then on the scans.

**How the export reads the quoted schedules** (`amendment_export`, `tasks/legal.py`, version 65). Besides "Ministry of …" and lettered "A. Department of …" headings, it reads, as the scans print them:

* **A unit of the top level by another name, in capitals, its Hindi name in brackets** ("CABINET SECRETARIAT (MANTRIMANDAL SACHIVALAYA)", 1_Upload_157): a unit of the top level, its entries numbered with no stop. A heading in capitals that runs on to its next line ("MINISTRY OF PETROLEUM AND / CHEMICALS (PETROLEUM AUR RASAYAN MANTRALAYA)") is one heading, not a second unit.
* **An unlettered department first in a passage, in capitals, with or without its Hindi name** ("DEPARTMENT OF ELECTRONICS (ELECTRONICS VIBHAG)", 1_Upload_123; "DEPARTMENT OF TECHNICAL DEVELOPMENT", 1_Upload_52): a department, its subject in words after it. An unlettered department's name alone on its line may carry its Hindi name in brackets ("DEPARTMENT OF STATISTICS (SANKHYIKI VIBHAG)", 1_Upload_144) and a full stop.
* **A quote mark read after a department's letter** ('C". DEPARTMENT OF INFORMATION TECHNOLOGY', 1_Upload_298): the letter C.
* **A ministry and its one department on one line**, the First Schedule's ("4A. Ministry of Energy (Oorja Mantralaya) : Department of Power (Vidyut Vibhag)", 1_Upload_171): two units, the department inside the ministry.
* **A unit's first group heading** ("DEPARTMENT OF PERSONNEL … / I. Recruitment … / 1 Reservation of posts …", 1_Upload_157): the entries after it number from 1.
* **A replacement's scope "and the entries under that heading"** is read from the change's own clause, not the next one's: 1_Upload_38's "(a) for the heading 'Department of Commerce' and the entries under that heading … (b) for the entries under the heading …" replaces the heading and its entries in (a), the entries alone in (b).
* A note's text that does not end its sentence goes on over the next line, as an entry's does.

Not yet: notes and provisos are siblings of the entry they follow in `content`, not its children; `ref_seq` is on the op, not on the path step.

## A6. The Rules' states (`aob-states_`)

**A state** is the Rules on one date, as a tree:

* `order` → `rule` → sub-rules, provisos;
* `schedule 1` → `ministry` → `department` (and secretariats and offices, at either level);
* `schedule 2` → `ministry` → `department` → `group_heading` → `entry` → `item`, with `note`, `proviso`, `explanation` under entries.

Each node has its number, its text (or heading), the English transliteration of its name where printed, and its Akoma Ntoso `eId`, made from its path by AKN's naming rules (`sch_2__hcontainer_1__hcontainer_a__point_14`). A unit of Schedule 1 also has an **id that lasts** through renames (§A7).

**The patcher** applies an amendment's ops to the state before it, in `seq` order:

* it resolves each cited path to nodes: headings by their normalized form, numbers as printed, ranges after the state's own numbering (so 25A is inside 24–28), `ref_seq` to the node an earlier op made;
* it checks `expect` against the node's text;
* it raises a problem for every path that resolves to nothing or to more than one node, and every `expect` that does not match. **It guesses only by a listed rule** (below, inferences): each use is noted on its change and kept in `inferences.json`, and a person's call on the rule decides whether it acts.
* **A rename the notification takes as made in both schedules.** A change may name a unit in one schedule by the new heading another change gave it in the other schedule, referring back to that change ("B. DEPARTMENT FOR PROMOTION OF INDUSTRY AND INTERNAL TRADE … as so substituted" in S.O. 503(E) of 2019, after the First Schedule's rename). The patcher renames the unit there too before applying the change, provided three things hold: the change refers to the rename (`ref_seq`); exactly one unit of that kind under the parts the path names has the heading the rename replaced; and the path's heading is the rename's new one. The rename is then that change's part, and the report notes it. Anything else is still a path not found.
* **An entry's item cited by the entry's number and the item's letter**, as the gazettes cite it: "after entry 23(b), … 23(c). Matters relating to Forward Contracts …" (S.O. 2694(E) of 2013). A path's "entry 23 (b)" is item (b) of entry 23, and quoted text that starts "23 (c)." is item (c).
* **A part inserted under the number of one omitted before takes its place**, as the compilers print it: S.O. 2010(E) of 2014 inserts "(q) National AIDS Control Organisation (NACO)" after item (p), where the version prints "(q) Omitted."; the omitted (q) goes.
* **A heading put in place of a numbered one keeps its number when quoted without one**, as the compilers print it: S.O. 277(E) of 2005 (series 279, 1_Upload_323) puts "Ministry of Health and Family Welfare …" with its departments in place of "15. Ministry of Health and Family Welfare …", the new heading unnumbered; 1_Upload_910 prints it 15. Only for one part replaced by one of its kind; the part is marked (`num_kept`) and the report notes it, so a number lost in reading the quote is still seen.
* **A sub-heading omitted alone** ("the sub-heading 'A. DEPARTMENT OF PARLIAMENTARY AFFAIRS …' shall be omitted", 1_Upload_222): the heading goes, its entries stay the ministry's.
* **A unit's entries put for it with no heading of their own kind** (1_Upload_216's Department of Health: groups and entries): they go inside it; in the Second Schedule, a ministry replaced by its lettered departments alone, likewise (1_Upload_268).
* **A department's heading put alone right under a ministry's** ("A. Department of Works, Housing & Supply", 1_Upload_38; "A. DEPARTMENT OF RURAL DEVELOPMENT", 1_Upload_260): the ministry's parts after it, up to its next department, are the department's.
* **"and entries as under the existing heading '…'"** (1_Upload_38): the heading put in with a copy of the parts under the one named, as the Rules stood before the notification.
* **"the heading '…' and the entries given in Appendix I to this Order"** (1_Upload_50, 61): the content is that heading and those appendices of the notification.
* **A department quoted with its parts after a unit the First Schedule has it within** goes in that unit (1_Upload_186's Ocean Development, in the Cabinet Secretariat); an unlettered department after a top-level department, beside it.
* **A heading quoted again over the parts put under it** (1_Upload_44's Defence; 1_Upload_278's Law, Justice and Company Affairs): those parts.
* **A department cited by its heading alone, as if of the top level,** where the Second Schedule has it within a ministry ("under the heading 'Department of Personnel and Administrative Reforms'", within Home Affairs since 1977, 1_Upload_175): found within that ministry when exactly one department there has the heading, and noted as found loosely.
* **A cite that finds a part in a unit and in a department within it** ("under the heading 'MINISTRY OF HOME AFFAIRS', entry 34", 1_Upload_163): the unit's own part, the one under the fewest units, not the Department of Personnel's entry 34 inside it. Not for a range.
* **A ministry's heading replaced by a heading and one sub-heading** ("for the existing heading, the following heading and sub-heading shall be substituted: 'Ministry of Irrigation and Power' / 'A. Department of Irrigation'", 1_Upload_202), where the ministry has no departments: the ministry renamed, and all its parts now its new department's.
* **"For the sub-heading '…' and the entries thereunder"** replaced by one unit of the same kind with its own heading (1_Upload_143: "C. Department of Community Development" and its entries, by Rural Development): the whole department replaced, not its entries alone.

### Inferences and decisions

**An inference** is a step the reading does not state outright. Each is a rule, noted on the change it acts on (`report.tsv`, `changes.json`), kept in `aob-states_/output/inferences.json` (rule, change, note, status, new since the run before), raised in the amendments' studio as information on the change (`aob:states_inferred_<rule>`, step `inferred_check`), and listed with the amendment's own clause on `versions/inferred.html`:

| Rule | What it does | Example |
|---|---|---|
| `loose` | a misread name taken for the one unit it can mean: each of its words in the other, a letter or two misread, nearer than the next | "Minisatry of Consumer Affairs …" (1_Upload_331) |
| `hindi_cited`, `hindi_name` | a unit cited, or headed, by its Hindi name alone, its English name from the First Schedules the run has | 1_Upload_122 (1971) |
| `one_heading` | a ministry's heading and its sub-heading put as one heading: the department's parts the ministry's | 1_Upload_79 (1966), Industry |
| `earlier_name` | a Second Schedule heading lagging behind the First Schedule's renames: the unit found by an earlier name | Commerce and Supply (1_Upload_206) |
| `put_again` | a unit put in again by a name already there: the stale one omitted | Tourism (1_Upload_278, 1998) |
| `after_its_ministry` | a ministry inserted after a department of another ministry that the states do not have: put after that department's ministry | Civil Supplies after Agriculture's Department of Agricultural Research and Education (1_Upload_182, 1980) |
| `renamed_by_decision` | a rename no amendment records, made by a person's decision (below, a person's renames) | Prime Minister's Office, series 135 |
| `renamed_as_referred`, `number_kept` | as above (the patcher) | |

**The 1971 English headings** (under `hindi_name`). Series 88 (1_Upload_122) prints the First Schedule in Hindi names alone ("Raksha Mantralaya"). Each such heading gets its English name from the English re-issue a month later (1_Upload_123), which the run has: the English name becomes the heading and the Hindi one its Hindi name, as the re-issue prints them. A department read as an item ("(1) Shiksha Vibhag") is made a department, its name its heading. A Hindi name near two names in the list is taken when both are one English name spelt apart. Those the reading cannot place are given by a person's renames.

**The decisions file** (`aob-states_/src/decisions.yml`, states config `decisions`) holds the calls: a rule accepted (applied, counted right), unreviewed (applied, not yet looked at) or off (not applied); a single case rejected (`{rule, series, seq}`: not applied, the rest of the rule acting); a rule tried and left out, with why (a unit the First Schedule drops, dropped from the Second: the schedules are amended in separate notifications, and a rename can look like a drop). A person need not review each case in the studio: the rule's call covers them.

### A person's renames

**The renames list** (`renames:` in `aob-states_/src/states.yml`, `StatesConfig.renames`) holds the renames a person decided where no amendment records one: each with the `series` after whose changes it is made, the `schedule` (1 or 2), `from` and `to` (the heading), `to_hi` (its Hindi name, if given) and a `note` (who decided, when, why). The states rename the first unit of that heading, top level or second, mark it as the decision's (`by: <series>:decision`), and note it under the rule `renamed_by_decision`, so the page and the lineage show it was a person's call, not the gazette's. In the list now: "Prime Minister's Secretariat" in the Second Schedule renamed "Prime Minister's Office" from series 135 (the First Schedule's 1977 rename, which the Second printed only at the 1985 re-issue), and six of series 88's Hindi departments given the English names the June 1971 re-issue prints (Banking, Revenue and Insurance, Cooperation, Family Planning, Labour and Employment, Chemicals).

A rename goes here only when the gazettes are silent and the schedules disagree. A misread name is mended in the reading (an edit), not renamed here.

### Lineage

**A document's lineage** is one file, `aob-states_/output/lineage/<file>.json`, for every file the states read (the 1961 base, the checkpoints, the amendments), written by the states on every run, with a page for it (`versions/lineage-<file>.html`; `versions/lineage.html` lists them; a re-issue read both as an amendment and as a version has two, the version's `<file>.version`). It gathers what is recorded elsewhere and adds nothing new: a person can see from it alone everything that made the document's reading and what became of it.

| Part | What it holds | Read from |
|---|---|---|
| `source` | the file's URL, portal, download time, sha256; its pages; the pages left off (`page_skip`, a re-issue's Hindi half) | the GovDoc file's `source`; the flows' config |
| `edits` | each run of a person's edits, by whom and when, each edit's target, before and after | `conf/<file>.edits.yml` (as brought into the GovDoc file: its `edits` and human runs) |
| `steps` | the steps whose work is current: each step's task, version, stamp and time; for a model's step, the model, its prompt file and its config hash | the GovDoc file's `runs`: the last run of each step, and the human runs whose edits stand (a run superseded by a later one of its step is left out) |
| `reviews` | each review in the studio: what it is on (a change, an annotation, an issue), its status (verified, rejected, corrected, pending), by whom, when, its note | the GovDoc file's `reviews` |
| `issues` | each issue on the file, by stage (`read_`, `old_`, `states_`, `new_`), its severity and message, open or dismissed (with the dismissal's note) | the GovDoc file's `issues`; the states' problems on it (`problems.json`) |
| `rules` | each inference that acted on one of its changes: the rule, the change, the note, the rule's status from the decisions file (accepted, unreviewed, rejected), and the decision's date and maker | `inferences.json`; the decisions file |
| `changes` | each change: its op and path as read, applied or not; when not, the problem, its cause and its known issue (below) | the states' `changes.json`, `report.tsv` |
| `bridge` | for a re-issue or a schedule substituted whole: what it substitutes, its segment, the bridge's differences | `bridges.json`; the re-issues list (phase C) |
| `made_by` | the code's commit and the docflow version the run used | the run |

A model's call is named by the step's model and config hash. The call's cache key and batch are not recorded on the run today; recording them is a docflow change (left to the docflow spec, Part P), and the lineage shows them once the run has them.

### Known issues

**A change not applied has a cause**, given by the states from where its path stops in the state before it (`changes.json`, `checks.json`, the lineage):

| Cause | When |
|---|---|
| `unit_not_found` | a ministry or a department the path names is not there by that name |
| `group_not_found` | a group heading or a part the path names is not there |
| `entry_not_in_state` | the entry is not in the unit (looking through its groups and parts): beyond its last, in a gap, an "A" entry |
| `items` | the entry has no items, or not numbered as cited (misread: "li", "lv") |
| `number_twice` | two parts with the number the change cites |
| `words_differ` | the words to substitute, or the part it quotes, not as the state has them |
| `refers_missing` | it refers to a change not made |

**The known issues file** (`aob-states_/src/known.yml`, states config `known`), like the decisions file, holds a person's account of what is left: each known issue with an id, a title, why, and what it covers (by segment, cause, unit heading or amendment), and the units known to be missing with why (1971's Hindi names; the Prime Minister's Office, renamed in the First Schedule in 1977, in the Second at the 1985 re-issue; Food Processing Industries, its schedules a month apart). The states put each change not applied, and each unit missing, under the first known issue that covers it, else under none; `known-issues.json` and `versions/known-issues.html` list them by segment. **The basic checks pass** for a segment when nothing is under none: every change not applied, unit missing and reading error is fixed or known.

### The basic checks

After every series (`checks.json`, `versions/checks.html`; each run's numbers appended to `checks-history.jsonl` with the code's commit):

1. **The First Schedule:** its problems in the series, major (an error) or minor.
2. **Coverage:** every unit of the First Schedule, top level and second (a remark's departments too), headed in the Second (the same name; spelt apart, minor: a misread, plural, or Hindi name the same).
3. **Subjects:** its part has numbered subjects (in words only, minor: the Ministry of Planning).
4. **Reading:** each amendment's changes read by schedule, its reading issues, and its changes not applied by schedule. Re-issues and schedules substituted whole are bridged: listed apart, their Second Schedule changes counted there.

By segment (C1, C2, C3, phase B), a re-issue's state starting its segment.

**A version listed under the wrong "upto"** is flagged on the version, for a person to set it aside (the versions flow's `exclude`) or dismiss: one that already prints, where an amendment acts, what the amendment makes (`old_upto_ahead`: 1_Upload_915, listed upto 299, prints 300's rename), and one that reads the same as the next version though the amendment between changes the Rules (`old_upto_same`: 1_Upload_913 is 910 word for word). The website's file can be replaced by a later one without its listing changing.

**Checks against the checkpoints:** after amendment N, where a consolidated version says "upto N", the state is compared with it: the First Schedule exactly (normalized), the Second Schedule entry by entry. The versions' footnotes are read but not compared with the changes (decided November 4, 2026): they are another format to consume, and the compilers do not keep them with care.

**Phase C: the amendments before 301.** No consolidated version is printed before 2011 (upto 299), and the website lists none before 301 that we keep. Two amendments substitute **both schedules whole** ("for the First Schedule and the Second Schedule, the following Schedules shall be substituted"), and from the day they take effect the schedules are what they print: the gazette itself, not a compilation. They split phase C into three segments:

| Segment | Starts from | Amendments | Checked at its end against |
|---|---|---|---|
| C1 | the 1961 Rules (`aob-1961_`) | 1–173 | the schedules of Series 174 |
| C2 | the schedules of Series 174: 1_Upload_212, S.O. 696(E), 25.09.1985 | 175–270 | the schedules of Series 271 |
| C3 | the schedules of Series 271: 1_Upload_535, S.O. 17(E), 06.01.2004 | 272–300 | 1_Upload_910 (upto 301) |

A misreading in one segment stops at its end; each segment has a check at its end; they can be worked in any order. The order of work is C3, C2, then the 1961 base and C1; within each, Schedule 1 before Schedule 2. Series 243 (1_Upload_283, 1999, 100 pages) is not a re-issue: it inserts ministries with their entries, an ordinary amendment.

* **The re-issues as checkpoints.** Both are printed in Hindi first, then in English. The versions task lists them in `include` (the website does not list them as versions), each with the series it holds, its first English page and why: 1_Upload_212 from page 34, 1_Upload_535 from page 154. Only those pages are read, in both tasks, so the Hindi half is never sent to OCR. 1_Upload_212 has no text layer and is set in two columns; 1_Upload_535's layer is a scanner's (Readiris) that garbles the Hindi: both are read by Cloud Vision. The version reader takes a document of schedules with no Order. A re-issue numbers its entries afresh, so a gap in the numbering is a misreading. Each is reviewed in full: it is a segment's base.
* **The re-issues** (`versions/reissues.html`): the First Schedule substituted whole in Series 30, 46, 58, 73, 89, 135 and 217, and in Hindi alone in 88 (1_Upload_122, not bridged); the Second Schedule alone in 174 (1_Upload_212, starting C2); both in 271 (1_Upload_535, starting C3). Each is bridged but 88.
* **The re-issues as amendments.** Their other clauses (rule 3, in 2004) are read by the model as any amendment's. The clause that substitutes the schedules is one change, "the schedules replaced", whose content is the versions task's reading of the same file, not the model's: the model reads the clause pages only, not 150 pages of quoted schedules.
* **A schedule substituted alone.** An ordinary amendment may substitute one schedule whole and change the other clause by clause: S.O. 452(E) of 1991 (Series 217, 1_Upload_257) substitutes the First Schedule, renumbered, and amends the Second by name. The versions task reads that schedule too (`include`, its pages; the reading stops at the next amending clause, "3. In the Second Schedule …"), and the change's content is its reading, not the model's: the versions reader knows a schedule's Hindi names, numbering and columns. It is not a check: what it prints is the amendment's own change, and no other text of that day exists to compare it with. A gap in its numbering is a misreading, as in a re-issue; what it misreads otherwise shows at the segment's end.
* **1971: the Hindi version and the English one.** 1_Upload_122 (S.O. 1914, May 1971) substitutes the First Schedule in Hindi names alone and amends the Second Schedule, heading the units it changes in Hindi ("SHIKSHA AUR SAMAJ KALYAN MANTRALAYA") and citing them so ("VITTA MANTRALAYA"). 1_Upload_123 (S.O. 2319, June 1971) substitutes the First Schedule in English and, by its rule 3, (a) gives the Second Schedule's units the First Schedule's names, (b) re-arranges them in its order. The Hindi First Schedule is left off the First Schedule's page (`page_skip: [88]`); 1_Upload_122's Second Schedule changes are applied, its Hindi names read by the English ones (`hindi_cited`, `hindi_name`). Rule 3(b), the order, is not applied: no check depends on it.
* **The states at a re-issue:** the schedules start again from the re-issue's; the Order goes on, with its other clauses applied.
* **The check at a segment's end** compares the states just before the re-issue with the schedules it prints, as a version is compared, under the `new_` codes. A difference is a misreading of ours or a change the re-issue itself made (a re-issue can bring a reorganisation: September 1985); the tools cannot tell which, and a person reviews them.
* **Without a version before an amendment there is no old:** every change that does not apply is a `states_` issue, and in phase C these are the work list, worked in series order, the earliest first. A difference at a segment's end goes on the amendment that last changed the part (its `by`), else on the checkpoint.
* **The bridge at a re-issue of the First Schedule.** Between the states just before a re-issue and the First Schedule it prints, the changes that take one to the other, in the amendments' terms: renamed, moved (to another ministry, or between ministry and department), merged, inserted, omitted, reworded, and the routine ones folded away (renumbered, as runs; spelled otherwise; a Hindi name given). A unit is matched by its name, else by its number at its level where the two names share a word, else by a name holding most of the other's words; so each unit keeps one identity through the re-issue, for the evolution of ministries. Applied to the states before, the bridge must give the First Schedule printed; what it leaves is listed. Each bridge is in `bridges.json` and on the version page of its series; a person checks the short list instead of two schedules, and a change that repeats one an amendment in the segment should have made points at an extraction error. The First Schedule over time is a page between two re-issues, linked to the bridge at its end.
* **Schedule 1 first:** the report, the issues and the check at a segment's end can be limited to Schedule 1, so Schedule 2 does not bury it.

**Generated versions.** After each amendment, the states are also rendered as a page a person reads like a consolidated version, `aob-states_/output/versions/<series>.html` with an index: at its head what that amendment changed (each change, the part before and after, or why it was not applied); below, the Rules after it, each part with its eId as its anchor, a note of the change that last made it ("Inserted vide Series 310, 08.12.2014", as the compilers' footnotes say, once on the outermost part), the parts this amendment changed marked, and buttons to show the Order or one schedule (phase C reviews Schedule 1 first). They are marked as generated from the amendments, not official: they repeat any change read wrongly, and the checks never use them. They are written again with the states on every run, never kept apart. The amendments studio links them from the header's chain and from a change's "In the Rules".

**Back to the studio.** Each change's part of the Rules before and after it (or, not applied, the nearest part its path reaches), with the versions' pages, is written to `aob-states_/output/changes.json`; the amendments studio shows it with the change (studio.md §R6.2). The patcher's and the checks' problems are written to `aob-states_/output/problems.json`, each naming where a person fixes it (`on`):

* **A problem tied to a change** (an op the patcher refused, a difference in a part a change made or changed, or a part missing among the parts a change made): that change, in the amendment's file (its document and `seq`). A change acting nearby (in the same department) is not enough.
* **A difference in a part no change touched:** a misreading of a version, or the compilers' own correction between versions. It goes on the part's words in the consolidated version's file: the version after the amendment, or, for a part only in the state, the version the check started from.

A checker step, `problems_check` (`states_check` in both the amendments task and the versions task), reads the file (a config file: its hash joins the step's stamp, so a new file runs it again) and raises each problem on its file as an issue `aob:<code>`, a warning: on the change (a relation), or on the line of the part's first word, with the words that differ in its details. A person fixes the change in the studio, or dismisses the issue with a note: a gazette gap, a correction in the version. The states are then built again. The states product reads the dismissals back from the GovDoc files: a dismissed problem stays in `problems.json` with who dismissed it and the note, and `report.tsv` counts it in `dismissed`, apart from the differences still open.

**Issues by stage.** An issue's code names the stage it is found at, so a person sees where to look first. The words: **old** is the consolidated version printed before an amendment; **new** the one printed after it; **expected new** old with the amendment applied; **the states** the Rules built from the start version through the amendments alone (the only chain where no version comes between, phase C).

| Stage | Codes | What failed |
|---|---|---|
| 1. `read_`: reading the amendment, on its own (`legal_ops_check`) | `read_quote_mismatch` (error), `read_clause_missed`, `read_sequence`, `read_path_unsure`; `read_page_break`, `read_hindi_missing` (information); the model steps' `core:model_unanchored`, `core:model_invalid` are grouped here | A change quotes words not in the notification; a "shall be" clause with no change; changes out of order or referring wrongly; the model unsure of a path |
| 2. `old_`: applying a change to old | `old_path_missing`, `old_path_ambiguous`, `old_quote_mismatch`, `old_words_missing`, `old_already_omitted`, `old_ref_missing`, `old_op_unknown`; `old_upto_ahead`, `old_upto_same` | The change does not fit old, so it is left out; or old is listed under the wrong upto |
| 3. `states_`: applying a change to the states | `states_` and stage 2's second parts (`states_path_missing`, …) | The change fits old but not the states: an earlier difference left open |
| 4. `new_`: expected new against new | `new_text_differs`, `new_missing` (a part of new missing from expected new), `new_extra` (in expected new, not in new), `new_renumbered` (headings renumbered alike), `new_hindi_differs` (information) | Something misread, or the compilers' own correction |

**A renumbering.** Headings under one part whose names agree but whose numbers differ, all by the same amount, three or more (1_Upload_910 numbers ministries 24–43 and departments 46–50 one lower than the base and the amendments since give them, filling the 23 the changes left empty; no amendment says so), are one `new_renumbered` issue, naming each heading's number before and after; a heading's number differing on its own (lost, or moved by another amount) stays a `new_text_differs`. Taken, the states give each heading its number in the version from that amendment on.

The patcher's own names lack the stage (`path_missing`); the problem's code adds it. The model's flags keep their prompt's names (`ambiguous_target`, `page_break_inside`, `hindi_missing`), so the prompt and its cached answers stand; each raises its `read_` issue, and the export lists the issue codes. A dismissal or a verification recorded under the codes before the stages (`version_text`, `path_not_found`, `state_path_not_found`, …) is read under the new ones.

**The version's own correction.** A difference in a part no amendment changed, where the version is right (the compilers mended the wording: "its subjects" for "their subjects" in rule 3, 2022; or carried a rename into an entry's text, which the amendment did not ask for), is verified in the studio ("Take the version's text", the collection config's `issues.verify`) instead of dismissed. The checks are unchanged, but the states take the version's part from that amendment on: its text and all inside it, or its heading; a part only in the version goes in after the part before it there, and one only in the state is left out. The problem stays in `problems.json` with `taken` (who, when, the note), `report.tsv` counts it in `taken` and notes the part in that amendment's row, and the states' `drift` from the versions does not carry it on. A taken part's `by` in the states is `<series>:version`.

## A7. The ministries over time (`aob-ministries_`)

`ministries.csv`, one row per event, from the states and the ops:

```
date,series,seq,id,kind,op,name,new_name,transliteration,parent,new_parent
1961-01-14,0,1,ministry/commerce-and-industry,ministry,add,Ministry of Commerce & Industry,,,,
1961-01-14,0,2,department/commerce,department,add,Department of Commerce,,,ministry/commerce-and-industry,
```

| Column | |
|---|---|
| `date` | the in-force date; the base is 1961-01-14 |
| `series`, `seq` | the amendment (0 for the base) and the op: the order of events on one day |
| `id` | lasts through renames: `<kind>/<slug of the first name>`, with `-2` when a slug was already used |
| `kind` | `ministry`, `department`, or `other` (Cabinet Secretariat, Planning Commission, NITI Aayog…) |
| `op` | `add`, `remove`, `rename` (`new_name`), `move` (a department to another ministry: `new_parent`). A department that becomes a ministry is a `remove` and an `add` |
| `name`, `transliteration` | English as printed in the gazette, normalized (spaces, "&" and "and", case); the bracketed transliteration in its own column |

* **A rename** is a change of name alone, spelling included, made by an amendment that substitutes the heading. Anything more (a split, a merge) is `remove` and `add` for now; the evolution product will say more.
* Implicit departments (a ministry with no departments listed holds its subjects itself) are not in the CSV.
* `load.py` makes `membership(id, kind, name, parent, valid_from, valid_to)`, rejecting events that do not fit (adding what is there, removing what is not), with the query for a date.
* **Checked** at every checkpoint: the list on that date is the consolidated version's First Schedule.

## A8. The Rules on Gitea (`aob-gitea_`)

The task writes the repository's history as files; pushing it to a Gitea server is a separate, later step, one commit and pull request at a time (the person gives the server's details and a token).

```
output/gitea/
  manifest.json               every commit in order: what to push, and how
  0000/                       the first commit: the 1961 Rules
  0001/ … 0386/               one per amendment: the files it adds or changes, at their paths in the repository
```

In the repository:

```
README.md
rules.akn.xml               the Rules as an Akoma Ntoso act: each amendment changes it
text/order.md               the Order's rules
text/schedule-1.md          the ministries and departments
text/schedule-2/<id>.md     one file per ministry, named by its id (a rename changes one heading line)
amendments/<series>/gazette.md        the notification's English text, and its URL on cabsec.gov.in
amendments/<series>/amendment.akn.xml the amendment as an Akoma Ntoso amendment (activeModifications)
```

`manifest.json`, one entry per commit:

```json
{"step": 1, "series": 1, "folder": "0001", "branch": "amendment-0001",
 "files": ["text/schedule-1.md", "text/schedule-2/cabinet-secretariat.md", "rules.akn.xml",
           "amendments/1/gazette.md", "amendments/1/amendment.akn.xml"],
 "removed": [], "date": "1961-04-17", "author": "Cabinet Secretariat",
 "title": "Amendment Series No. 1: S.O. 857 (1961)", "body": "…", "checks": "passed"}
```

* **The first commit** is the 1961 Rules, dated 14 January 1961. Then one per amendment, in series order: one branch, one pull request.
* **The pull request's description:** the series no., the S.O. no., the dates, the gazette's URL (no other copies), and each change in Akoma Ntoso's terms (`repeal` of `…__point_14`, quoted "…").
* **Dated** by the in-force date (author and committer); merged fast-forward to keep the dates. The two retrospective amendments come earlier in time than the commits before them.
* `checks` says whether the amendment passed its checks (§A6); one that did not is left open for a person when pushed.
* **Corrections:** the files are written again and the repository is made again from scratch.
* Akoma Ntoso files are checked against the OASIS schema. Text is one entry a line, so a diff shows exactly the entries changed.

## A9. Steps

0. **The model tagger** (`docflow.md` Part M).
1. **The amendments task, born-digital era:** import, text, language, layout, split; the model tagger's three steps and the ops; tests T1–T4. Needs: the language step, the ops check, the ops export, the vocabulary.
1a. **The ops in the studio:** a view of an amendment's changes, each with its provision, its quoted text and its fields, editable, the edits recorded as for any other item (`studio.md` §R6.2). Built: the Relations level, `flow/aob-ammend_/review/studio.yml`.
2. **The checkpoints task** on the consolidated versions from 2016 on. Built: `flow/aob-rules_/`, `rules_export`.
3. **The states task** from the 2016 checkpoint (upto 329) forward to 386, checked at every checkpoint; problems back to the studio.
4. **The ministries CSV** for 2016–2026, checked the same way.
5. **Phase C** (§A6): reading scans by their text layer or by Cloud Vision, as their quality says; a pilot of 10–15 amendments across the decades; the two re-issues as checkpoints and resets; then segment C3 (272–300), C2 (175–270), and the 1961 base (three readings, the comparison, the full review) with C1 (1–173). Schedule 1 before Schedule 2 in each.
6. *(merged into 5)*
7. **The ministries CSV** from 1961.
8. **Gitea:** the files and manifest for 2016–2026 first, pushed to a trial repository; then the whole history.

## A10. Open

* ~~The ops spec changes~~ Done: merged into this spec as §A12 (November 22). Still open there: whether `content` nodes get provisional stable ids when read or only when the patcher places them; where the `amendment` object's JSON Schema lives, and whether it shares node definitions with the Rules'.
* The `legal:` and `aob:` vocabularies and the profiles of the three document types, in the amendments task's `conf/`.
* ~~GovDoc §10.4's example used `legal:substitution` for replacing a whole entry.~~ Done: now `legal:replacement`, as in Akoma Ntoso (GovDoc 3.4).
* The models' exact ids, and their cost on a sample.
* Akoma Ntoso's work and expression URIs for the Rules and the amendments (FRBR), following its naming convention.
* Recording a model call's cache key and batch on its run, for the lineage (docflow, Part P).

## A11. Debugging a change that does not apply

Every fix of November 21 went the same way: from a change not applied, or a unit missing at a check, back to the gazette's file, page and clause; then one of five fixes; then a refresh and the checks again. Two tracks follow: one for an agent (Claude) working in the repositories, one for a person in the studio. Both end at the same checks.

**The five fixes**, from cheapest to dearest:

| What is wrong | The fix | Where | Costs a paid call? |
|---|---|---|---|
| The gazette is read wrong: a misspelt word ("Irodyagiki" for "Prodyogiki", "Kailway", "DEPARTMESNT") | a source edit | `flow/aob-ammend_/conf/<file>.edits.yml`, made in the studio | Yes, if the word reaches the ops step: Gemini re-reads that notification |
| The words are right, but the quoted schedule is turned into the wrong units (a heading missed, a scope read from the next clause) | a reader fix, with a test | `doc`: `tasks/legal.py`, `tests/test_legal.py`; the export's version goes up | No: the export re-runs from the call cache |
| The words and units are right, but the change names a part the states hold another way (§A6, the patcher) | a patcher rule, or an inference with a call on it | `doc`: `products/states.py`, `products/inferences.py`, `tests/test_states.py`; `aob-states_/src/decisions.yml` | No |
| The gazettes are silent: the schedules disagree and no amendment says why | a person's rename | `renames:` in `aob-states_/src/states.yml` | No |
| None of these: a gazette gap, or left for later | a known issue | `aob-states_/src/known.yml`, or the issue dismissed with a note | No |

### For an agent in the repositories

The repositories: `cabsec_new` (the flows: `flow/aob-ammend_`, `aob-rules_`, `aob-states_`) and `doc` (docflow's code and this spec). Never touch `flow/aob-cells_` from here; it is its own task.

1. **Find the change.** Start from what the person names, or from the open list: `aob-states_/output/report.tsv` (one row per amendment, its changes not applied), `checks.json` (the basic checks by segment, C1, C2, C3) and `problems.json`. A change is `<series>/<seq>`. Read its entry in `changes.json`: its op, its path as read, the part its path reaches, and its cause (§A6, known issues). `output/lineage/<file>.json` gathers the same for one file, with its edits and the rules that acted on it.
2. **Find its clause in the gazette.** The amendment's export, `aob-ammend_/output/<file>.pdf.json`, gives the change's clause words, its quoted content as units, and its page. Read the text of that page, and look at the page image only when the text is in doubt. Compare three things: what the gazette prints, what the reading says (the text), and what the export made of it (the units).
3. **Name the cause, and the fix by the table above.** The words wrong: an edit. The words right, the units wrong: the reader. The units right, the path unresolved: the patcher, or an inference. Nothing printed explains it: a rename, or a known issue. Look for the same pattern elsewhere before fixing one case: a reader or patcher fix usually closes several changes.
4. **Make a free fix first.** A reader or patcher fix goes with a test that quotes the gazette's words and names the file. Run only the tests touched (`uv run pytest packages/docflow/tests/test_legal.py -k …`).
5. **Batch the paid fixes.** Gather every edit that reaches the ops step, then count before paying: run the amendments with `DOCFLOW_DEFER=review/tmp/defer.jsonl` (and `DOCFLOW_CACHE_ONLY=gemini` for any run that must be free), then `uv run --no-sync docflow batch src/flow.yml review/tmp/defer.jsonl --storage .storage --count`. Tell the person which documents are re-read and the cost, and send the batch only on their word. Then run again with `DOCFLOW_DEFER` still set: every answer is in the cache (docflow.md §P11b).
6. **Refresh once.** `make refresh` in `cabsec_new/flow` (the versions and amendments, the states, then both again so the new problems reach the studios); its last lines say how many changes are not applied. Do not loop refreshes: one per batch of fixes.
7. **Check.** The basic checks by segment (`versions/checks.html`, `checks.json`, the run appended to `checks-history.jsonl`): C1, C2, C3 and phase B, before and after. A fix is good when the count not applied falls and **none fewer apply** (no change that applied before now fails), and C2, C3 and phase B still pass. Compare `report.tsv` before and after to be sure.
8. **Record it.** The commit message in `doc` says what was read wrong, the file, and the counts ("150 -> 149 not applied, none fewer"). Mark the call in `decisions.yml` (status, date, by whom, why) and the rename's `note`. Update `known.yml` for what is left, and this spec for any new reading rule, patcher rule or inference.

### For a person in the studio

1. **Open the studio** for the amendments: `make studio` in `cabsec_new/flow/aob-ammend_` (it sets the Gemini project from gcloud). The versions' studio is `make studio` in `aob-rules_`.
2. **Find the change.** Either filter the issues to the `states_` codes (stage 3: a change that does not fit the states), oldest series first, or start from `aob-states_/output/versions/checks.html`, where each segment's missing units and uncovered items name the changes behind them. "What this means" under an issue explains its code.
3. **Look at it.** Select the change: the inspector shows the part of the Rules before and after (or, not applied, the nearest part its path reaches) and the cause. Press the page button ("p.11 ›") to see the clause on the gazette page, and compare the page with the words read.
4. **Fix what the page shows.**
   * A word read wrong: at the Words level, select it, `Enter`, type it right, `Cmd+Enter`. It is saved to the file's edits (`conf/<file>.edits.yml`).
   * A change missing or wrong (an insert the reading missed): fix it in the Relations view.
   * The words are right but the change still fails, or the same mistake comes back across files: it is in the reader or the rules. Add a note for the flow (`n`) with the words as an example, and ask Claude to fix the reader or add a rule.
   * The gazette itself is silent, or the version mended its own wording: dismiss the issue with a note (`x`), or verify "Take the version's text". A rename the gazettes never print is a decision: ask for it to go in the renames list, with your reason.
5. **Run once, after several fixes.** "● N edits · re-run" shows what is waiting. An edited word that reaches the ops step makes Gemini read that notification again, a paid call, so gather your edits and press **Run** once rather than after each. (Claude can send them as one batch at half the price, §P11b: say so before pressing Run.) The run brings in the edits, rebuilds the states and runs the checks.
6. **Read the result.** The run ends with "Issues 14 → 12: 2 closed, 0 new" and the model calls it made. Open any new issue it lists: a fix can close one change and open another. Then look at the segment's check in `versions/checks.html` again; reload the studio to see the new issues.

## A12. The ops spec: the `amendment` object

Merged here on November 22, 2026 from "AoB Amendment Extraction – Requirements" (0.2, October 30), brought up to the code. It is the contract between the amendments task (§A5) and the patcher (§A6): the task records **what the text says to change**, in the notification's own words and order, never what the change means, and the patcher applies it to the Rules in force the day before. Hindi script, OCR and applying the ops are not its part.

**Input.** A GovDoc file per PDF from `aob-ammend_`, one document per notification (a PDF may hold two or three), English blocks only, each word with its box. The notification's series, S.O. number, dates and URL come from `items.json`.

**Output.** The ops are stored in the GovDoc file as annotations and relations (below), and `amendment_export` writes `output/<name>.json` per PDF: `file` (name, id, pages, source, sha256) and `documents`, each with its `amendment`:

```json
{
  "amendment": {
    "schema_version": "1.0",
    "in_force": { "date": "2021-07-06", "basis": "at_once" },
    "extracted_by": { "tool": "amendment_export", "version": 65, "at": "2026-10-30T15:30:00+05:30" },
    "ops": [
      {
        "seq": 1,
        "source_ref": "2(i)",
        "op": "omit",
        "akn_type": "repeal",
        "target": {
          "cited": [
            { "type": "schedule", "num": "2" },
            { "type": "ministry", "heading": "MINISTRY OF CONSUMER AFFAIRS, FOOD AND PUBLIC DISTRIBUTION", "heading_hi": "UPBHOKTA MAMLE, KHADYA AUR SARVAJANIK VITARAN MANTRALAYA" },
            { "type": "department", "num": "B", "heading": "DEPARTMENT OF FOOD AND PUBLIC DISTRIBUTION" },
            { "type": "entry", "num": "14" }
          ],
          "eId": null
        },
        "expect": "Directorate of Vanaspati, Vegetable Oils and Fats.",
        "flags": []
      }
    ]
  },
  "notification": { "series": ___, "number": "S.O. ____(E)", "date": "2021-07-06", "url": "https://cabsec.gov.in/..." }
}
```

| Field | Required | Description |
| --- | --- | --- |
| `seq` | Yes | 1-based order; the patcher applies ops strictly in this order |
| `source_ref` | Yes | Clause label as printed, e.g. `2(i)`, `2(a)(ii)`, `2(b)(i)(A)` |
| `op` | Yes | One of the operations in section 4 |
| `akn_type` | Yes | Matching Akoma Ntoso `textualMod` type |
| `target` | All except `insert` | Node(s) the op acts on (section 5) |
| `position`, `anchor` | `insert` only | `after` / `before` / `first_child` / `last_child`, and the node it is relative to |
| `expect` | When the text states it | Current text of the target, quoted in the notification; the patcher checks it before applying |
| `old`, `new` | `substitute_text` only | Exact words removed and inserted |
| `content` | `insert`, `replace` | New node(s) as a subtree in the same format as the Rules document |
| `scope` | `replace` only, when stated | `heading` (the heading alone) or `children` (what is under it alone); unset, the whole node |
| `flags` | Yes | Review flags (section 7); empty when clean |


Each op also carries `relation` (its `legal:` relation in the GovDoc file), `words` (its first and last word) and `boxes`, so a reader sees it on the page. `eId` stays `null`: resolving a cited path needs the Rules in force that day, so it is the patcher's.

**In the GovDoc file** (`govdoc.md` §6.6, §10.4), written by the model tagger's three steps from one model answer (`docflow.md` Part M):

| The ops spec | GovDoc (`specs/govdoc.md` §6.6, §10.4) |
| --- | --- |
| a clause (`source_ref`) | a `core:division` role annotation, its marker as printed |
| `content`, the quoted new text | a `core:quoted_text` role annotation; its entries are divisions inside it |
| `target`, `anchor` (`cited`) | a `core:provision` entity annotation on the words that cite it, with the path as its `provision` value |
| an op | a `legal:` relation from the provision to the quoted text, named after its `akn_type`: `legal:repeal`, `legal:insertion`, `legal:replacement`, `legal:substitution`, `legal:renumbering`; `seq`, `position`, `expect`, `old`, `new`, `new_num` as value arguments; `ref_seq` an argument pointing at the earlier relation |
| `in_force` | a `core:date` entity annotation, and its basis |


### The five operations

Each maps to one Akoma Ntoso `textualMod` type: `substitution` changes words inside a node, `replacement` swaps whole nodes.

| `op` | `akn_type` | Gazette wording | Required fields |
| --- | --- | --- | --- |
| `omit` | `repeal` | "… shall be omitted" | `target`, `expect` if quoted |
| `insert` | `insertion` | "after entry X, the following entry/entries/heading shall be inserted" | `position`, `anchor`, `content` |
| `replace` | `replacement` | "for entry X / for the heading …, the following … shall be substituted" | `target`, `content`, `expect` if quoted |
| `substitute_text` | `substitution` | "in entry X, for the words …, the words … shall be substituted" | `target`, `old`, `new` |
| `renumber` | `renumbering` | "entry X shall be renumbered as entry Y" | `target`, `new_num` |

Rules:

1. One instruction that names several targets ("existing entries 24, 25, 26, 27 and 28 shall be omitted") becomes one op with several targets, not five ops.
2. Renumbering that happens only as a side effect of a `replace` (8A, 8B becoming 8A, 8B, 8C) is not emitted as a separate `renumber` op. The new numbers live in the `content` nodes.
3. A notification that renames a heading by substituting the whole heading is a `replace`. Whether that is a rename is decided later (section 9).
4. `content` uses the same node types as the Rules document: `ministry`, `department`, `secretariat`, `part` (e.g. "PART I", its opening words in `text`), `group_heading` (e.g. "XIII. Right to Information."), `entry`, `item`, `proviso`, `note`, `explanation`. Each node carries `num` (string, e.g. `"20B"`), `text`, and `heading_hi` where the Hindi name is given.

### Target addressing

Every `target` and `anchor` is the locator exactly as the notification states it, a path from the schedule down; the task does not guess stable ids.

| Path step `type` | Identified by | Example |
| --- | --- | --- |
| `schedule` | `num`: `1` or `2` | "THE SECOND SCHEDULE" → `2` |
| `ministry` | `heading` (English), `heading_hi`, and `num` in Schedule 1 | "MINISTRY OF PERSONNEL, PUBLIC GRIEVANCES AND PENSIONS (KARMIK, LOK SHIKAYAT TATHA PENSION MANTRALAYA)" |
| `department` | `num` (letter or roman numeral) and `heading` | "B. DEPARTMENT OF FOOD AND PUBLIC DISTRIBUTION" |
| `group_heading` | `num` (roman) and `text` | "XIII. Right to Information." |
| `entry` | `num` as a string | `"14"`, `"20A"` |
| `item` | `num` as printed | `"k"` from "item (k)" |

Rules:

1. Headings are stored in the notification's spelling, with the Hindi part split into `heading_hi`. Case is preserved; matching is the patcher's job.
2. "as so substituted" or "as so inserted" means the step refers to a node created by an earlier op in the same notification. Set `"ref_seq": <seq of that op>` (today on the op, not the path step: §A5, not yet).
3. A range ("entries 24 to 28") is never expanded, because the current Rules may hold entries such as 25A inside it. Keep `{ "type": "entry", "range": ["24", "28"] }` for the patcher to resolve. Numbers the notification lists one by one ("24, 25, 26, 27 and 28") become one path per number.
4. Context carried from a parent clause (the heading and sub-heading in clause 2's opening sentence) is copied in full into every child op's path. Each op must stand alone.

### The drafting formulas

The notifications follow a small set of formulas, each mapped so. The scans' quoted schedules have more shapes, read by the export (§A5, how the export reads the quoted schedules).

| Pattern in the text | Produces |
| --- | --- |
| "1. (1) These rules may be called …" | `notification.title` if missing; not an op |
| "(2) They shall come into force at once." | `in_force: { date: <notification date>, basis: "at_once" }` |
| "(2) They shall come into force on the …" | `in_force: { date: <that date>, basis: "stated" }` |
| "In the … Rules, 1961, in THE SECOND SCHEDULE, under the heading "…", under the sub-heading "…"" | Path context inherited by every child clause |
| "(a) in the FIRST SCHEDULE," / "(b) in the SECOND SCHEDULE," | Schedule step for its sub-clauses |
| "entry N relating to '…' shall be omitted" | `omit`, `expect` = the quoted text |
| "in entry N, item (k) shall be omitted" | `omit` on path `… entry N / item k` |
| "after entry N, the following entry/entries shall be inserted, namely: - '…'" | `insert`, `position: after`; each quoted line becomes one `content` node |
| "after entry N, the following heading and entry shall be inserted" | `insert` with a `group_heading` node followed by `entry` nodes |
| "for entry N, the following entry shall be substituted" | `replace` |
| "in entry N, for the words, figures and brackets '…', the words, figures and brackets '…' shall be substituted" | `substitute_text` with `old` and `new` |
| "for the sub-heading …, the following sub-heading shall be substituted" | `replace` on the department node, heading only (`scope: "heading"`) |
| "under the heading …, for the existing sub-headings / for the entries, the following … shall be substituted" | `replace` on the heading's node, what is under it only (`scope: "children"`): the heading stays, its sub-headings or entries become the `content` |
| "for existing headings 'X' and 'Y', the following headings shall be substituted" | One `replace` with two targets and N content nodes |
| "after the heading … and entries thereunder, the following heading and entries shall be inserted" | `insert` of a whole `ministry` subtree, including departments and entries |

Text handling:

1. Quoted content is copied verbatim, including the final full stop, abbreviations and Act citations like "(1 of 2024)". Normalise only curly vs straight quotes and line-break hyphenation.
2. A quoted entry's leading number ("24. Directorate of …") goes to `num`; the rest goes to `text`.
3. Notes, provisos and explanations inside an inserted block belong to the entry they follow (today they are its siblings in `content`: §A5, not yet) (e.g. the "Note: - The Ministries concerned …" under entry 1 of the Ministry of Cooperation).
4. A heading with a bracketed Hindi transliteration is split: English into `heading`, the bracket's contents into `heading_hi`.
5. Clause labels nest as printed: `2`, `(a)`, `(i)`, `(A)`. `source_ref` joins them without spaces, e.g. `2(b)(i)(A)`.

### Checks

`legal_ops_check` (`prefix: aob`) raises every doubtful case as an issue, a `read_` code (§A6, issues by stage), for a person to fix in the studio, where the fix is kept on every later run:

1. every clause that says "shall be" has at least one op, and every op points back to a real clause (`read_clause_missed`);
2. `seq` runs 1..N in text order, and every `ref_seq` points to an earlier op that makes or replaces a node (`read_sequence`);
3. every verbatim string (`expect`, `old`, `new`, the quoted text) occurs in the text after normalising quotes and hyphenation (`read_quote_mismatch`, an error); a passage across a page break is seen in its words (`read_page_break`, information);
4. a path step that could match more than one node (`read_path_unsure`); a new heading with no Hindi name (`read_hindi_missing`, information); the model tagger's `core:model_unanchored`, `core:model_invalid`.

The model's flags keep their prompt's names (`ambiguous_target`, `page_break_inside`, `hindi_missing`) in `flags`.

### Acceptance tests

The four samples are the flow's expected outputs (`aob-ammend_/src/expected/`, checked by `docflow expect`): the export must match each `ops` list exactly, `extracted_by` aside. T1 = no. 385, T2 = 382, T3 = 355, T4 = 362.

| Test | Sample | Expected ops |
| --- | --- | --- |
| T1 | Consumer Affairs, Dept. B (Food & PD) | 3 × `omit` (entries 14, 15, 18, each with `expect`); 1 × `insert` after entry 23, content entry "24" "Directorate of Sugar and Vegetable Oils (DSVO)." |
| T2 | Personnel, Dept. A (DoPT) | `insert` 2A after 2; `insert` 5A and 5B after 5 (one op, two nodes); `substitute_text` in 20A (1947 → 1988 Act); `insert` 20B after 20A; `substitute_text` in 26 (1949 Rules → 1965 Rules); `insert` group heading XIII + entry 46 after 45. Six ops, no flags (the page break between (i) and (ii) falls between ops). |
| T3 | Health and Family Welfare, Dept. A | 1 × `omit`, path `… entry 16 / item k`, no `expect` |
| T4 | Ministry of Cooperation (Schedules 1 and 2) | Schedule 1: `replace` of department heading (i) under Agriculture; `replace` of headings 8A, 8B with 8A Cooperation, 8B Corporate Affairs, 8C Culture. Schedule 2: `replace` of Agriculture sub-heading A; one `omit` with five targets (entries 24, 25, 26, 27, 28) under it, each path carrying `ref_seq` to the previous op ("as so substituted"); `replace` of entry 2 under Fertilizers Dept. B; `insert` of the whole Ministry of Cooperation subtree after Consumer Affairs Dept. B, with entries 1–9+ and the note and proviso as child nodes. Flag `page_break_inside` on the last op. |

Still to add: a notification with a stated future commencement date (`in_force.basis: "stated"`), and one with a clause no op matches (the file still written, the clause raised).

### Meaning, later

What a change means (a rename or a new unit, a transfer of subjects) is not the ops' to say. It goes in a separate `effects` layer written by a person or a later task, for the ministries over time (§A7):

```json
"effects": [
  { "kind": "rename", "from": "dept-agri-coop-fw", "to_heading": "Department of Agriculture and Farmers Welfare", "op_seq": 1 },
  { "kind": "create", "entity": "min-cooperation", "op_seq": 6 },
  { "kind": "transfer_subjects", "from": "dept-agri-fw", "to": "min-cooperation", "op_seq": [4, 6] }
]
```
