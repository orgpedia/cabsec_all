"""Download the current file of every active item, once per file_key.

Usage: CABSEC_COLLECTION=council|aob|tob download.py [--scope new|all] [--window 7d] [--limit N] [--retry-failed] [--delay 1]

--scope new  only files of items first seen within --window; all = every current file.

The file goes to LFS/cabsec_all/<HF_PREFIX>/<file_key>.pdf (the site's folder and name), with a symlink in
input/documents/<collection>/pdfs/. 404 and unknown-type responses are not retried until the file_key changes,
or with --retry-failed. Existing files are never re-downloaded.
"""

import argparse
import sys
import time
from collections import Counter

from common import (
    COLLECTION,
    fetch_file,
    file_ext,
    file_path,
    group_by_file,
    is_new,
    link_file,
    parse_window,
    read_records,
    rel_path,
    save_records,
    sha1_file,
    utc_now,
    write_records,
)

DONE = ("downloaded", "seeded")
PERSISTENT = ("failed:404", "failed:unknown_type")


def ensure_paths(d, items):
    """Refresh the symlink and the bookkeeping fields of a downloaded file."""
    ext = file_ext(d)
    path = file_path(d["file_key"], ext)
    if path.is_file() and path.stat().st_size != d.get("size"):
        print(f"\tWARNING {d['file_key']}: {path.name} has {path.stat().st_size} bytes, recorded {d.get('size')}")
    link_file(d["file_key"], ext)  # dangles until `make import` on a fresh clone
    d["source_keys"], d["paths"], d["format"] = [i["source_key"] for i in items], [rel_path(d["file_key"], ext)], ext


def main(args):
    items = read_records("items")
    downloads = read_records("downloads")
    all_groups = group_by_file(items)
    groups = all_groups
    if args.scope == "new":
        window = parse_window(args.window)
        groups = {k: g for k, g in all_groups.items() if any(is_new(i, window) for i in g)}

    status = {k: downloads.get(k, {}).get("status") for k in groups}
    todo = [k for k, s in status.items() if s not in DONE and (args.retry_failed or s not in PERSISTENT)]
    if args.limit:
        todo = todo[: args.limit]
    todo_set = set(todo)
    done = sum(1 for s in status.values() if s in DONE)
    print(f"*** {COLLECTION} scope={args.scope}: {len(groups)} files for {sum(map(len, groups.values()))} items; "
          f"{done} already downloaded, {len(todo)} to download now")

    downloaded, not_found, failed = [], [], []
    try:
        for key, group in groups.items():
            d = downloads.get(key)
            if d and d.get("status") in DONE:
                ensure_paths(d, group)
                save_records("downloads", downloads)
                continue
            if key not in todo_set:
                continue

            first = group[0]
            url = first["file_url"]
            n = len(downloaded) + len(failed) + len(not_found) + 1
            print(f"{key} [{n}/{len(todo)}] {first['item_id']} {url}")
            info, error = fetch_file(url, file_path(key))
            attempts = (d or {}).get("attempts", 0) + 1

            if not info:
                downloads[key] = {
                    "file_key": key,
                    "source_keys": [i["source_key"] for i in group],
                    "url": url,
                    "paths": [rel_path(key)],
                    "status": f"failed:{error}",
                    "attempts": attempts,
                    "current": True,
                    "last_attempt_utc": utc_now(),
                }
                (not_found if f"failed:{error}" in PERSISTENT else failed).append(key)
                print(f"\tFAILED {error}")
                save_records("downloads", downloads)
                time.sleep(args.delay)
                continue

            d = downloads[key] = {
                "file_key": key,
                "source_keys": [],
                "url": url,
                "paths": [],
                "size": info["size"],
                "sha1": sha1_file(info["path"]),
                "last_modified": info["last_modified"],
                "etag": info["etag"],
                "download_time_utc": utc_now(),
                "status": "downloaded",
                "format": info["format"],
                "attempts": attempts,
                "current": True,
            }
            ensure_paths(d, group)
            downloaded.append(key)
            print(f"\tok {info['format']} ({info['size']} bytes)")
            save_records("downloads", downloads)
            time.sleep(args.delay)
    finally:
        for key, d in downloads.items():
            d["current"] = key in all_groups
        write_records("downloads", downloads)

    formats = Counter(downloads[k].get("format") for k in downloaded)
    print(f"*** Downloaded: {len(downloaded)} of {len(todo)} {dict(formats) if formats else ''}")
    print(f"*** 404 / unknown type: {len(not_found)} {not_found[:20]} (retry with RETRY_FAILED=1)")
    print(f"*** Failed: {len(failed)} {failed[:20]}")
    have = sum(1 for k in groups if downloads.get(k, {}).get("status") in DONE)
    print(f"*** Files downloaded: {have} of {len(groups)} (scope={args.scope})")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scope", choices=("new", "all"), default="all")
    p.add_argument("--window", default="7d", help="what --scope new means")
    p.add_argument("--limit", type=int, default=0, help="max downloads this run (0 = no limit)")
    p.add_argument("--retry-failed", action="store_true", help="also retry 404 / unknown-type failures")
    p.add_argument("--delay", type=float, default=1.0, help="seconds between downloads")
    main(p.parse_args())
