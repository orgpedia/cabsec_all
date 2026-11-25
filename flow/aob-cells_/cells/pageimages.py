"""The amendments' page images for the site (ui-requirements U44, U49): each page of each amendment's PDF as a WebP
about 1,200 pixels wide, in <site>/pages/<file>/<page>.webp, and <site>/data/pages.json with each page's size in
the extracted data's word-box units (300 per inch of the PDF's points), so the page can draw the boxes in percent.
The re-issues (cfg `reissues`) are not amendments and get no images (U46). Pages already made are kept. Reads the
PDFs from ../aob-ammend_/input (links into LFS); the build does not fetch them. Needs pdftoppm and Pillow."""

import io
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import yaml
from PIL import Image

WIDTH, QUALITY, DPI = 1200, 45, 300


def page_sizes(pdf: Path) -> list[tuple[float, float]]:
  out = subprocess.run(["pdfinfo", "-f", "1", "-l", "9999", str(pdf)], capture_output=True, text=True).stdout
  return [(float(w), float(h)) for w, h in re.findall(r"Page\s+\d+ size:\s+([\d.]+) x ([\d.]+)", out)]


def one(job: tuple[str, int, str]) -> tuple[str, int, int, int]:
  pdf, page, dest = job
  d = Path(dest)
  if d.exists():
    try:
      with Image.open(d) as im:
        im.load(); return pdf, page, im.width, im.height
    except Exception:
      pass                                   # an unfinished file from an earlier run: make it again
  with tempfile.TemporaryDirectory() as tmp:
    base = Path(tmp) / "p"
    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-scale-to-x", str(WIDTH), "-scale-to-y", "-1",
                    "-gray", "-png", pdf, str(base)], check=True, capture_output=True)
    im = Image.open(next(Path(tmp).glob("p*.png")))
    buf = io.BytesIO(); im.save(buf, "WEBP", quality=QUALITY, method=5)
  d.parent.mkdir(parents=True, exist_ok=True)
  d.write_bytes(buf.getvalue())             # written whole, in one go
  return pdf, page, im.width, im.height


def main(cfg_path: str, site: str) -> None:
  cfg_path = Path(cfg_path).resolve(); root = cfg_path.parent
  cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
  flow = root.parent.parent
  chain = json.loads((flow / "aob-states_/output/chain.json").read_text(encoding="utf-8"))
  skip = set(cfg.get("reissues") or [])
  site = Path(site).resolve()
  pdfdir = flow / "aob-ammend_/input"
  jobs, sizes = [], {}
  for c in chain:
    if c["series"] in skip: continue
    pdf = pdfdir / c["file"]
    if not pdf.exists(): print("missing", pdf.name); continue
    ps = page_sizes(pdf); sizes[c["file"]] = ps
    for i in range(len(ps)):
      jobs.append((str(pdf), i + 1, str(site / "pages" / c["file"].removesuffix(".pdf") / f"{i + 1}.webp")))
  print(f"{len(jobs)} pages in {len(sizes)} files")
  todo = [j for j in jobs if not Path(j[2]).exists()]
  limit = int(os.environ.get("PAGES_LIMIT", "0"))   # at most this many new pages in one run (0: all)
  if limit and len(todo) > limit:
    with ProcessPoolExecutor() as ex:
      list(ex.map(one, todo[:limit], chunksize=2))
    print(f"made {limit}; {len(todo) - limit} pages still to make: run again")
    return
  done = {}
  with ProcessPoolExecutor() as ex:
    for k, (pdf, page, w, h) in enumerate(ex.map(one, jobs, chunksize=4)):
      done.setdefault(Path(pdf).name, {})[page] = (w, h)
      if k % 200 == 0: print(k, flush=True)
  manifest = {f: [{"w": round(w * DPI / 72), "h": round(h * DPI / 72), "iw": done[f][i + 1][0], "ih": done[f][i + 1][1]}
                  for i, (w, h) in enumerate(ps)] for f, ps in sizes.items()}
  (site / "data").mkdir(parents=True, exist_ok=True)
  (site / "data/pages.json").write_text(json.dumps(manifest, separators=(",", ":")), encoding="utf-8")
  total = sum(p.stat().st_size for p in (site / "pages").rglob("*.webp"))
  print(f"pages.json: {sum(len(v) for v in manifest.values())} pages; images {total / 1e6:.0f} MB")


if __name__ == "__main__":
  main(sys.argv[1] if len(sys.argv) > 1 else "src/cells.yml", sys.argv[2] if len(sys.argv) > 2 else "../../../site.cabsec-aob")
