"""Shared paths, constants and helpers for the import scripts.

The collection (council, aob or tob) comes from the CABSEC_COLLECTION environment variable, which the
Makefile sets for every run. Everything collection-specific below is derived from it.

Files keep the site's names: <HF_PREFIX>/<file_key>.pdf, e.g. council/pdfs/changeinportfolio/1_Upload_1595.pdf.
"""

import datetime
import hashlib
import json
import os
import re
import shutil
import signal
import time
import zipfile
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------- CONFIG

NAME = "cabsec_all"                         # LFS/<NAME>/ and the HF dataset name
DEFAULT_HF_REPO_ID = f"Orgpedia/{NAME}"
SITE = "https://cabsec.gov.in"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0"
FORMATS = ("pdf",)                          # accepted file types, detected from bytes

COLLECTIONS = {
    "council": {
        "ia_prefix": "in.gov.cabsec.council.",
        "hf_prefix": "council/pdfs",
        "source_page": f"{SITE}/councilofministers/changeinportfolios/",
    },
    "aob": {
        "ia_prefix": "in.gov.cabsec.aob.",
        "hf_prefix": "aob/pdfs",
        "source_page": f"{SITE}/allocationofbusinessrules/amendment/",
    },
    "tob": {
        "ia_prefix": "in.gov.cabsec.tob.",
        "hf_prefix": "tob/pdfs",
        "source_page": f"{SITE}/transactionofbusiness/tobamendment/",
    },
}

COLLECTION = os.environ.get("CABSEC_COLLECTION", "").strip()
if COLLECTION not in COLLECTIONS:
    raise SystemExit(f"Set CABSEC_COLLECTION to one of {', '.join(COLLECTIONS)} (got {COLLECTION!r})")
_C = COLLECTIONS[COLLECTION]

HF_PREFIX = _C["hf_prefix"]                 # folder inside LFS/<NAME>/ and the HF repo
IA_PREFIX = _C["ia_prefix"]                 # archive.org identifier = IA_PREFIX + item_id
SOURCE_PAGE = _C["source_page"]             # default human-facing page (items carry their own list_url)

LFS_DIR = ROOT / "LFS" / NAME
FILES_DIR = LFS_DIR / HF_PREFIX
DOCS_DIR = ROOT / "input" / "documents" / COLLECTION   # JSON state, tracked in git
LINKS_DIR = DOCS_DIR / "pdfs"               # symlinks to the files
CHANGES_DIR = DOCS_DIR / "changes"
RAW_DIR = LFS_DIR / "raw" / COLLECTION      # raw listing responses per run (not pushed to HF)

# Record key field(s) per state file in DOCS_DIR
KEYS = {
    "items": ("source_key",),     # one per entry on the site; item_id (frozen) is a field, None while held
    "downloads": ("file_key",),   # one per downloaded file
    "wayback": ("file_key",),
    "archive": ("item_id", "file_key"),  # a replaced file (new file_key) is uploaded again to the same item
}


def sub_path(file_key, ext="pdf"):
    """Path of a file below FILES_DIR and LINKS_DIR: the site's own folder and name."""
    return f"{file_key}.{ext}"


# ---------------------------------------------------------------- environment

def load_env():
    load_dotenv(ROOT / ".env")  # existing env vars win


def require_env(*names):
    values = [os.environ.get(n, "").strip() for n in names]
    missing = [n for n, v in zip(names, values) if not v]
    if missing:
        raise SystemExit(f"Missing environment variables: {', '.join(missing)} (set them in .env)")
    return values


def hf_settings():
    repo_id = os.environ.get("HF_REPO_ID", "").strip() or DEFAULT_HF_REPO_ID
    token = os.environ.get("HF_TOKEN", "").strip() or None
    return repo_id, token


# ---------------------------------------------------------------- time

def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z%z")


def parse_utc(s):
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return datetime.datetime.fromisoformat(s)


def parse_window(s):
    """'7d' / '12h' / '30' (days) -> timedelta"""
    m = re.fullmatch(r"\s*(\d+)\s*([dh]?)\s*", s or "")
    if not m:
        raise SystemExit(f"Bad time window: {s!r} (use e.g. 7d or 12h)")
    n, unit = int(m.group(1)), m.group(2) or "d"
    return datetime.timedelta(days=n) if unit == "d" else datetime.timedelta(hours=n)


def within(s, window):
    t = parse_utc(s)
    return bool(t) and datetime.datetime.now(datetime.timezone.utc) - t <= window


MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def make_date(y, m, d):
    """ISO date string, or None if the parts don't form a real date."""
    try:
        return datetime.date(int(y), int(m), int(d)).isoformat()
    except (TypeError, ValueError):
        return None


def parse_dmy(text):
    """First dd/mm/yyyy or dd.mm.yyyy in text (lenient about spaces and a stray comma), as ISO, else None."""
    m = re.search(r"(\d{1,2})\s*,?\s*[/.]\s*(\d{1,2})\s*,?\s*[/.]\s*(\d{4})", text or "")
    return make_date(m.group(3), m.group(2), m.group(1)) if m else None


def parse_month_name(text):
    """'15 October, 2026' or 'April, 14 1961' as ISO, else None."""
    text = text or ""
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,})\.?\s*,?\s*(\d{4})", text)
    if m and m.group(2)[:3].lower() in MONTHS:
        return make_date(m.group(3), MONTHS.index(m.group(2)[:3].lower()) + 1, m.group(1))
    m = re.search(r"([A-Za-z]{3,})\.?\s*,?\s*(\d{1,2})\s*,?\s+(\d{4})", text)
    if m and m.group(1)[:3].lower() in MONTHS:
        return make_date(m.group(3), MONTHS.index(m.group(1)[:3].lower()) + 1, m.group(2))
    return None


# ---------------------------------------------------------------- state files

def record_key(name, r):
    fields = KEYS[name]
    return r[fields[0]] if len(fields) == 1 else tuple(r[f] for f in fields)


def read_records(name):
    """Read DOCS_DIR/<name>.json as a dict keyed by the file's key field(s)."""
    path = DOCS_DIR / f"{name}.json"
    if not path.exists():
        return {}
    return {record_key(name, r): r for r in json.loads(path.read_text())}


def read_json(name, default=None):
    """A curated JSON file in DOCS_DIR (overrides.json, delisted.json)."""
    path = DOCS_DIR / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else default


_last_write = {}


def sort_key(k):
    """Numbers sort numerically, strings lexically; tuples element-wise."""
    parts = k if isinstance(k, tuple) else (k,)
    return tuple((0, p, "") if isinstance(p, int) else (1, 0, str(p)) for p in parts)


def write_records(name, records):
    """Sorted list, indent=2, atomic (tmp + rename)."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    path = DOCS_DIR / f"{name}.json"
    ordered = [records[k] for k in sorted(records, key=sort_key)]
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(ordered, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)
    _last_write[name] = time.monotonic()


def save_records(name, records, every=10):
    """write_records at most every `every` seconds; always call write_records in a finally block too."""
    if time.monotonic() - _last_write.get(name, 0) >= every:
        write_records(name, records)


def _sigterm(signum, frame):
    raise KeyboardInterrupt(f"signal {signum}")


signal.signal(signal.SIGTERM, _sigterm)  # kill/cancel -> KeyboardInterrupt -> finally blocks save state


class ChangeLog:
    """Buffer events and append them to changes/<YYYY-MM-DD>.json on flush()."""

    def __init__(self):
        self.pending = []

    def add(self, event, item_id, **extra):
        self.pending.append({"time_utc": utc_now(), "item_id": item_id, "event": event, **extra})

    def flush(self):
        if not self.pending:
            return
        CHANGES_DIR.mkdir(parents=True, exist_ok=True)
        path = CHANGES_DIR / f"{datetime.datetime.now(datetime.timezone.utc):%Y-%m-%d}.json"
        events = json.loads(path.read_text()) if path.exists() else []
        events.extend(self.pending)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(events, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(path)
        self.pending = []


# ---------------------------------------------------------------- http
# cabsec.gov.in answers every HEAD with 200 text/html, even for missing files: never use HEAD.

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})


def get(url, params=None, data=None, retries=4):
    """GET (or POST when data is given) and return the body text."""
    error = None
    for attempt in range(1, retries + 1):
        try:
            if data is None:
                r = SESSION.get(url, params=params, timeout=90)
            else:
                r = SESSION.post(url, params=params, data=data, timeout=90)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            error = e
            print(f"\tattempt {attempt}/{retries} failed: {e}")
            time.sleep(5 * attempt)
    raise RuntimeError(f"{'POST' if data else 'GET'} {url} failed: {error}")


def probe(url):
    """(http_status, total_size, last_modified) from a 1-byte Range GET."""
    with SESSION.get(url, headers={"Range": "bytes=0-0"}, stream=True, timeout=60) as r:
        return r.status_code, total_size(r), r.headers.get("Last-Modified")


# ---------------------------------------------------------------- items

def active(item):
    """An item that should have a file, an archive.org item and a Wayback link.

    Items no longer listed on the site (removed_utc, or listed=False) stay active: their files still download.
    """
    return item.get("status") == "ok" and bool(item.get("item_id")) and bool(item.get("file_url"))


def is_listed(item):
    return item.get("listed", True) and not item.get("removed_utc")


def is_new(item, window):
    """SCOPE=new: an active item first seen within the window."""
    return bool(active(item)) and within(item.get("first_seen_utc"), window)


def upload_order(item):
    """Oldest first: council by date, aob / tob by series number."""
    if COLLECTION == "council":
        return (item.get("date") or "9999", sort_key(item.get("item_id") or ""))
    return (0, sort_key(item["source_key"]))


def group_by_file(items):
    """{file_key: [active items in source_key order]}"""
    groups = {}
    for key in sorted(items, key=sort_key):
        item = items[key]
        if active(item):
            groups.setdefault(item["file_key"], []).append(item)
    return dict(sorted(groups.items(), key=lambda kv: sort_key(kv[0])))


def same_file_map(items, downloads):
    """{item_id: [other item_ids whose file has the same sha1]}"""
    by_sha = {}
    for i in items.values():
        sha = downloads.get(i.get("file_key"), {}).get("sha1")
        if active(i) and sha:
            by_sha.setdefault(sha, []).append(i["item_id"])
    out = {}
    for ids in by_sha.values():
        for i in ids:
            out[i] = sorted(x for x in ids if x != i)
    return out


def identifier_for(item_id):
    return IA_PREFIX + item_id


def file_ext(download):
    return (download or {}).get("format") or "pdf"


def rel_path(file_key, ext="pdf"):
    """Path inside LFS/<NAME>/ and the HF repo."""
    return f"{HF_PREFIX}/{sub_path(file_key, ext)}"


def file_path(file_key, ext="pdf"):
    return LFS_DIR / rel_path(file_key, ext)


# ---------------------------------------------------------------- files

def sha1_file(path):
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_format(path):
    """pdf / jpg / png / doc / docx from the file's first bytes (not its name), or None (e.g. an HTML error page)."""
    with path.open("rb") as f:
        head = f.read(1024)
    if b"%PDF" in head:
        return "pdf"
    if head.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if head.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "doc"
    if head.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(path) as z:
                if any(n.startswith("word/") for n in z.namelist()):
                    return "docx"
        except zipfile.BadZipFile:
            pass
    return None


def hardlink(src, dst):
    """Make dst the same file as src (hardlink, or copy across devices)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if os.path.samefile(src, dst):
            return
        dst.unlink()
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def link_file(file_key, ext="pdf"):
    """Create/repair LINKS_DIR/<sub_path> -> relative path to LFS/<NAME>/<HF_PREFIX>/<sub_path>."""
    link = LINKS_DIR / sub_path(file_key, ext)
    link.parent.mkdir(parents=True, exist_ok=True)
    for old in link.parent.glob(f"{Path(sub_path(file_key, ext)).stem}.*"):  # file changed type
        if old != link and old.is_symlink():
            old.unlink()
    target = os.path.relpath(file_path(file_key, ext), link.parent)
    if link.is_symlink() and os.readlink(link) == target:
        return
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(target)


def total_size(r):
    if r.status_code == 206:
        m = re.search(r"/(\d+)$", r.headers.get("Content-Range", ""))
        return int(m.group(1)) if m else None
    length = r.headers.get("Content-Length")
    return int(length) if length else None


def fetch_file(url, dest, retries=5):
    """Download url via dest.part, resuming with Range on retries. Returns (info, error).

    Saved as dest with the extension of its detected type (info["format"], info["path"]).
    error is "404", "unknown_type" (not in FORMATS) or the last exception text.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    error = ""
    for attempt in range(1, retries + 1):
        offset = part.stat().st_size if part.exists() else 0
        headers = {"Range": f"bytes={offset}-"} if offset else {}
        try:
            with SESSION.get(url, headers=headers, stream=True, timeout=120) as r:
                if r.status_code == 404:
                    return None, "404"
                if r.status_code == 416:  # stale .part, start over
                    part.unlink()
                    continue
                r.raise_for_status()
                if r.status_code == 200:
                    offset = 0  # server ignored Range
                total = total_size(r)
                info = {"last_modified": r.headers.get("Last-Modified"), "etag": r.headers.get("ETag")}
                with part.open("ab" if offset else "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)

            size = part.stat().st_size
            if total and size != total:
                raise OSError(f"size mismatch {size} vs {total}")
            fmt = file_format(part)
            if fmt not in FORMATS:
                part.unlink()
                return None, "unknown_type"
            final = dest.with_suffix(f".{fmt}")
            part.replace(final)
            info.update(size=size, format=fmt, path=final)
            return info, ""
        except (requests.RequestException, OSError) as e:
            error = str(e)
            print(f"\tattempt {attempt}/{retries} failed: {error}")
            time.sleep(5 * attempt)
    return None, error


def ensure_file(download):
    """Local path of a downloaded file, fetching it if LFS lacks it: HF -> source (sha1 must match)."""
    key = download["file_key"]
    dest = file_path(key, file_ext(download))
    if dest.exists():
        return dest

    from huggingface_hub import hf_hub_download

    repo_id, token = hf_settings()
    try:
        hf_hub_download(repo_id=repo_id, repo_type="dataset", filename=rel_path(key, file_ext(download)),
                        local_dir=LFS_DIR, token=token)
        if dest.exists() and sha1_file(dest) == download.get("sha1"):
            return dest
    except Exception:
        pass

    info, error = fetch_file(download["url"], dest)
    if info and info["path"] == dest and sha1_file(dest) == download.get("sha1"):
        return dest
    if info and info["path"].exists():
        info["path"].unlink()
    raise RuntimeError(f"cannot get the file for {key} (not on HF; source: {error or 'sha1 differs'})")
