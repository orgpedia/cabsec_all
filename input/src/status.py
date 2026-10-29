"""Print pipeline counts and compare the site with archive.org.

Usage: CABSEC_COLLECTION=<collection> status.py [--no-ia]
"""

import argparse
import re
from collections import Counter

from common import ARCHIVE, COLLECTION, IA_PREFIX, KIND, active, file_ext, identifier_for, is_listed, read_records

# item ids per kind; amendments and rules share an IA_PREFIX, so the search result is filtered by these
ID_RE = {"council": r"[a-z]{3}\.\d{4}-[A-Z][a-z]{2}-\d{2}\.\d+", "ammend": r"\d+", "rules": r"\d{4}-[A-Z][a-z]{2}-\d{2}\.\d+"}


def archive_org_identifiers():
    import internetarchive as ia

    found = {r["identifier"] for r in ia.search_items(f"identifier:{IA_PREFIX}*", fields=["identifier"])}
    return {i for i in found if re.fullmatch(ID_RE[KIND], i[len(IA_PREFIX):])}


def main(args):
    items, downloads = read_records("items"), read_records("downloads")
    wayback, archive = read_records("wayback"), read_records("archive")

    on_site = [i for i in items.values() if not i.get("removed_utc")]
    statuses = Counter(i.get("status") for i in on_site)
    act = [i for i in on_site if active(i)]
    keys = {i["file_key"] for i in act}
    done = {k for k in keys if downloads.get(k, {}).get("status") in ("downloaded", "seeded")}
    failed = {k for k in keys if (downloads.get(k, {}).get("status") or "").startswith("failed")}
    linked = {k for k in done if wayback.get(k, {}).get("link_success")}
    uploaded = [i for i in act if archive.get((i["item_id"], i["file_key"]), {}).get("upload_success")]
    collections = Counter(archive[(i["item_id"], i["file_key"])].get("collection") for i in uploaded)

    print(f"*** {COLLECTION}: items")
    print(f"\ton site: {len(on_site)}   removed from site: {len(items) - len(on_site)}   "
          f"not listed (kept): {sum(1 for i in items.values() if not is_listed(i))}")
    for s, n in sorted(statuses.items(), key=lambda x: str(x[0])):
        print(f"\t{s}: {n}")
    print(f"*** Files: {len(keys)}")
    print(f"\tdownloaded: {len(done)} / {len(keys)}   failed: {len(failed)}   pending: {len(keys) - len(done) - len(failed)}")
    print(f"\tby type: {dict(Counter(file_ext(downloads[k]) for k in done).most_common())}")
    reasons = Counter(downloads[k]["status"] for k in failed)
    if reasons:
        print(f"\tfailed by reason: {dict(reasons)}")
    print(f"*** Wayback: linked {len(linked)} / {len(done)}   pending {len(done) - len(linked)}")
    if ARCHIVE:
        print(f"*** archive.org: uploaded {len(uploaded)} / {len(act)}   pending {len(act) - len(uploaded)}   "
              f"by collection: {dict(collections)}")
    else:
        print("*** archive.org: not uploaded for this collection (download, HF and Wayback only)")

    held = sorted((str(i["source_key"]), i["status"]) for i in on_site if (i.get("status") or "").startswith("held"))
    if held:
        print(f"*** Held ({len(held)}): {held[:20]}")

    if ARCHIVE and not args.no_ia:
        expected = {identifier_for(i["item_id"]) for i in act}
        print("*** Site vs archive.org")
        print(f"\ton site {len(on_site)} - no_file {statuses.get('no_file', 0)} - held {len(held)} = expected items {len(expected)}")
        try:
            found = archive_org_identifiers()
            missing, extra = sorted(expected - found), sorted(found - expected)
            print(f"\titems on archive.org: {len(found)}   missing: {len(missing)}   not expected: {len(extra)}")
            if missing:
                print(f"\tmissing (first 20): {missing[:20]}")
            if extra:
                print(f"\tnot expected (first 20): {extra[:20]}")
            print("\t(archive.org search can lag new uploads by a few hours)")
        except Exception as e:
            print(f"\tcould not search archive.org: {e}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--no-ia", action="store_true", help="skip the archive.org search")
    main(p.parse_args())
