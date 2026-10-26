---
pretty_name: Cabinet Secretariat (India) orders and rule amendments
language:
- en
tags:
- government
- india
- pdf
- council-of-ministers
viewer: false
---

# cabsec_all: Cabinet Secretariat, Government of India

Documents published by the Cabinet Secretariat at <https://cabsec.gov.in>, mirrored as plain files.
This dataset holds the files only. The metadata (titles, dates, source URLs, Wayback and archive.org links)
is in the GitHub repo under `input/documents/<collection>/`.

## Layout

The files keep the names they have on cabsec.gov.in (`writereaddata/<folder>/english/1_Upload_N.pdf`).

| Folder | What | Source page |
|---|---|---|
| `council/pdfs/councilofministers/` | Council of Ministers lists with portfolios | <https://cabsec.gov.in/councilofministers/councilofministers/> |
| `council/pdfs/changeinportfolio/` | Change in Portfolios orders | <https://cabsec.gov.in/councilofministers/changeinportfolios/> |
| `council/pdfs/swearingofnewministers/` | Swearing of New Ministers | <https://cabsec.gov.in/councilofministers/swearingofnewministers/> |
| `council/pdfs/initial_compositions_of_council_of_ministers/` | Initial Compositions of Council of Ministers | <https://cabsec.gov.in/archived/88> |
| `aob/pdfs/` | Amendments to the Government of India (Allocation of Business) Rules, 1961 | <https://cabsec.gov.in/allocationofbusinessrules/amendment/> |
| `tob/pdfs/` | Amendments to the Government of India (Transaction of Business) Rules, 1961 | <https://cabsec.gov.in/transactionofbusiness/tobamendment/> |

Older council orders come from the site's archive pages (`/archived/<1|3|5|88>/<year>`). A few files the site
no longer lists are kept as well.

## Also archived at

- archive.org, one item per document:
  - `https://archive.org/details/in.gov.cabsec.council.<abbr>.<YYYY-Mon-DD>.<n>`, where `abbr` is `com` (Council of
    Ministers), `cip` (Change in Portfolios), `snm` (Swearing of New Ministers) or `icm` (Initial Compositions).
    Example: `in.gov.cabsec.council.cip.1995-Nov-22.1`.
  - `https://archive.org/details/in.gov.cabsec.aob.<series no.>`, e.g. `in.gov.cabsec.aob.386`
  - `https://archive.org/details/in.gov.cabsec.tob.<no.>`, e.g. `in.gov.cabsec.tob.75`
- Wayback Machine: the original source URL of each file

## Updates

New documents are added by running `make update` in the GitHub repo. Files are never deleted.
