"""Upload files to archive.org (one item per active item), or refresh item metadata.

Usage:
    CABSEC_COLLECTION=council|aob|tob upload_archive.py [--scope new|all] [--window 7d] [--limit N] [--collection opensource]
    CABSEC_COLLECTION=council|aob|tob upload_archive.py --update-metadata [--collection opensource]

Identifier: IA_PREFIX + item_id, file <identifier>.<ext> (e.g. in.gov.cabsec.aob.386.pdf). Items go oldest
first (council by date, aob / tob by series number). A replaced file (new file_key) is uploaded under the same
name; archive.org keeps the old one in history/files/.
First run: --limit 55 into opensource (Community Texts), ask archive.org for the collection with those URLs,
then `--update-metadata --collection <new>` moves them and a plain run uploads the rest.
--update-metadata only calls modify_metadata for items whose metadata hash changed (never re-uploads).
"""

import argparse
import datetime
import hashlib
import html
import json
import sys

import internetarchive as ia

from common import (
    COLLECTION,
    active,
    ensure_file,
    file_ext,
    identifier_for,
    is_listed,
    is_new,
    load_env,
    parse_window,
    read_records,
    require_env,
    same_file_map,
    save_records,
    upload_order,
    utc_now,
    write_records,
)

DONE = ("downloaded", "seeded")
MAX_CONSECUTIVE_FAILURES = 5

# ---------------------------------------------------------------- metadata

CREATOR = "Cabinet Secretariat, Government of India"
LANGUAGE = "eng"  # MARC code
# council items also get their category, e.g. ["Ministers", "Change In Portfolios"]
SUBJECTS = {
    "council": ["Ministers"],
    "aob": ["Allocation of Business Rules"],
    "tob": ["Transaction of Business Rules"],
}


def human_date(iso):
    return datetime.date.fromisoformat(iso).strftime("%-d %B %Y") if iso else ""


def make_title(item):
    site = " ".join(item.get("title_site", "").replace("(", " ").replace(")", " ").split())
    sno = item["source_key"]
    if COLLECTION == "council":
        return f"{item['category']}: {site}" if site else f"{item['category']}, {human_date(item.get('date'))}"
    if COLLECTION == "aob":
        return f"Allocation of Business Rules, 1961: Amendment No. {sno} ({site})"
    return f"Transaction of Business Rules, 1961: Amendment No. {sno} ({site})"


def build_metadata(item, d, wb, collection):
    """All archive.org metadata for one item. Empty values are dropped."""
    title = make_title(item)
    wayback_url = wb.get("archive_url", "") if wb.get("link_success") else ""  # omitted when not linked
    source_page = item.get("list_url") or ""
    listed = is_listed(item)
    gazette = ", ".join(x for x in (item.get("gazette"), item.get("gazette_date")) if x) if COLLECTION == "aob" else ""

    def row(label, value):
        return f'<tr><td style="vertical-align: top"><b>{label}</b>:&nbsp;</td><td style="vertical-align: top">{value}</td></tr>'

    def link(href, text):
        return f'<a href="{html.escape(href)}">{html.escape(text)}</a>'

    rows = [row("Title", html.escape(title)), row("Date", html.escape(item.get("date") or ""))]
    if COLLECTION == "council":
        rows.append(row("Category", html.escape(item["category"])))
    else:
        rows.append(row("Amendment No.", html.escape(str(item["source_key"]))))
    if item.get("file_number"):
        rows.append(row("File number", html.escape(item["file_number"])))
    if gazette:
        rows.append(row("Gazette of India", html.escape(gazette)))
    rows.append(row("Source URL", link(item["file_url"], item["file_url"])))
    if source_page:
        rows.append(row("Source page", link(source_page, source_page)))
    if not listed:
        rows.append(row("Note", "No longer listed on cabsec.gov.in"))
    if wayback_url:
        rows.append(row("Wayback URL", link(wayback_url, "web.archive.org")))
    if d.get("download_time_utc"):
        rows.append(row("Downloaded", html.escape(d["download_time_utc"])))
    if item.get("same_file_as"):
        rows.append(row("Same file also posted as", ", ".join(
            link(f"https://archive.org/details/{identifier_for(i)}", i) for i in item["same_file_as"])))
    description = (
        f"<p>{html.escape(title)}, published by {html.escape(CREATOR)}.</p>\n"
        "<table>\n" + "\n".join(rows) + "\n</table>"
    )

    subjects = SUBJECTS[COLLECTION] + ([item["category"]] if COLLECTION == "council" else [])
    metadata = {
        "collection": collection,
        "mediatype": "texts",
        "title": title,
        "date": item.get("date") or "",
        "creator": CREATOR,
        "publisher": CREATOR,
        "language": LANGUAGE,
        "subject": subjects,
        "category": item.get("category") or "",
        "series_number": str(item["source_key"]) if COLLECTION != "council" else "",
        "file_number": item.get("file_number") or "",
        "gazette": gazette,
        "source": item["file_url"],
        "source_page": source_page,
        "source_last_modified": d.get("last_modified") or "",
        "sha1": d.get("sha1", ""),
        "listed": "" if listed else "false",
        "same_file_as": item.get("same_file_as") or [],
        "wayback_url": wayback_url,
        "description": description,
    }
    return {k: v for k, v in metadata.items() if v}


# ---------------------------------------------------------------- generic

def metadata_hash(metadata):
    return hashlib.sha1(json.dumps(metadata, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def upload(identifier, filename, path, metadata, keys):
    responses = ia.upload(
        identifier,
        files={filename: str(path)},
        metadata=metadata,
        access_key=keys[0],
        secret_key=keys[1],
        checksum=True,  # skip if the same file is already in the item
        retries=5,
        retries_sleep=30,
        validate_identifier=True,
    )
    bad = [r for r in responses if r.status_code != 200]
    if bad:
        raise RuntimeError(f"HTTP {bad[0].status_code}: {bad[0].text[:200]}")
    if not responses:
        print("\tfile already present in item (checksum match)")


def modify(identifier, metadata, keys):
    r = ia.modify_metadata(identifier, metadata, access_key=keys[0], secret_key=keys[1])
    if r.status_code == 200 or "no changes" in r.text.lower():
        return
    raise RuntimeError(f"modify_metadata HTTP {r.status_code}: {r.text[:200]}")


def select(items, downloads, archive, scope="all", window="7d", limit=0):
    win = parse_window(window)
    todo = []
    for item in sorted(items.values(), key=upload_order):
        d = downloads.get(item.get("file_key"), {})
        if not active(item) or d.get("status") not in DONE:
            continue
        if archive.get((item["item_id"], item["file_key"]), {}).get("upload_success"):
            continue
        if scope == "new" and not is_new(item, win):
            continue
        todo.append(item)
    return todo[:limit] if limit else todo


def run_upload(args, keys, items, downloads, wayback, archive):
    todo = select(items, downloads, archive, args.scope, args.window, args.limit)
    pending = len(select(items, downloads, archive))
    print(f"*** {COLLECTION}: to upload this run: {len(todo)} (scope={args.scope}, limit={args.limit or '-'}, "
          f"collection={args.collection}; {pending} pending overall)")

    uploaded, failed, consecutive = [], [], 0
    have_item = {k[0] for k, a in archive.items() if a.get("upload_success")}
    for idx, item in enumerate(todo):
        item_id, key = item["item_id"], item["file_key"]
        identifier = identifier_for(item_id)
        d = downloads[key]
        print(f"**** {item_id} [{idx + 1}/{len(todo)}]")
        record = {"item_id": item_id, "file_key": key, "identifier": identifier, "collection": args.collection,
                  "sha1": d.get("sha1"), "time_utc": utc_now()}
        try:
            if not wayback.get(key, {}).get("link_success"):
                print("\tno wayback link yet, uploading without wayback_url")
            path = ensure_file(d)
            metadata = build_metadata(item, d, wayback.get(key, {}), args.collection)
            upload(identifier, f"{identifier}.{file_ext(d)}", path, metadata, keys)
            if item_id in have_item:  # metadata sent with an upload only applies when the item is created
                modify(identifier, metadata, keys)
            have_item.add(item_id)
            record.update(upload_success=True, archive_url=f"https://archive.org/details/{identifier}",
                          metadata_sha1=metadata_hash(metadata), message="")
            uploaded.append(item_id)
            consecutive = 0
            print(f"\tUPLOADED: {record['archive_url']}")
        except Exception as e:
            record.update(upload_success=False, message=str(e)[:500])
            failed.append(item_id)
            consecutive += 1
            print(f"\tFAILED: {record['message']}")

        archive[(item_id, key)] = record
        save_records("archive", archive)
        if consecutive >= MAX_CONSECUTIVE_FAILURES:
            print(">>> Stopping: too many consecutive failures, re-run later")
            break
    return uploaded, failed


def run_update_metadata(args, keys, items, downloads, wayback, archive):
    updated, failed, todo, total = [], [], [], 0
    for item in sorted(items.values(), key=upload_order):
        a = archive.get((item.get("item_id"), item.get("file_key")))
        if not active(item) or not a or not a.get("upload_success"):
            continue
        total += 1
        key = item["file_key"]
        metadata = build_metadata(item, downloads.get(key, {}), wayback.get(key, {}), args.collection)
        h = metadata_hash(metadata)
        if h != a.get("metadata_sha1"):
            todo.append((item, a, metadata, h))
    print(f"*** {COLLECTION}: metadata changed: {len(todo)} of {total} items on archive.org (collection={args.collection})")

    for idx, (item, a, metadata, h) in enumerate(todo):
        try:
            modify(a["identifier"], metadata, keys)
            a.update(metadata_sha1=h, collection=args.collection, metadata_time_utc=utc_now())
            updated.append(item["item_id"])
            print(f"{item['item_id']} [{idx + 1}/{len(todo)}]: metadata updated")
        except Exception as e:
            failed.append(item["item_id"])
            print(f"{item['item_id']} [{idx + 1}/{len(todo)}]: FAILED {e}")
        save_records("archive", archive)
    return updated, failed


def show(item_id):
    """Print the metadata one item would get (no network, no credentials)."""
    items, downloads, wayback = read_records("items"), read_records("downloads"), read_records("wayback")
    same = same_file_map(items, downloads)
    item = next((i for i in items.values() if i.get("item_id") == item_id), None)
    if not item:
        raise SystemExit(f"no item {item_id!r} in {COLLECTION}")
    item["same_file_as"] = same.get(item_id, [])
    key = item["file_key"]
    print(f"identifier: {identifier_for(item_id)}   file: {identifier_for(item_id)}.{file_ext(downloads.get(key))}")
    print(json.dumps(build_metadata(item, downloads.get(key, {}), wayback.get(key, {}), "opensource"),
                     indent=2, ensure_ascii=False))


def main(args):
    if args.show:
        return show(args.show)
    load_env()
    keys = require_env("IA_ACCESS_KEY", "IA_SECRET_KEY")
    items, downloads = read_records("items"), read_records("downloads")
    wayback, archive = read_records("wayback"), read_records("archive")
    same = same_file_map(items, downloads)
    for i in items.values():
        i["same_file_as"] = same.get(i.get("item_id"), [])

    run = run_update_metadata if args.update_metadata else run_upload
    try:
        done, failed = run(args, keys, items, downloads, wayback, archive)
    finally:
        write_records("archive", archive)

    print(f"*** {'Updated' if args.update_metadata else 'Uploaded'}: {len(done)}")
    if done and not args.update_metadata:
        print("\n".join(f"https://archive.org/details/{identifier_for(i)}" for i in done))
    print(f"*** Failed: {len(failed)} {failed[:20]}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scope", choices=("new", "all"), default="all")
    p.add_argument("--window", default="7d", help="what --scope new means")
    p.add_argument("--limit", type=int, default=0, help="max uploads this run (0 = no limit)")
    p.add_argument("--collection", default="opensource")
    p.add_argument("--update-metadata", action="store_true", help="re-apply changed metadata to uploaded items")
    p.add_argument("--show", metavar="ITEM_ID", help="only print the metadata for one item")
    main(p.parse_args())
