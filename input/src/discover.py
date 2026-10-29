"""Discover documents on cabsec.gov.in and record them in input/documents/<collection>/items.json.

Usage: CABSEC_COLLECTION=<collection> discover.py [--full]

council: the current lists (ajax_page_data.php page_id 18/19/20, every year in the dropdown) and the archived
         lists (/archived/<1|3|5|88>/<year>). Without --full only archived years not seen before, plus the latest
         year of each section, are fetched. Files the site no longer lists come from delisted.json.
aob-ammend/tob-ammend: one request returns the whole list (page_id 205 / 208), so every run is a full walk.
aob-rules/tob-rules: the current version (page_id 206 / 207) and earlier versions (/archived/<30|17>/<year>),
         fetched like the council archive.

--full walks the whole site: updates changed entries, records replaced files, and marks entries no longer listed
as removed (their files and archive.org items are kept). overrides.json fixes site values (e.g. bad dates).
"""

import argparse
import datetime
import html
import json
import re
import time

from common import (
    COLLECTION,
    KIND,
    RAW_DIR,
    SITE,
    ChangeLog,
    MONTHS,
    get,
    parse_dmy,
    parse_month_name,
    read_json,
    read_records,
    same_file_map,
    sort_key,
    utc_now,
    write_records,
)

TRACKED = ("title_site", "date", "category", "file_url", "current")  # changes logged as metadata_changed
MIN_FULL_RATIO = 0.9  # don't mark entries removed if a full walk saw fewer than this share of known ones
LIST_DELAY = 0.5      # seconds between list pages
FIRST_DATE = "1947-08-15"


class Held(Exception):
    """make_item_id() can't name the entry yet (bad date, ...); the entry is retried every run."""


# ---------------------------------------------------------------- site

# Council categories: site folder under writereaddata/ -> abbr, name, current list (page_id, page), archived section
CATEGORIES = {
    "councilofministers": dict(abbr="com", name="Council of Ministers",
                               page_id=18, page="/councilofministers/councilofministers/", archived=1),
    "swearingofnewministers": dict(abbr="snm", name="Swearing of New Ministers",
                                   page_id=19, page="/councilofministers/swearingofnewministers/", archived=3),
    "changeinportfolio": dict(abbr="cip", name="Change In Portfolios",
                              page_id=20, page="/councilofministers/changeinportfolios/", archived=5),
    "initial_compositions_of_council_of_ministers": dict(abbr="icm", name="Initial Compositions of Council of Ministers",
                                                         page_id=None, page=None, archived=88),
}
AOB_PAGE_ID, TOB_PAGE_ID = 205, 208
# Complete rules: current version (page_id, page) and the archived section with the earlier versions
RULES = {
    "aob-rules": dict(page_id=206, page="/allocationofbusinessrules/completeaobrules/", archived=30),
    "tob-rules": dict(page_id=207, page="/transactionofbusiness/transactionofbusinessrules/", archived=17),
}


class Fetcher:
    """GET/POST with a polite delay; keeps every response under raw_dir."""

    def __init__(self, raw_dir):
        self.raw_dir, self.n = raw_dir, 0

    def __call__(self, url, params=None, data=None, name="page"):
        if self.n:
            time.sleep(LIST_DELAY)
        text = get(url, params=params, data=data)
        self.n += 1
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        (self.raw_dir / f"{self.n:04d}_{name}").write_text(text)
        return text


def api_rows(fetch, page_id, year=None):
    """Rows of ajax_page_data.php; the body has leading blank lines and is `0` when empty."""
    text = fetch(f"{SITE}/ajax_page_data.php", params={"page_id": page_id},
                 data={"year_id": year} if year else None, name=f"api_{page_id}_{year or 'all'}.json")
    rows = json.loads(text.strip() or "[]")
    return rows if isinstance(rows, list) else []


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(s or "")).strip()


def split_fileinfo(fileinfo):
    """'councilofministers/english/1_Upload_4295.pdf|8.2 MB' -> (path, size)"""
    path, _, size = (fileinfo or "").partition("|")
    return path.strip(), size.strip()


def stem(path):
    return re.sub(r"\.[A-Za-z0-9]+$", "", path.rsplit("/", 1)[-1])


def council_entry(path, title_site, date_site, list_url, size_site):
    """One council entry from a site file path such as changeinportfolio/english/1_Upload_1595.pdf."""
    folder = path.split("/", 1)[0]
    cat = CATEGORIES.get(folder)
    if not cat:
        print(f"\tWARNING: unknown council folder {folder!r} ({path}), skipped")
        return None
    key = f"{folder}/{stem(path)}"
    m = re.match(r"^(.*?)\s*dated\b", title_site, re.I)
    return {
        "source_key": key,
        "file_key": key,
        "file_url": f"{SITE}/writereaddata/{path}",
        "category": cat["name"],
        "abbr": cat["abbr"],
        "site_folder": folder,
        "title_site": title_site,
        "file_number": m.group(1) if m and re.search(r"\d", m.group(1)) else None,
        "date_site": date_site,
        "date": parse_dmy(date_site) or parse_month_name(date_site),
        "list_url": list_url,
        "size_site": size_site,
        "listed": True,
    }


def council_current(fetch):
    for folder, cat in CATEGORIES.items():
        if not cat["page_id"]:
            continue
        page = fetch(f"{SITE}{cat['page']}", name=f"page_{cat['abbr']}.html")
        years = sorted(set(re.findall(r'<option value="(\d{4})"', page)))
        rows = api_rows(fetch, cat["page_id"])
        for y in years:
            rows += api_rows(fetch, cat["page_id"], y)
        for r in rows:
            path, size = split_fileinfo(r.get("fileinfo"))
            if not path:
                continue
            date_site = clean(r.get("dateformat"))
            title = clean(f"{clean(r.get('title'))} {date_site}")
            e = council_entry(path, title, date_site, f"{SITE}{cat['page']}", size)
            if e:
                yield e


def archived_rows(text):
    """(description, href) per row of an /archived/<sec>/<year> table."""
    i = text.find("Sl.No.")
    j = text.find("</table>", i)
    if i < 0:
        return
    for row in re.findall(r"<tr.*?</tr>", text[i:j], re.S):
        hrefs = re.findall(r'href="([^"]+)"', row)
        cells = [clean(re.sub(r"<[^>]+>", " ", c)) for c in re.findall(r"<td.*?</td>", row, re.S)]
        if hrefs and len(cells) >= 2:
            yield cells[1], hrefs[0]


def archived(fetch, sec, full, items):
    """(path, title, date_site, list_url, size) per row of /archived/<sec>/<year>.

    Without full: only years no known item came from, plus the latest year.
    """
    seen_years = {m.group(0) for i in items.values() for m in [re.search(r"archived/\d+/\d{4}", i.get("list_url") or "")] if m}
    index = fetch(f"{SITE}/archived/{sec}", name=f"archived_{sec}.html")
    years = sorted(set(re.findall(rf"archived/{sec}/(\d{{4}})", index)))
    if not full and years:
        years = [y for y in years if f"archived/{sec}/{y}" not in seen_years] + [years[-1]]
    for y in sorted(set(years)):
        url = f"{SITE}/archived/{sec}/{y}"
        for desc, href in archived_rows(fetch(url, name=f"archived_{sec}_{y}.html")):
            path = href.split("writereaddata/", 1)[-1]
            m = re.search(r"\((\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{4})\)", desc)
            title = clean(re.sub(r"\s*\(\s*[\d.]+\s*(?:KB|MB|GB|B)\s*\)\s*$", "", desc))
            size = re.search(r"\(\s*([\d.]+\s*(?:KB|MB|GB|B))\s*\)\s*$", desc)
            yield path, title, m.group(1) if m else "", url, size.group(1) if size else ""


def council_archived(fetch, full, items):
    for cat in CATEGORIES.values():
        for row in archived(fetch, cat["archived"], full, items):
            e = council_entry(*row)
            if e:
                yield e


def list_council(full, items, fetch):
    seen = set()
    for e in [*council_current(fetch), *council_archived(fetch, full, items)]:
        if e["source_key"] not in seen:  # the current list wins over the archive
            seen.add(e["source_key"])
            yield e
    for d in read_json("delisted", []):  # files the site no longer lists, from the 2021 crawl
        if d["source_key"] in seen:
            print(f"\tdelisted.json: {d['source_key']} is listed on the site again")
            continue
        e = council_entry(d["path"], d.get("title_site", ""), d.get("date_site", ""), d.get("list_url"), d.get("size_site", ""))
        e["listed"] = False
        yield e


def list_aob(fetch):
    for r in api_rows(fetch, AOB_PAGE_ID):
        path, size = split_fileinfo(r.get("fileinfo"))
        desc = clean(r.get("description"))
        g = re.match(r"(.*?)\s+[A-Za-z]{3,}\s*,", desc)
        title = clean(r.get("title"))
        yield {
            "source_key": int(r["sno"]),
            "file_key": stem(path),
            "file_url": f"{SITE}/writereaddata/{path}",
            "title_site": title,
            "date_site": title,
            "date": parse_dmy(title),
            "gazette": g.group(1) if g else desc,
            "gazette_date": parse_month_name(desc),
            "description_site": desc,
            "list_url": f"{SITE}/allocationofbusinessrules/amendment/",
            "size_site": size,
            "listed": True,
        }


def list_tob(fetch):
    for r in api_rows(fetch, TOB_PAGE_ID):
        path, size = split_fileinfo(r.get("fileinfo"))
        date_site = clean(r.get("dateformat"))
        yield {
            "source_key": int(r["sno"]),
            "file_key": stem(path),
            "file_url": f"{SITE}/writereaddata/{path}",
            "title_site": clean(f"{clean(r.get('title'))} dated {date_site}"),
            "file_number": clean(r.get("title")),
            "date_site": date_site,
            "date": parse_dmy(date_site),
            "list_url": f"{SITE}/transactionofbusiness/tobamendment/",
            "size_site": size,
            "listed": True,
        }


def rules_entry(path, title_site, date_site, list_url, size_site, current):
    """One version of the complete rules, e.g. '(Upto Amendment Series No.299) (13/07/2011)'."""
    upto = re.search(r"Amendment\s+Series\s+No\.?\s*(\d+)", title_site, re.I)
    return {
        "source_key": stem(path),
        "file_key": stem(path),
        "file_url": f"{SITE}/writereaddata/{path}",
        "title_site": title_site,
        "date_site": date_site,
        "date": parse_dmy(date_site),
        "upto_amendment": int(upto.group(1)) if upto else None,
        "current": current,
        "list_url": list_url,
        "size_site": size_site,
        "listed": True,
    }


def list_rules(full, items, fetch):
    """The current version first (it wins), then the archived versions."""
    cfg = RULES[COLLECTION]
    seen = set()
    rows = []
    for r in api_rows(fetch, cfg["page_id"]):
        path, size = split_fileinfo(r.get("fileinfo"))
        if path:
            date_site = clean(r.get("dateformat"))
            rows.append((path, clean(f"{clean(r.get('title'))} {date_site}"), date_site, f"{SITE}{cfg['page']}", size, True))
    rows += [(*row, False) for row in archived(fetch, cfg["archived"], full, items)]
    for row in rows:
        e = rules_entry(*row)
        if e["source_key"] not in seen:
            seen.add(e["source_key"])
            yield e


# ---------------------------------------------------------------- ADAPT

def list_entries(full, items, raw_dir):
    """Yield one dict per document on the site (see the module docstring)."""
    fetch = Fetcher(raw_dir)
    if COLLECTION == "council":
        yield from list_council(full, items, fetch)
    elif COLLECTION == "aob-ammend":
        yield from list_aob(fetch)
    elif COLLECTION == "tob-ammend":
        yield from list_tob(fetch)
    else:
        yield from list_rules(full, items, fetch)


def assign_order(rec):
    """Order in which new entries get ids: amendments by sno; council (by site folder) and rules by upload number."""
    if KIND == "ammend":
        return sort_key(rec["source_key"])
    m = re.search(r"(\d+)$", rec["source_key"])
    return (rec.get("site_folder") or "", int(m.group(1)) if m else 0, rec["source_key"])


def make_item_id(entry, items):
    """Frozen id: council <abbr>.<YYYY-Mon-DD>.<n> (n per abbr and date), rules <YYYY-Mon-DD>.<n>, amendments <sno>.

    Only [A-Za-z0-9._-] allowed, IA_PREFIX + item_id <= 100 chars. Raise Held("reason") rather than guess:
    an archive.org identifier can never be renamed.
    """
    if KIND == "ammend":
        return str(entry["source_key"])
    date = entry.get("date")
    latest = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    if not date or not FIRST_DATE <= date <= latest:
        raise Held("bad_date")
    y, m, d = date.split("-")
    prefix = f"{entry['abbr']}." if KIND == "council" else ""
    prefix += f"{y}-{MONTHS[int(m) - 1].title()}-{d}."
    used = [int(i["item_id"][len(prefix):]) for i in items.values()
            if (i.get("item_id") or "").startswith(prefix) and i["item_id"][len(prefix):].isdigit()]
    item_id = f"{prefix}{max(used, default=0) + 1}"
    if not re.fullmatch(r"[A-Za-z0-9._-]+", item_id):
        raise Held("bad_identifier")
    return item_id


# ---------------------------------------------------------------- generic

def apply_overrides(entry, overrides):
    ov = overrides.get(str(entry["source_key"]))
    if ov:
        entry.update({k: v for k, v in ov.items() if k != "note"})
        entry["overridden"] = sorted(k for k in ov if k != "note")
    return entry


def upsert(items, entry, now, log):
    key = entry["source_key"]
    fields = {k: v for k, v in entry.items() if k != "source_key"}
    if fields.get("file_url"):
        fields.setdefault("file_key", key)
    else:
        fields["file_key"] = None

    rec = items.get(key)
    if rec is None:
        items[key] = {"source_key": key, "item_id": None, **fields, "status": "",
                      "first_seen_utc": now, "last_seen_utc": now, "removed_utc": None}
        log.add("new", None, source_key=key)
        return True

    rec["last_seen_utc"] = now
    if rec.get("removed_utc"):
        rec["removed_utc"] = None
        log.add("reappeared", rec.get("item_id"), source_key=key)
    if fields.get("file_key") != rec.get("file_key"):
        log.add("file_replaced", rec.get("item_id"), source_key=key,
                old={"file_key": rec.get("file_key"), "url": rec.get("file_url")},
                new={"file_key": fields.get("file_key"), "url": fields.get("file_url")})
    changed = [f for f in TRACKED if f in fields and rec.get(f) != fields[f]]
    if changed:
        log.add("metadata_changed", rec.get("item_id"), source_key=key, fields=changed,
                old={f: rec.get(f) for f in changed}, new={f: fields[f] for f in changed})
    rec.update(fields)
    return False


def mark_removed(items, seen, now, log):
    known = [k for k, r in items.items() if not r.get("removed_utc")]
    if known and len(seen & set(known)) < MIN_FULL_RATIO * len(known):
        print(f">>> Full walk saw only {len(seen & set(known))} of {len(known)} known entries; not marking removals")
        return
    for k in known:
        if k not in seen:
            items[k]["removed_utc"] = now
            log.add("removed", items[k].get("item_id"), source_key=k)


def assign(items, log):
    """Give new entries a frozen item_id, or hold them; set status ok / held:<reason> / no_file."""
    used = {r["item_id"] for r in items.values() if r.get("item_id")}
    for key in sorted(items, key=lambda k: assign_order(items[k])):
        rec = items[key]
        if not rec.get("file_url"):
            rec["status"] = "no_file"
            continue
        if rec.get("item_id"):
            rec["status"] = "ok"
            continue
        if rec.get("removed_utc"):
            continue
        old = rec.get("status")
        try:
            item_id = make_item_id(rec, items)
            if item_id in used:
                raise Held("duplicate_item_id")
            rec["item_id"], rec["status"] = item_id, "ok"
            used.add(item_id)
            if old and old.startswith("held"):
                log.add("released", item_id, source_key=key)
        except Held as e:
            rec["status"] = f"held:{e}"
            if rec["status"] != old:
                log.add("held", None, source_key=key, reason=str(e))


def main(args):
    items = read_records("items")
    overrides = read_json("overrides", {})
    full = args.full or not items or KIND == "ammend"
    log, now = ChangeLog(), utc_now()
    raw_dir = RAW_DIR / datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H%M%S")
    seen, new = set(), 0
    print(f"*** discover {COLLECTION} ({'full' if full else 'new only'}); {len(items)} known entries")
    try:
        for entry in list_entries(full, items, raw_dir):
            if entry["source_key"] in seen:
                print(f"\tWARNING: {entry['source_key']} listed twice, keeping the first")
                continue
            seen.add(entry["source_key"])
            new += upsert(items, apply_overrides(entry, overrides), now, log)
        if full:
            mark_removed(items, seen, now, log)
        assign(items, log)
        same = same_file_map(items, read_records("downloads"))
        for r in items.values():
            r["same_file_as"] = same.get(r.get("item_id"), [])
    finally:
        write_records("items", items)
        log.flush()

    statuses = {}
    for r in items.values():
        s = "removed" if r.get("removed_utc") else r.get("status")
        statuses[s] = statuses.get(s, 0) + 1
    print(f"*** Seen this run: {len(seen)}   new: {new}   total: {len(items)}   by status: {statuses}")
    print(f"*** Not listed on the site: {sum(1 for r in items.values() if not r.get('listed', True))}")
    held = sorted((str(k), r["status"]) for k, r in items.items()
                  if (r.get("status") or "").startswith("held") and not r.get("removed_utc"))
    if held:
        print(f"*** Held ({len(held)}): add a date to overrides.json and re-run: {held[:20]}")
    no_date = sorted(str(k) for k, r in items.items() if r.get("item_id") and not r.get("date"))
    if no_date:
        print(f"*** No date ({len(no_date)}), add one to overrides.json: {no_date[:20]}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--full", action="store_true", help="walk the whole site, update known entries, mark removals")
    main(p.parse_args())
