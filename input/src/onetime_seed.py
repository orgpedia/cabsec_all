"""One-time: seed council files from the old cabsec repo instead of downloading them again.

Usage: CABSEC_COLLECTION=council onetime_seed.py [--seed-dir LFS/_seed/cabsec] [--old-repo ~/orgpedia/cabsec] [--no-probe]

Sources (old layout pdfs/<changePort|councilMin|swearNewMin|initCompo>/<year>/1_Upload_N.pdf):
  --seed-dir   a `hf download Orgpedia/cabsec` copy (made by `make onetime_seed`); files are hardlinked from it
  --old-repo   ~/orgpedia/cabsec: LFS/cabsec/pdfs/ (2024-26 files, copied) and import/documents/documents.yml
               (old download times). The old repo is only read.

A file is seeded when an active item has its file_key, the bytes are a PDF, and the size equals the site's
(from a 1-byte Range GET; --no-probe skips that check). Otherwise it is left for `make download` and reported.
Seeded files get status "seeded" in downloads.json, so download.py skips them. Run `make discover_full` first.
"""

import argparse
import datetime
import re
import shutil
import time
from pathlib import Path

from common import (
    COLLECTION,
    ROOT,
    active,
    file_format,
    file_path,
    hardlink,
    link_file,
    probe,
    read_records,
    rel_path,
    save_records,
    sha1_file,
    write_records,
)

OLD_FOLDERS = {
    "changePort": "changeinportfolio",
    "councilMin": "councilofministers",
    "swearNewMin": "swearingofnewministers",
    "initCompo": "initial_compositions_of_council_of_ministers",
}
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))  # wget logs of the 2021 crawl are in IST
PROBE_DELAY = 0.5


def old_files(pdfs_dir, label):
    """{file_key: (path, seed_source)} for pdfs/<old folder>/<year>/<name>.pdf"""
    out = {}
    if not pdfs_dir.is_dir():
        print(f"*** {label}: {pdfs_dir} not found, skipped")
        return out
    for p in sorted(pdfs_dir.glob("*/*/*.pdf")):
        folder = OLD_FOLDERS.get(p.parent.parent.name)
        if not folder:
            continue
        key = f"{folder}/{p.stem}"
        if key in out:
            print(f"\tWARNING {label}: {key} twice ({out[key][0]} and {p}), keeping the first")
            continue
        out[key] = (p, f"{label}:{p.relative_to(pdfs_dir.parent)}")
    print(f"*** {label}: {len(out)} PDFs in {pdfs_dir}")
    return out


def old_download_times(yml_path):
    """{file_key: download time UTC} from documents.yml (url + download_time per entry)."""
    if not yml_path.exists():
        return {}
    times, url = {}, None
    for line in yml_path.read_text().splitlines():
        m = re.match(r"\s+url:\s*(\S+)", line)
        if m:
            url = m.group(1)
            continue
        m = re.match(r"\s+download_time:\s*(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)", line)
        if m and url:
            path = url.split("writereaddata/", 1)[-1]
            key = f"{path.split('/', 1)[0]}/{Path(path).stem}"
            t = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
            times[key] = t.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z%z")
            url = None
    return times


def main(args):
    if COLLECTION != "council":
        raise SystemExit("onetime_seed is only for CABSEC_COLLECTION=council")
    items, downloads = read_records("items"), read_records("downloads")
    if not items:
        raise SystemExit("no items yet: run `make discover_full C=council` first")

    old_repo = Path(args.old_repo).expanduser()
    sources = old_files(Path(args.seed_dir) / "pdfs", "hf:Orgpedia/cabsec")
    for key, v in old_files(old_repo / "LFS" / "cabsec" / "pdfs", "local:cabsec/LFS").items():
        sources.setdefault(key, v)
    times = old_download_times(old_repo / "import" / "documents" / "documents.yml")

    todo = [i for i in items.values() if active(i)
            and downloads.get(i["file_key"], {}).get("status") not in ("downloaded", "seeded")]
    print(f"*** Active items: {sum(1 for i in items.values() if active(i))}; not yet downloaded or seeded: {len(todo)}")

    seeded, mismatched, not_pdf, missing = [], [], [], []
    try:
        for n, item in enumerate(todo, 1):
            key, url = item["file_key"], item["file_url"]
            if key not in sources:
                missing.append(key)
                continue
            src, seed_source = sources[key]
            if file_format(src) != "pdf":
                not_pdf.append(key)
                continue
            size = src.stat().st_size
            site_status = last_modified = None
            if not args.no_probe:
                site_status, site_size, last_modified = probe(url)
                time.sleep(PROBE_DELAY)
                if site_status in (200, 206) and site_size != size:
                    print(f"{key} [{n}/{len(todo)}] SIZE MISMATCH: seed {size}, site {site_size}; leaving it for download")
                    mismatched.append(key)
                    continue

            dest = file_path(key)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if seed_source.startswith("hf:"):
                hardlink(src.resolve(), dest)  # our own hf download copy
            else:
                shutil.copy2(src, dest)        # the user's old repo: copy, never move
            downloads[key] = {
                "file_key": key,
                "source_keys": [item["source_key"]],
                "url": url,
                "paths": [rel_path(key)],
                "size": size,
                "sha1": sha1_file(dest),
                "last_modified": last_modified,
                "etag": None,
                "download_time_utc": times.get(key),
                "status": "seeded",
                "seed_source": seed_source,
                "site_status": site_status,
                "format": "pdf",
                "attempts": 0,
                "current": True,
            }
            link_file(key)
            seeded.append(key)
            print(f"{key} [{n}/{len(todo)}] seeded from {seed_source}"
                  + (f" (site answered {site_status})" if site_status not in (None, 200, 206) else ""))
            save_records("downloads", downloads)
    finally:
        write_records("downloads", downloads)

    print(f"*** Seeded: {len(seeded)}")
    print(f"*** Size differs from the site, left for download: {len(mismatched)} {mismatched[:20]}")
    print(f"*** Not a PDF, left for download: {len(not_pdf)} {not_pdf[:20]}")
    print(f"*** No seed copy, left for download: {len(missing)} {missing[:30]}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--seed-dir", default=str(ROOT / "LFS" / "_seed" / "cabsec"))
    p.add_argument("--old-repo", default="~/orgpedia/cabsec")
    p.add_argument("--no-probe", action="store_true", help="don't compare sizes with the site")
    main(p.parse_args())
