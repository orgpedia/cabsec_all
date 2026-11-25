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
                                  "flags", "changes") if k in e} for e in events],
    "people": holders,
    "reissues": {},
  }


def _caption(e: dict[str, Any], name) -> str:
  """A plain caption for a prologue change; no subject counts, since sizes before 1961 are approximate."""
  f = [name(u, e["prev"]) for u in e["from"]]
  t = [name(u, e["prev"] if e["kind"] == "absorbed" else e["series"]) for u in e["to"]]
  both = lambda xs: ", ".join(xs[:-1]) + " and " + xs[-1] if len(xs) > 1 else xs[0]
  return {"born": lambda: f"{t[0]} is created", "ended": lambda: f"{f[0]} is abolished",
          "split": lambda: f"{f[0]} splits into {both(t)}", "merged": lambda: f"{both(f)} merge into {t[0]}",
          "spun_off": lambda: f"{t[0]} is separated from {f[0]}", "absorbed": lambda: f"{f[0]} joins {t[0]}",
          "renamed": lambda: f"{f[0]} is renamed {t[0]}"}[e["kind"]]()


def prologue(tl: dict[str, Any], pro: dict[str, Any]) -> dict[str, Any]:
  """Put the years before the Rules of 1961 in front of the run (requirements R12): frames from the cabinet lists,
  sizes worked back from 1961, and the changes written by hand in prologue.yml."""
  units, first = tl["units"], tl["frames"][0]
  for uid, u in pro["units"].items():
    names = [{"name": n[1], "short": n[2], "hindi": None, "kind": n[3] if len(n) > 3 else "ministry", "from": n[0]}
             for n in u["names"]]
    if uid in units: units[uid]["names"] = names + units[uid]["names"]
    else: units[uid] = {"names": names, "parents": [], "sector": u["sector"]}
  frames = [{"series": f["series"], "date": f["date"], "sizes": dict(pro["sizes"][f["series"]]), "flags": ["approx"],
             "order": f.get("order")} for f in pro["frames"]]
  frames[0]["flags"].append("start")
  first["flags"] = [x for x in first.get("flags", []) if x != "start"]
  if not first["flags"]: del first["flags"]
  allf = frames + [first]
  for uid, u in units.items():                      # born and ended from where each unit is on stage
    on = [f["series"] for f in allf if uid in f["sizes"]]
    if not on: continue
    u["born"] = min(on)
    if uid.startswith("P"): u["ended"] = next(f["series"] for f in allf if f["series"] > max(on))
  def name(uid, series):
    ns = units[uid]["names"]; n = ns[0]
    for x in ns:
      if x["from"] <= series: n = x
    return n["name"]
  order = [f["series"] for f in allf]; date = {f["series"]: f["date"] for f in allf}
  events = []
  for e in pro["events"]:
    e = {"from": [], "to": [], "moved": [], **e}
    e["prev"] = order[order.index(e["series"]) - 1]
    ev = {"series": e["series"], "date": date[e["series"]], "kind": e["kind"], "from": e["from"], "to": e["to"],
          "moved": e["moved"], "caption": _caption(e, name), "flags": ["approx"]}
    key_unit = e["to"][0] if e["kind"] in ("born", "spun_off", "merged") else e["from"][0]
    ev["key"] = f'{e["series"]} {e["kind"]} {units[key_unit]["names"][0]["short"]}'
    if e.get("salient"): ev["salient"] = True; ev["story"] = e["story"]
    events.append(ev)
  tl["frames"] = frames + tl["frames"]
  tl["events"] = events + tl["events"]
  tl["reissues"][str(first["series"])] = {"label": "The Rules begin", "text": " ".join(pro["note"].split())}
  return tl


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
  if cfg.get("prologue"):
    tl = prologue(tl, yaml.safe_load((root / cfg["prologue"]).read_text(encoding="utf-8")))
    # the office-holders from before the first frame of the Rules
    tl["people"] = [p for p in people.get("people", []) if (p["to"] or "9999") > tl["frames"][0]["date"]
                    and p["from"] <= tl["frames"][-1]["date"]]
  from cells import lineage, slugs   # each unit's ministry page (U52) and its line (U67)
  names_cfg = yaml.safe_load((root / cfg.get("names", "cells-names.yml")).read_text(encoding="utf-8")) or {}
  for uid, ln in lineage.lines(tl["units"], tl["events"], names_cfg.get("lines")).items():
    if len(ln) > 1:
      tl["units"][uid]["line"] = ln
  date_of = {f["series"]: f["date"] for f in tl["frames"]}
  for uid, slug in slugs.assign(tl["units"], lambda s: (date_of.get(s) or "0000")[:4]).items():
    tl["units"][uid]["slug"] = slug
  ui = (root / cfg.get("ui", "../ui")).resolve()
  ui.mkdir(parents=True, exist_ok=True)
  name = stem.replace("cells", "timeline")
  (ui / f"{name}.json").write_text(json.dumps(tl, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
  print(f"{name}.json: {len(tl['frames'])} frames, {len(tl['units'])} units, {len(tl['events'])} events "
        f"({sum(1 for e in tl['events'] if e.get('salient'))} salient), {len(tl['people'])} office-holders")


if __name__ == "__main__":
  main(sys.argv[1] if len(sys.argv) > 1 else "src/cells-2004.yml")
