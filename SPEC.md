# cabsec_all: Spec

The Cabinet Secretariat (cabsec.gov.in) publishes three sets of documents this repo archives:

1. **Council of Ministers orders** in four categories (Council of Ministers lists, Change in Portfolios, Swearing of
   New Ministers, Initial Compositions), 1947 to today.
2. **Amendments to the Allocation of Business (AOB) Rules, 1961**, series no. 1–386.
3. **Amendments to the Transaction of Business (TOB) Rules, 1961**, nos. 1–75.

This spec covers only getting the files in reliably: download → Hugging Face → Wayback → archive.org. OCR and
extraction (what `~/orgpedia/cabsec` does today) come later and stay in that repo.

One repo, one HF dataset and one archive.org collection (`india-cabsec`). Every target takes `C=council|aob|tob`
(default: all three).

| Mode | Target | What |
|---|---|---|
| **Setup** | `make setup` | discover_full → onetime_seed (council) → download → HF push → archive.org (first `SETUP_ARCHIVE_LIMIT`=55 of each set) → status. No Wayback. |
| **Update** | `make update` | new entries only: discover → download → Wayback → archive.org → HF → status |
| **Backfill** | `make backfill WHAT=archive\|wayback [C=…] LIMIT=n` | work through the backlog in chunks |

## Decisions

| # | Decision | Choice |
|---|---|---|
| A1 | Scope | The three sets above, English files only. |
| A2 | Existing files | **Seed** council from HF `Orgpedia/cabsec` (912 PDFs) plus `~/orgpedia/cabsec/LFS/cabsec/pdfs` (9 PDFs, 2024–26). **Copy only**; the old repo and dataset are not touched. AOB and TOB are downloaded fresh. |
| B1 | source_key | council: `<site folder>/<file stem>`, e.g. `changeinportfolio/1_Upload_1595`. aob, tob: the site's `sno` (series number). |
| B2 | file_key | council: same as source_key. aob, tob: file stem (`1_Upload_4249`), so a re-uploaded amendment becomes a new file in the same item. |
| B3 | item_id | council: `<abbr>.<YYYY-Mon-DD>.<n>`, where `abbr` is `com` (Council of Ministers), `cip` (Change in Portfolios), `snm` (Swearing of New Ministers) or `icm` (Initial Compositions of Council of Ministers). `n` is counted per category and date, ordered by upload number, and **frozen** once given. aob, tob: `<sno>`, unpadded. |
| B4 | archive.org identifier | `in.gov.cabsec.council.<item_id>`, `in.gov.cabsec.aob.<item_id>`, `in.gov.cabsec.tob.<item_id>` |
| B5 | Curated inputs | `overrides.json` per collection (§2): 5 AOB date typos, 1 council date. |
| C1 | NAME / HF dataset | `cabsec_all` → `LFS/cabsec_all/`, dataset `Orgpedia/cabsec_all` (new, public, `viewer: false`). |
| C2 | Folders in the dataset | **Site file names kept**: `council/pdfs/<site folder>/1_Upload_N.pdf`, `aob/pdfs/1_Upload_N.pdf`, `tob/pdfs/1_Upload_N.pdf`. No year folders. |
| C3 | Symlinks | `input/documents/<C>/pdfs/<same sub path>` |
| C4 | File types | PDF only (all 1,405 entries are `.pdf`). Type checked from the bytes. |
| C5 | Replaced files | council: never re-downloaded, warn if `Last-Modified` or size changes. aob/tob: a new upload number under an existing sno is a new file_key, uploaded to the same item. |
| D1 | Metadata | Table in §5, with one real example per collection. |
| D2 | Title language | All English. `language=eng`. |
| D3 | Collection | One collection, `india-cabsec`, for all three sets; `opensource` until archive.org creates it (`IA_COLLECTION`). The sets are told apart by identifier prefix and `subject` (§5). |
| D4 | First upload | 55 of each set (165 total), oldest first. Then `update_archive_metadata IA_COLLECTION=india-cabsec` and `backfill WHAT=archive IA_COLLECTION=india-cabsec`. |
| D5 | File name inside the archive.org item | `<identifier>.pdf`, e.g. `in.gov.cabsec.council.cip.1995-Nov-22.1.pdf`, `in.gov.cabsec.aob.1.pdf`. HF keeps the site names (C2). |
| E1 | Wayback in setup | **None** (`SETUP_WAYBACK=0`). `backfill WHAT=wayback LIMIT=n` links files and refreshes the archive.org metadata afterwards. |
| E2 | WAYBACK_REUSE | `30d`. All files are ≤ 11 MB, so the default poll timeout is fine. |
| F1 | "New" | A new source_key, never a recent date. (The 22 council files below are pre-2019 orders the 2021 crawl never saw.) |
| F2 | Changes | `discover_full` logs edits, removals and replacements to `input/documents/<C>/changes/<date>.json`. |
| F3 | Running it | `make update`, run by hand. No scheduler. |
| G1 | Delisted files | 8 files from the old `documents.yml` that the site no longer lists (they still download) are kept as items with `listed: false`, plus `same_file_as` where the bytes match another item. |

## 1. Source website (studied 2026-10-24)

The site is PHP. Every list page loads its rows as JSON from `https://cabsec.gov.in/ajax_page_data.php?page_id=<id>`,
optionally `POST year_id=<YYYY>`. Rows look like `{"title", "dateformat" | "description", "fileinfo": "<path>|<size>"}`,
and the file is at `https://cabsec.gov.in/writereaddata/<path>`. Older council orders are only on the server-rendered
`/archived/<sec>/<year>` pages.

| Set | List | Count |
|---|---|---:|
| Council: current (2019+) | `page_id=18` council, `19` swearing, `20` portfolios (`POST year_id` per year 2019–2026 returns the same rows) | 37 |
| Council: archived | `/archived/1/<y>` council (55 years), `/archived/3/<y>` swearing (11), `/archived/5/<y>` portfolios (68), `/archived/88/<y>` initial compositions (23); year list from `/archived/<sec>` | 899 |
| Council: delisted | in `documents.yml`, no longer on any list | 8 |
| AOB | `page_id=205` (page `/allocationofbusinessrules/amendment/`). One GET returns all 386 rows. | 386 |
| TOB | `page_id=208` (page `/transactionofbusiness/tobamendment/`). One GET returns all 75 rows. | 75 |

Findings, each with its design consequence:

- **HEAD is broken.** It returns `200 text/html`, 62,438 bytes, for every URL, including ones that don't exist.
  → Never use HEAD. Probe with `GET` + `Range: bytes=0-0`, which returns a real `206` with `Content-Range` total size
  and `Last-Modified`, or a real `404`.
- **Range works** (`Accept-Ranges: bytes`). `Last-Modified` is present. There is **no ETag**. → Resume `.part` files;
  watch `Last-Modified` and size for in-place replacement.
- **A missing file returns a real 404** (an HTML body). → Mark it `failed:404`, and check the bytes as usual.
- **URLs move.** The 4 Change-in-Portfolio files from 2026 in `documents.yml` use `writereaddata/changeinportfolio/2026/…`,
  which now returns 404. The site now lists them under `…/english/…`. → source_key drops the `english`/year segment,
  and the seed maps the old URLs to the current ones.
- **Upload numbers aren't unique across folders.** `1_Upload_1266.pdf` exists in both `councilofministers/` and
  `changeinportfolio/`. → The council source_key and HF path include the site folder.
- **Many council orders share a date.** There are 944 items on 672 dates. Counted per category and date, 803 of the
  868 pairs have a single item, 55 have 2, 9 have 3, and one has 4 (`cip.2003-May-24`). → A `.<n>` counter within the category.
- **Files get moved between categories under new upload numbers.** `changeinportfolio/1_Upload_1573` and
  `swearingofnewministers/1_Upload_3196` are byte-identical (both 21/11/1990). `changeinportfolio/1_Upload_1722` (08/09/2003)
  looks re-posted as `swearingofnewministers/1_Upload_3131`. → Keep both, and link them with `same_file_as` (by sha1).
  `changeinportfolio/1_Upload_2797` and `2794` are another byte-identical pair.
- **Dates.** archived rows: `"55/1/1/1995- Cab. dated (22/11/1995) (45.1 KB)"`. Current rows: `dateformat` of
  `" (15.10.2026) "` (council, swearing) or `" 15 October, 2026 "` (portfolios). TOB: `" 28.03.1962 "`. AOB: the date is
  inside the title, `"Order dated  9/04/1961"`, and the Gazette notice is in `description` (`"S.O. 857  April, 14 1961"`).
  5 AOB titles have typos (§2). → Lenient parsing. A council item whose date won't parse is **held** (no item_id)
  until `overrides.json` fixes it.
- **The AOB series number is official.** The page says "upto series no. 386", and `sno` runs 1…386 with no gaps.
  TOB `sno` runs 1…75 with no gaps. → Use `sno` as the item_id. If the site ever renumbers, log it as a change; never rename.
- **Files are replaced in place.** `councilofministers/1_Upload_4119` (10.06.2024) is 198,860 bytes in the old local
  copy and 636,550 bytes on the site today. → `onetime_seed` compares every seed copy's size with the site and leaves a
  mismatch for `download`, which fetches the current version. The old copy stays in `~/orgpedia/cabsec`.
- **Sizes.** Council is about 2.3 GB, AOB 145 MB, TOB 13 MB. The largest file is 10.2 MB.
- Politeness: browser User-Agent, 1 s between file downloads, 0.5 s between list pages.

Seed coverage, after mapping old paths to current URLs:

| | Council |
|---|---:|
| Items (listed 936 + delisted 8) | 944 |
| Copied from HF `Orgpedia/cabsec` | 913 (912 from `documents.yml` + `swearNewMin/2024/1_Upload_3869`) |
| Copied from `~/orgpedia/cabsec/LFS` | 9 |
| **To download** (`changeinportfolio` 3083–3087, 3304, 3846, 3848, 4120; `councilofministers` 3106, 3107, 3194, 3195, 3847, 3849; `initial_compositions…` 2005, 2007; `swearingofnewministers` 3129–3133) | **22** |

AOB (386) and TOB (75) are downloaded in full. That's 483 downloads in total.

## 2. Naming

```
council  item_id = <abbr>.<YYYY-Mon-DD>.<n>   e.g. cip.1995-Nov-22.1
         archive.org : in.gov.cabsec.council.cip.1995-Nov-22.1   file in.gov.cabsec.council.cip.1995-Nov-22.1.pdf
         HF / LFS    : council/pdfs/changeinportfolio/1_Upload_1595.pdf

aob      item_id = <sno>                       e.g. 386
         archive.org : in.gov.cabsec.aob.386                     file in.gov.cabsec.aob.386.pdf
         HF / LFS    : aob/pdfs/1_Upload_4249.pdf

tob      item_id = <sno>                       e.g. 75
         archive.org : in.gov.cabsec.tob.75                      file in.gov.cabsec.tob.75.pdf
         HF / LFS    : tob/pdfs/1_Upload_3982.pdf
```

| abbr | Category (site name) | Site folder | Items |
|---|---|---|---:|
| `com` | Council of Ministers | `councilofministers` | 248 |
| `cip` | Change In Portfolios | `changeinportfolio` | 644 |
| `snm` | Swearing of New Ministers | `swearingofnewministers` | 18 |
| `icm` | Initial Compositions of Council of Ministers | `initial_compositions_of_council_of_ministers` | 34 |

The longest identifier is 39 characters. Examples: `icm.1947-Aug-15.1` is the first item, `com.2026-Oct-15.1` the latest,
and `snm.1990-Nov-21.1` is the swearing-in on the same date as `cip.1990-Nov-21.1`.

- **Council counter.** In the one-time setup, items with the same category and date are numbered 1, 2, … in order of
  upload number. After that the ids are **frozen** in `items.json`. A later order for an old date gets the next free `n`.
  A date fixed later (through an override) never renames an item that already has an id; only its metadata changes.
- **The category is fixed per source_key.** When the site moves a file to another category, it re-uploads it under a
  new upload number, which becomes a new item. The abbreviation of an existing item never changes.
- **Held entries.** If a council date won't parse, or falls outside 1947-08-15…today+30 days, the entry is held:
  it isn't downloaded or uploaded, and every run lists it.

### Overrides (`input/documents/<C>/overrides.json`)

| C | Key | Site value | Override | Evidence |
|---|---|---|---|---|
| council | `councilofministers/1_Upload_3889` (delisted) | none | `date: 2024-06-10` | Page 1: "New Delhi, the 10th June, 2024". An earlier version of `1_Upload_4119` (10.06.2024). It becomes `com.2024-Jun-10.1`, and 4119 becomes `com.2024-Jun-10.2`. |
| aob | 112 | `Order dated 162/8/1975` | `date: 1975-08-16` | Gazette S.O. 438(E), 19 Aug 1975 |
| aob | 113 | `Order dated 292/8/1975` | `date: 1975-08-29` | Gazette S.O. 461(E), 2 Sep 1975 |
| aob | 173 | `Order dated 16/091985` | `date: 1985-09-16` | Gazette S.O. 673(E), 16 Sep 1985 |
| aob | 261 | `Order dated 23/05/002` | `date: 2002-05-23` | Gazette S.O. 566(E), 24 May 2002 |
| aob | 292 | `Order dated 29/042008` | `date: 2008-04-29` | Gazette S.O. 1055(E), 30 Apr 2008 |

The AOB overrides change only the `date` metadata, never the id. The AOB dates are inferred from the Gazette date and
should be checked against the PDFs before upload.

### Delisted council items (`listed: false`)

| source_key | Date (2021 snapshot) | item_id | Note |
|---|---|---|---|
| `changeinportfolio/1_Upload_935` | 2009-05-28 | `cip.2009-May-28.1` | |
| `changeinportfolio/1_Upload_1476` | 2004-11-27 | `cip.2004-Nov-27.2` | |
| `changeinportfolio/1_Upload_1573` | 1990-11-21 | `cip.1990-Nov-21.1` | same bytes as `snm.1990-Nov-21.1` (`swearingofnewministers/1_Upload_3196`) |
| `changeinportfolio/1_Upload_1574` | 1990-11-21 | `cip.1990-Nov-21.2` | |
| `changeinportfolio/1_Upload_1711` | 2003-01-29 | `cip.2003-Jan-29.2` | |
| `changeinportfolio/1_Upload_1718` | 2003-05-24 | `cip.2003-May-24.3` | |
| `changeinportfolio/1_Upload_1722` | 2003-09-08 | `cip.2003-Sep-08.1` | probably re-posted as `snm.2003-Sep-08.1` (`1_Upload_3131`) |
| `councilofministers/1_Upload_3889` | 2024-06-10 (override) | `com.2024-Jun-10.1` | |

The dates come from the `index.html` snapshots in `Orgpedia/cabsec` (`pdfs/<cat>/<year>/index.html`, crawled 2021-08-30).

## 3. Repository layout

```
cabsec_new/
├── Makefile  SPEC.md  pyproject.toml  env.example  .gitignore
├── input/
│   ├── src/        common.py discover.py download.py link_wayback.py upload_archive.py status.py onetime_seed.py
│   ├── documents/
│   │   ├── council/  items.json downloads.json wayback.json archive.json overrides.json delisted.json changes/
│   │   │             pdfs/<site folder>/1_Upload_N.pdf -> ../../../../../LFS/cabsec_all/council/pdfs/...
│   │   ├── aob/      (same files)   pdfs/1_Upload_N.pdf -> …
│   │   └── tob/      (same files)   pdfs/1_Upload_N.pdf -> …
│   ├── hf/README.md
│   └── logs/
└── LFS/cabsec_all/     NOT in git; mirror of HF dataset Orgpedia/cabsec_all
    ├── council/pdfs/{councilofministers,changeinportfolio,swearingofnewministers,initial_compositions_of_council_of_ministers}/
    ├── aob/pdfs/
    ├── tob/pdfs/
    └── raw/<C>/<run>/      raw list responses (not pushed)
```

The code starts as a copy of the skill's `reference/`. `common.py` gains a `COLLECTIONS` table instead of a single
CONFIG, and every script takes `--collection`:

```python
COLLECTIONS = {
    "council": dict(ia_prefix="in.gov.cabsec.council.", hf_prefix="council/pdfs", source_page="https://cabsec.gov.in/councilofministers/changeinportfolios/"),
    "aob":     dict(ia_prefix="in.gov.cabsec.aob.",     hf_prefix="aob/pdfs",     source_page="https://cabsec.gov.in/allocationofbusinessrules/amendment/"),
    "tob":     dict(ia_prefix="in.gov.cabsec.tob.",     hf_prefix="tob/pdfs",     source_page="https://cabsec.gov.in/transactionofbusiness/tobamendment/"),
}
```

(Each item's `source_page` metadata is the exact list page it came from, e.g. `/archived/5/1995`.)

## 4. State files (`input/documents/<C>/`)

`items.json` (council):
```json
{
  "source_key": "changeinportfolio/1_Upload_1595",
  "item_id": "cip.1995-Nov-22.1",
  "category": "Change In Portfolios",
  "abbr": "cip",
  "site_folder": "changeinportfolio",
  "title_site": "55/1/1/1995- Cab. dated (22/11/1995)",
  "date": "1995-11-22",
  "file_url": "https://cabsec.gov.in/writereaddata/changeinportfolio/english/1_Upload_1595.pdf",
  "file_key": "changeinportfolio/1_Upload_1595",
  "list_url": "https://cabsec.gov.in/archived/5/1995",
  "listed": true,
  "size_site": "45.1 KB",
  "first_seen_utc": "…", "last_seen_utc": "…"
}
```

`items.json` (aob):
```json
{
  "source_key": "386", "item_id": "386",
  "title_site": "Order dated 22/07/2026", "date": "2026-07-22",
  "gazette": "S.O. 4040(E)", "gazette_date": "2026-07-23",
  "file_key": "1_Upload_4249",
  "file_url": "https://cabsec.gov.in/writereaddata/allocationbusinessrule/amendment/english/1_Upload_4249.pdf",
  "list_url": "https://cabsec.gov.in/ajax_page_data.php?page_id=205", "listed": true
}
```

`items.json` (tob): like aob, with `file_no: "1/20/1/2024-Cab"` and `date: "2025-01-13"`, and no gazette fields.

`downloads.json`, `wayback.json` and `archive.json` are as in the reference. Seeded rows have `status: "seeded"`,
`seed_source: "hf:Orgpedia/cabsec@f079e0b:pdfs/changePort/1995/1_Upload_1595.pdf"` (or `local:…`), and the old
`download_time` from `documents.yml`.

## 5. Targets

**discover / discover_full.**
- council `discover`: the current API (`page_id` 18/19/20, `POST year_id` for each year in the dropdown), plus the
  `/archived/<sec>` year list, fetching only years not seen before and the latest archived year.
- council `discover_full`: every archived year page as well (157 pages).
- aob, tob: one GET returns the whole list, so `discover` and `discover_full` are the same.
- A known file that is missing from a full walk is marked `listed: false` and logged. It is never deleted.

**onetime_seed (council only).**
- Runs `hf download Orgpedia/cabsec --repo-type dataset --include "pdfs/**/*.pdf"` into `LFS/_seed/` (not pushed).
- Maps each `documents.yml` key and HF path to a source_key (`changePort`→`changeinportfolio`, `councilMin`→`councilofministers`,
  `swearNewMin`→`swearingofnewministers`, `initCompo`→`initial_compositions_of_council_of_ministers`), and
  `…/2026/…` → `…/english/…`.
- **Copies** the file to `LFS/cabsec_all/council/pdfs/<folder>/<name>`.
- Checks: `%PDF` magic, and size against the site's `Content-Range` (from a `Range: 0-0` GET, 0.5 s apart).
  On a size mismatch it does not seed the file; it leaves it for `download` and reports it.
- Writes `status: "seeded"` with sha1. `~/orgpedia/cabsec` is read-only for this step.

**download.** As in the reference, except that it never sends HEAD.

**upload_archive.** `build_metadata()` per collection. Empty values are dropped, and `wayback_url` is included only when linked.

| Field | council (`in.gov.cabsec.council.cip.1995-Nov-22.1`) | aob (`in.gov.cabsec.aob.386`) | tob (`in.gov.cabsec.tob.75`) |
|---|---|---|---|
| collection | `opensource` → `india-cabsec` | same | same |
| mediatype | `texts` | `texts` | `texts` |
| title | `Change In Portfolios: 55/1/1/1995- Cab. dated 22/11/1995` | `Allocation of Business Rules, 1961: Amendment No. 386 (Order dated 22/07/2026)` | `Transaction of Business Rules, 1961: Amendment No. 75 (1/20/1/2024-Cab dated 13.01.2025)` |
| date | `1995-11-22` | `2026-07-22` | `2025-01-13` |
| creator, publisher | `Cabinet Secretariat, Government of India` | same | same |
| language | `eng` | `eng` | `eng` |
| subject | `Ministers`; `Change In Portfolios` (`Ministers` + one of the 4 categories) | `Allocation of Business Rules` | `Transaction of Business Rules` |
| category | `Change In Portfolios` (one of the 4 site names) | n/a | n/a |
| series_number | n/a | `386` | `75` |
| gazette | n/a | `S.O. 4040(E), 2026-07-23` | n/a |
| file_number | `55/1/1/1995- Cab.` | n/a | `1/20/1/2024-Cab` |
| source | `https://cabsec.gov.in/writereaddata/changeinportfolio/english/1_Upload_1595.pdf` | `…/allocationbusinessrule/amendment/english/1_Upload_4249.pdf` | `…/transactionofbusinessrulescomplete/tobamendment/english/1_Upload_3982.pdf` |
| source_page | `https://cabsec.gov.in/archived/5/1995` | `https://cabsec.gov.in/allocationofbusinessrules/amendment/` | `https://cabsec.gov.in/transactionofbusiness/tobamendment/` |
| source_last_modified | `Thu, 17 Jan 2019 08:05:16 GMT` | from download | from download |
| sha1 | from download / seed | | |
| listed | `false` only for delisted items | | |
| same_file_as | e.g. `snm.1990-Nov-21.1` on `cip.1990-Nov-21.1` | | |
| wayback_url | only after Wayback is linked | | |
| description | HTML table: title, date, category, source URL, source page, Wayback, downloaded, same file as | same, plus gazette | same |

All three sets go into the one `india-cabsec` collection. Subjects are kept to these few values so archive.org's
topic facet splits the collection cleanly: `Ministers` (with the council category as a second subject),
`Allocation of Business Rules` and `Transaction of Business Rules`. The council category is also in `category`.

**update_archive_metadata IA_COLLECTION=<new>.** Moves already-uploaded items to the new collection and refreshes their metadata.

**status.** Per collection: site counts against items, downloads, wayback and archive, held items, delisted items, and the
archive.org search count per prefix.

## 6. Hugging Face dataset

`Orgpedia/cabsec_all` (new), public, files only, `viewer: false`. The card is `input/hf/README.md` and describes the three
folders and the archive.org prefixes. `make sync_hf_push` uses `hf upload`. Pushing large sets in folders is the
fallback. `Orgpedia/cabsec` stays as it is.

## 7. Environment

`.env`: `HF_TOKEN` (write access to `Orgpedia`), `HF_REPO_ID` (optional, default `Orgpedia/cabsec_all`), `IA_ACCESS_KEY`,
and `IA_SECRET_KEY` (also used for SPN2). `env.example` ships with the repo.

Makefile ADAPT block:
```make
NAME                  := cabsec_all
C                     ?= council aob tob
IA_COLLECTION         ?= opensource   # then india-cabsec
SETUP_ARCHIVE_LIMIT   ?= 55
SETUP_WAYBACK         ?= 0
```

## 8. Out of scope

- OCR, translation, order extraction (`~/orgpedia/cabsec` flow).
- Hindi versions of the documents.
- Other cabsec pages (Complete AOB Rules, First/Second Schedule, Cabinet Committees, the TOB Rules text). Each is easy to
  add later as another set.
- GitHub Actions or a scheduler. `make update` is run by hand.
