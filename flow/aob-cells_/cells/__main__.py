import json
import sys
from pathlib import Path

import yaml

from cells.build import build
from cells.page import review_page


def main(path: str) -> None:
  cfg_path = Path(path).resolve()
  root = cfg_path.parent
  cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
  names = root / cfg.get("names", "cells-names.yml")
  cfg["_names"] = yaml.safe_load(names.read_text(encoding="utf-8")) if names.exists() else {}
  cells, review = build(cfg, root)
  out = (root / cfg.get("out", "../output")).resolve()
  out.mkdir(parents=True, exist_ok=True)
  stem = cfg.get("stem", "cells")  # cells.json, or cells-2004.json for the frames from 2004
  (out / f"{stem}.json").write_text(json.dumps(cells, ensure_ascii=False, indent=1), encoding="utf-8")
  (out / f"{stem}-review.json").write_text(json.dumps(review, ensure_ascii=False, indent=1), encoding="utf-8")
  (out / f"{stem}-review.html").write_text(review_page(cells, review), encoding="utf-8")
  kinds: dict[str, int] = {}
  for e in cells["events"]:
    kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
  print(f"{len(cells['frames'])} frames, {len(cells['units'])} units, {len(cells['events'])} events {kinds}; "
        f"{len(review['dropped_untouched'])} left out (the amendment does not touch them)")


if __name__ == "__main__":
  main(sys.argv[1] if len(sys.argv) > 1 else "src/cells.yml")
