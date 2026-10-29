"""One-time: rename the amendment collections aob -> aob-ammend and tob -> tob-ammend.

Usage: onetime_rename.py [--no-hf]

For each rename:
  - git mv input/documents/<old> input/documents/<new>
  - move LFS/cabsec_all/<old> and LFS/cabsec_all/raw/<old>
  - rewrite the paths in downloads.json and relink the symlinks in input/documents/<new>/pdfs/
  - on the HF dataset, move <old>/pdfs/ to <new>/pdfs/ in one commit (server-side copies, nothing re-uploaded)
Every step is skipped when it is already done, so the script can be re-run. archive.org is not touched: the
identifiers (in.gov.cabsec.aob.<sno>, in.gov.cabsec.tob.<sno>) stay as they are.
"""

import argparse
import json
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
NAME = "cabsec_all"
DEFAULT_HF_REPO_ID = f"Orgpedia/{NAME}"
RENAMES = {"aob": "aob-ammend", "tob": "tob-ammend"}


def move(src, dst, git=False):
    if not src.exists():
        print(f"\t{src.relative_to(ROOT)}: not there, skipped")
        return
    if dst.exists():
        raise SystemExit(f"both {src.relative_to(ROOT)} and {dst.relative_to(ROOT)} exist; sort that out first")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if git:
        subprocess.run(["git", "mv", str(src), str(dst)], cwd=ROOT, check=True)
    else:
        src.rename(dst)
    print(f"\tmoved {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")


def fix_downloads(docs, old, new):
    path = docs / "downloads.json"
    if not path.exists():
        return
    records = json.loads(path.read_text())
    n = 0
    for d in records:
        paths = [f"{new}/{p[len(old) + 1:]}" if p.startswith(f"{old}/") else p for p in d.get("paths", [])]
        n += paths != d.get("paths", [])
        d["paths"] = paths
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)
    print(f"\tdownloads.json: {n} paths rewritten")


def relink(docs, new):
    links_dir, files_dir = docs / "pdfs", ROOT / "LFS" / NAME / new / "pdfs"
    n = 0
    for link in sorted(links_dir.rglob("*")) if links_dir.exists() else []:
        if not link.is_symlink():
            continue
        target = os.path.relpath(files_dir / link.relative_to(links_dir), link.parent)
        if os.readlink(link) != target:
            link.unlink()
            link.symlink_to(target)
            n += 1
    dangling = sum(1 for p in links_dir.rglob("*") if p.is_symlink() and not p.exists()) if links_dir.exists() else 0
    print(f"\tsymlinks: {n} relinked, {dangling} dangling")


def move_on_hf(old, new):
    from huggingface_hub import CommitOperationCopy, CommitOperationDelete, HfApi

    repo_id = os.environ.get("HF_REPO_ID", "").strip() or DEFAULT_HF_REPO_ID
    api = HfApi(token=os.environ.get("HF_TOKEN", "").strip() or None)
    paths = [f.path for f in api.list_repo_tree(repo_id, repo_type="dataset", recursive=True)
             if f.path.startswith(f"{old}/pdfs/") and hasattr(f, "size")]
    if not paths:
        print(f"\tHF {repo_id}: nothing under {old}/pdfs/, skipped")
        return
    ops = [CommitOperationCopy(src_path_in_repo=p, path_in_repo=f"{new}/{p[len(old) + 1:]}") for p in paths]
    ops.append(CommitOperationDelete(path_in_repo=f"{old}/pdfs/", is_folder=True))
    info = api.create_commit(repo_id, repo_type="dataset", operations=ops,
                             commit_message=f"rename {old}/pdfs -> {new}/pdfs")
    print(f"\tHF {repo_id}: moved {len(paths)} files {old}/pdfs/ -> {new}/pdfs/  {info.commit_url}")


def main(args):
    load_dotenv(ROOT / ".env")
    for old, new in RENAMES.items():
        print(f"*** {old} -> {new}")
        docs = ROOT / "input" / "documents" / new
        move(ROOT / "input" / "documents" / old, docs, git=True)
        move(ROOT / "LFS" / NAME / old, ROOT / "LFS" / NAME / new)
        move(ROOT / "LFS" / NAME / "raw" / old, ROOT / "LFS" / NAME / "raw" / new)
        fix_downloads(docs, old, new)
        relink(docs, new)
        if not args.no_hf:
            move_on_hf(old, new)
    if args.no_hf:
        print("*** HF not touched (--no-hf); run again without it to move the files on HF")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--no-hf", action="store_true", help="only the local moves")
    main(p.parse_args())
