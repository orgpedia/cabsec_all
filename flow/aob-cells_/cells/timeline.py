"""timeline-<stem>.json: what the chart and the video read (ui-requirements U30). One file: the units with their
names, kinds, sectors and parents; every frame's date and sizes; the events (the run's first frame left out), with
their keys, salient flags and captions; and the office-holders from people.json. The timing of the Full run and the
Story is left to the page, which lays the same script out two ways (U7)."""

import json
import sys
from pathlib import Path
from typing import Any

import yaml


def timeline(cells: dict[str, Any], people: dict[str, Any]) -> dict[str, Any]:
  start = cells["source"].get("start", 0)
  first = cells["frames"][0]["series"]
  events = [e for e in cells["events"] if e["series"] != first and "start" not in (e.get("flags") or [])]
  first_date, last_date = cells["frames"][0]["date"], cells["frames"][-1]["date"]
  holders = [p for p in people.get("people", []) if (p["to"] or "9999") > first_date and p["from"] <= last_date]
  return {
    "source": {**cells["source"], "people": people.get("sources", {})},
    "start": start,
    "units": cells["units"],
    "frames": [{"series": f["series"], "date": f["date"], "sizes": f["sizes"], **({"flags": f["flags"]} if f.get("flags") else {})}
               for f in cells["frames"]],
    "events": [{k: e[k] for k in ("series", "date", "kind", "from", "to", "moved", "caption", "key", "salient", "story",
                                  "flags") if k in e} for e in events],
    "people": holders,
    "reissues": {},
  }


def main(path: str) -> None:
  cfg_path = Path(path).resolve()
  root = cfg_path.parent
  cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
  stem = cfg.get("stem", "cells")
  out = (root / cfg.get("out", "../output")).resolve()
  cells = json.loads((out / f"{stem}.json").read_text(encoding="utf-8"))
  people = json.loads((root / cfg.get("people", "people.json")).read_text(encoding="utf-8"))
  tl = timeline(cells, people)
  first = tl["frames"][0]["series"]
  tl["reissues"] = {str(k): v for k, v in (cfg.get("reissue_notes") or {}).items() if int(k) > first}
  ui = (root / cfg.get("ui", "../ui")).resolve()
  ui.mkdir(parents=True, exist_ok=True)
  name = stem.replace("cells", "timeline")
  (ui / f"{name}.json").write_text(json.dumps(tl, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
  print(f"{name}.json: {len(tl['frames'])} frames, {len(tl['units'])} units, {len(tl['events'])} events "
        f"({sum(1 for e in tl['events'] if e.get('salient'))} salient), {len(tl['people'])} office-holders")


if __name__ == "__main__":
  main(sys.argv[1] if len(sys.argv) > 1 else "src/cells-2004.yml")
