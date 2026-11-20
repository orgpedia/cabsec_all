"""cells.json and cells-review.json from the frames (requirements.md)."""

import subprocess
from datetime import date
from pathlib import Path
from typing import Any

from cells import count, events as ev, match, read
from cells.text import hkey


def _commit(path: Path) -> str:
  try:
    return subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()
  except Exception:
    return ""


def build(cfg: dict[str, Any], root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
  states = (root / cfg["states"]).resolve()
  base = (root / cfg["base"]).resolve()
  least, share = int(cfg.get("least", 3)), float(cfg.get("share", 0.2))
  reissues, s1 = set(cfg.get("reissues", [])), set(cfg.get("schedule1_reissues", []))
  restarts = set(cfg.get("restarts", []))
  names_cfg = cfg.get("_names") or {}
  calls = names_cfg.get("events") or {}
  changes = read.changes(states)
  ids = ev.Ids()
  units_out: dict[str, dict[str, Any]] = {}
  frames_out: list[dict[str, Any]] = []
  events_out: list[dict[str, Any]] = []
  review: dict[str, Any] = {"dropped_untouched": [], "unnamed": [], "first_only": [], "empty": [], "steps": [],
                            "flagged": []}
  prev, prev_ids, prev_first = None, [], []
  for fr in read.frames(states, base, cfg.get("base_date", "1961-01-14")):
    got = count.units(fr["tree"])
    us = []
    for u in got["units"]:
      if not u["name"].strip():
        review["unnamed"].append({"series": fr["series"], "heading": u["heading"], "size": u["size"]})
        if not u["size"]:
          continue
        u["name"] = u["heading"].strip() or "(no name)"
      us.append(u)
    first = count.first_items(fr["tree"])
    if got["first_only"]:
      review["first_only"].append({"series": fr["series"], "units": got["first_only"]})
    for u in us:
      if not u["size"]:
        review["empty"].append({"series": fr["series"], "unit": u["name"]})
    s = fr["series"]
    flags = (["reissue"] if s in reissues else []) + (["schedule1_reissue"] if s in s1 else []) + \
            (["restart"] if s in restarts else [])
    if prev is None:
      cur_ids = [ids.new() for _ in us]
      evs: list[dict[str, Any]] = [{"kind": "born", "from": [], "to": [j], "moved": [u["size"]]} for j, u in enumerate(us)]
      heads: set[str] = {"*"}
    else:
      peer = {}
      for j, u in enumerate(us):
        for i, p in enumerate(prev):
          if p["hkey"] == u["hkey"]:
            peer[j] = i
            break
      f = match.flows(prev, us, peer)
      review["steps"].append({"series": s, "followed": f["followed"], "before": f["before"], "after": f["after"],
                              "flags": flags})
      cur_ids, evs = ev.step(prev, prev_ids, us, f, ids, least, share)
      heads = ev.touched(changes.get(s, []), [prev_first, first])
    whole = bool(flags) or s == 0
    a = prev or []
    for e in evs:
      out = {"series": s, "date": fr["date"], "kind": e["kind"],
             "from": [prev_ids[i] for i in e["from"]], "to": [cur_ids[j] for j in e["to"]], "moved": e["moved"],
             "caption": ev.caption(e, a, us)}
      if not ev.is_touched(e, a, us, heads, whole):
        review["dropped_untouched"].append(out)
        continue
      call = calls.get(f"{s}:{e['kind']}:{(out['from'] or out['to'])[0]}")
      if call == "drop":
        continue
      if call and call != "keep":
        out["kind"], out["called"] = call, True
      if flags:
        out["flags"] = flags
        review["flagged"].append(out)
      events_out.append(out)
    renamed_to = {cur_ids[j] for e in evs if e["kind"] == "renamed" and ev.is_touched(e, a, us, heads, whole)
                  for j in e["to"]}
    for j, u in enumerate(us):
      uid = cur_ids[j]
      rec = units_out.get(uid)
      if rec is None:
        rec = units_out[uid] = {"names": [{"name": u["name"], "hindi": u["hindi"], "from": s}], "born": s}
        parents = sorted({prev_ids[i] for e in evs if j in e["to"] for i in e["from"]
                          if e["kind"] in ("split", "spun_off", "merged")})
        if parents:
          rec["parents"] = parents
      else:
        last = rec["names"][-1]
        if uid in renamed_to:
          rec["names"].append({"name": u["name"], "hindi": u["hindi"] or last["hindi"], "from": s})
        elif hkey(last["name"]) != hkey(u["name"]) and not ev.renamed(last["name"], u["name"]) and whole:
          last["name"] = u["name"]  # the same name, spelt as the re-issue prints it
        elif u["hindi"] and not last["hindi"] and hkey(last["name"]) == hkey(u["name"]):
          last["hindi"] = u["hindi"]  # the Hindi name first printed later (1961 had none)
        elif u["hindi"] and last["hindi"] and u["hindi"] != last["hindi"] and uid in renamed_to:
          last["hindi"] = u["hindi"]
      rec.pop("ended", None)
    for uid in set(prev_ids) - set(cur_ids):
      units_out[uid]["ended"] = s
    frames_out.append({"series": s, "date": fr["date"], "notification": ", ".join(fr["docs"]), "file": fr["file"],
                       **({"flags": flags} if flags else {}),
                       "sizes": {cur_ids[j]: u["size"] for j, u in enumerate(us)}})
    prev, prev_ids, prev_first = us, cur_ids, first
  for uid, over in (names_cfg.get("units") or {}).items():
    if uid in units_out:
      units_out[uid]["display"] = over
  cells = {"source": {"states": str(cfg["states"]), "states_commit": _commit(states),
                      "made": date.today().isoformat(), "least": least, "share": share,
                      "counted": "numbered subjects of each top-level Second Schedule unit, omitted ones left out"},
           "units": units_out, "frames": frames_out, "events": events_out}
  return cells, review
