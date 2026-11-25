"""cells.json and cells-review.json from the frames (requirements.md)."""

import re
from concurrent.futures import ProcessPoolExecutor
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Any

from cells import count, events as ev, match, read
from cells.text import hkey


def _short_default(full: str) -> str:
  return re.sub(r"^(Ministry|Department) of ", "", full)


def _key(series: int, kind: str, unit_name: str, short: dict[str, str]) -> str:
  """An event's key in the corrections file: "<series> <kind> <unit's short name>", the unit being the new one for
  born, spun off and merged, else the first one it comes from."""
  return f"{series} {kind} {short.get(unit_name) or _short_default(unit_name)}"


def _commit(path: Path) -> str:
  try:
    return subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()
  except Exception:
    return ""


def _nm(u: dict[str, Any], s: int, short: dict[str, str]) -> dict[str, Any]:
  return {"name": u["name"], "short": short.get(u["name"]) or _short_default(u["name"]), "hindi": u["hindi"],
          "kind": u["kind"], "from": s}


def _moved_subjects(e: dict[str, Any], f: dict[str, Any], prev_ids: list[str], cur_ids: list[str],
                    most: int = 120) -> dict[str, list[str]]:
  """The subjects an event moved, by their text after it, under the unit that took them: those followed from one
  of its units before to one of its units after under another id; for a unit created from nothing, its subjects
  not followed from anywhere."""
  fr, to = set(e["from"]), set(e["to"])
  if e["kind"] in ("renamed", "grew", "shrank", "ended"):
    return {}
  out: dict[str, list[str]] = {}
  for i, j, t in f.get("links", []):
    if i in fr and j in to and prev_ids[i] != cur_ids[j]:
      out.setdefault(cur_ids[j], []).append(t)
  if e["kind"] == "born" or not fr:
    for j, t in f.get("new_list", []):
      if j in to:
        out.setdefault(cur_ids[j], []).append(t)
  return {u: ts[:most] for u, ts in out.items()}


def _changes_at(changes: list[dict[str, Any]], places: list[Any]) -> list[int]:
  """The numbers (seq) of an amendment's changes whose place, before or after, is in one of the units' places in
  the schedules (eIds, and everything under them)."""
  ps = {p for ps in places if ps for p in ps if p}
  out = set()
  for c in changes:
    for side in ("before", "after"):
      for x in c.get(side) or []:
        e = x.get("eId") or ""
        if any(e == p or e.startswith(p + "__") for p in ps):
          out.add(c["seq"])
  return sorted(out)


def _days(a: str, b: str) -> int:
  return (datetime.strptime(b, "%Y-%m-%d") - datetime.strptime(a, "%Y-%m-%d")).days


def _fmt(d: str) -> str:
  x = datetime.strptime(d, "%Y-%m-%d")
  return f"{x.day} {x.strftime('%B')} {x.year}"


def build(cfg: dict[str, Any], root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
  states = (root / cfg["states"]).resolve()
  base = (root / cfg["base"]).resolve()
  least, share = int(cfg.get("least", 3)), float(cfg.get("share", 0.2))
  reissues, s1 = set(cfg.get("reissues", [])), set(cfg.get("schedule1_reissues", []))
  restarts = set(cfg.get("restarts", []))
  names_cfg = cfg.get("_names") or {}
  calls = names_cfg.get("events") or {}
  short = names_cfg.get("short") or {}
  spelling = names_cfg.get("spelling") or {}   # a name as the data prints it -> as it is shown (R18); not a data fix
  sector_of = {n: sec for sec, ns in (names_cfg.get("sectors") or {}).items() for n in (ns or [])}
  changes = read.changes(states)
  ids = ev.Ids()
  units_out: dict[str, dict[str, Any]] = {}
  frames_out: list[dict[str, Any]] = []
  events_out: list[dict[str, Any]] = []
  review: dict[str, Any] = {"dropped_untouched": [], "unnamed": [], "first_only": [], "empty": [], "steps": [],
                            "flagged": [], "no_sector": [], "silent": [], "reissue_quiet": [],
                            "moves_across": []}
  window = int(cfg.get("move_window_days", 90))   # a transfer made across two notifications this far apart (R7b)
  buffer: list[dict[str, Any]] = []                # subjects taken out and not yet seen put in elsewhere
  prev, prev_ids, prev_first, prev_eids = None, [], [], {}
  start = int(cfg.get("start", 0))
  all_frames = list(read.frames(states, base, cfg.get("base_date", "1961-01-14"), start))
  with ProcessPoolExecutor() as ex:   # each frame's units, read in parallel: the slow part of the build
    all_units = list(ex.map(count.units, [fr["tree"] for fr in all_frames], chunksize=8))
  for fr, got in zip(all_frames, all_units):
    for u in got["units"]:
      if u["name"] in spelling:
        u["name"] = spelling[u["name"]]
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
    cur_eids: dict[str, list[str]] = {}
    flags = (["reissue"] if s in reissues else []) + (["schedule1_reissue"] if s in s1 else []) + \
            (["restart"] if s in restarts else []) + (["start"] if prev is None else [])
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
      cur_eids = {cur_ids[j]: [x for x in (u.get("eid"), u.get("first_eid")) if x] for j, u in enumerate(us)}
      heads = ev.touched(changes.get(s, []), [prev_first, first])
      # R7b: subjects taken out of a unit in one notification and put into another in a later one, within the window
      across = []
      if "reissue" in flags:
        buffer = []   # a re-issue rewrites the text: nothing before it can be followed across it
      else:
        cands = [b for b in buffer if not b["used"] and _days(b["date"], fr["date"]) <= window and b["uid"] in cur_ids]
        if cands and f["new_list"]:
          bef = [{"text": b["text"], "unit": k} for k, b in enumerate(cands)]
          aft = [{"text": t, "unit": j} for j, t in f["new_list"]]
          hit = match.match(bef, aft, {})
          tally: dict[tuple[str, str], list[int]] = {}
          for x, k in hit.items():
            pair = (cands[k]["uid"], cur_ids[aft[x]["unit"]])
            if pair[0] != pair[1]:
              tally.setdefault(pair, []).append(k)
          for (ua, ub), ks in tally.items():
            b0 = cands[ks[0]]
            if len(ks) >= least and len(ks) >= share * max(b0["size"], 1):
              for k in ks:
                cands[k]["used"] = True
              across.append({"from": ua, "to": ub, "n": len(ks), "series": b0["series"], "date": b0["date"]})
    whole = bool(flags) or s == 0
    a = prev or []
    if "reissue" in flags:   # R11: at a re-issue the size changes and moves come from the rewritten text
      kept = []
      for e in evs:
        if e["kind"] in ("grew", "shrank", "moved"):
          review["reissue_quiet"].append({"series": s, "kind": e["kind"], "caption": ev.caption(e, a, us)})
        else:
          kept.append(e)
      evs = kept
    if prev is not None:
      for m in across:   # one "moved" for each transfer across notifications; the size changes it explains go
        ja, jb = cur_ids.index(m["from"]), cur_ids.index(m["to"])
        e = {"kind": "moved", "from": [prev_ids.index(m["from"])] if m["from"] in prev_ids else [], "to": [jb],
             "moved": [m["n"]], "across": m}
        evs = [x for x in evs if not (x["kind"] == "grew" and x["to"] == [jb] and x["moved"][1] - x["moved"][0] <= m["n"] * 1.5 + 1)]
        for old in list(events_out):
          if old["series"] == m["series"] and old["kind"] == "shrank" and old["to"] == [m["from"]] \
              and old["moved"][0] - old["moved"][1] <= m["n"] * 1.5 + 1:
            events_out.remove(old)
            review["moves_across"].append({"series": m["series"], "dropped": old["caption"]})
        review["moves_across"].append({"series": s, "from_series": m["series"], "n": m["n"], "from": m["from"], "to": m["to"]})
        evs.append(e)
    for e in evs:
      if e.get("across"):
        m = e["across"]; na = us[cur_ids.index(m["from"])]["name"]; nb = us[cur_ids.index(m["to"])]["name"]
        out = {"series": s, "date": fr["date"], "kind": "moved", "from": [m["from"]], "to": [m["to"]], "moved": [m["n"]],
               "caption": f"{m['n']} subject{'s' if m['n'] != 1 else ''} move from {na} to {nb}, taken out on "
                          f"{_fmt(m['date'])} and put in on {_fmt(fr['date'])}",
               "across": {"series": m["series"], "date": m["date"]}}
        who = na
      else:
        out = {"series": s, "date": fr["date"], "kind": e["kind"],
               "from": [prev_ids[i] for i in e["from"]], "to": [cur_ids[j] for j in e["to"]], "moved": e["moved"],
               "caption": ev.caption(e, a, us)}
        who = us[e["to"][0]]["name"] if e["kind"] in ("born", "spun_off", "merged") or not e["from"] else a[e["from"][0]]["name"]
      out["key"] = _key(s, e["kind"], who, short)
      if not e.get("across") and not ev.is_touched(e, a, us, heads, whole):
        review["dropped_untouched"].append(out)
        continue
      call = calls.get(out["key"]) or calls.get(f"{s}:{e['kind']}:{(out['from'] or out['to'])[0]}")
      if isinstance(call, dict):  # {salient: true, caption: …, kind: …, drop: true}
        if call.get("drop"):
          continue
        if call.get("salient"):
          out["salient"] = True
        if call.get("caption"):
          out["story"] = call["caption"]
        call = call.get("kind")
      if call == "drop":
        continue
      if call and call != "keep":
        out["kind"], out["called"] = call, True
      if flags:
        out["flags"] = flags
        review["flagged"].append(out)
      if prev is not None and "reissue" not in flags and not e.get("across"):
        subs = _moved_subjects(e, f, prev_ids, cur_ids)
        if subs:
          out["subjects"] = subs   # the subjects it moved, by their text (ui-requirements U56)
      seqs = _changes_at(changes.get(s, []), [prev_eids.get(u) for u in out["from"] + out["to"]]
                         + [cur_eids.get(u) for u in out["from"] + out["to"]])
      if seqs:
        out["changes"] = seqs   # the amendment's changes that reach the event's units (ui-requirements U41)
      events_out.append(out)
    if prev is not None:
      kept_ids = [x for x in evs if x["kind"] != "renamed"]
      in_ev_from = {prev_ids[i] for x in evs for i in x["from"]}
      in_ev_to = {cur_ids[j] for x in evs for j in x["to"]}
      for uid in set(prev_ids) - set(cur_ids) - in_ev_from:
        review["silent"].append({"series": s, "unit": uid, "ends": True})
      for uid in set(cur_ids) - set(prev_ids) - in_ev_to:
        review["silent"].append({"series": s, "unit": uid, "starts": True})
    if prev is not None and "reissue" not in flags:
      buffer = [b for b in buffer if not b["used"] and _days(b["date"], fr["date"]) <= window]
      for i, t in f["gone_list"]:
        if prev_ids[i] in cur_ids:
          buffer.append({"text": t, "uid": prev_ids[i], "size": prev[i]["size"], "series": s, "date": fr["date"],
                         "used": False})
    renamed_to = {cur_ids[j] for e in evs if e["kind"] == "renamed" and ev.is_touched(e, a, us, heads, whole)
                  for j in e["to"]}
    for j, u in enumerate(us):
      uid = cur_ids[j]
      rec = units_out.get(uid)
      if rec is None:
        rec = units_out[uid] = {"names": [_nm(u, s, short)], "born": s}
        parents = sorted({prev_ids[i] for e in evs if j in e["to"] for i in e["from"]
                          if e["kind"] in ("split", "spun_off", "merged")})
        if parents:
          rec["parents"] = parents
      else:
        last = rec["names"][-1]
        if uid in renamed_to:
          rec["names"].append({**_nm(u, s, short), "hindi": u["hindi"] or last["hindi"]})
        elif hkey(last["name"]) != hkey(u["name"]) and not ev.renamed(last["name"], u["name"]) and whole:
          last["name"] = u["name"]  # the same name, spelt as the re-issue prints it
          last["short"] = short.get(u["name"]) or _short_default(u["name"])
        elif u["hindi"] and not last["hindi"] and hkey(last["name"]) == hkey(u["name"]):
          last["hindi"] = u["hindi"]  # the Hindi name first printed later (1961 had none)
        elif u["hindi"] and last["hindi"] and u["hindi"] != last["hindi"] and uid in renamed_to:
          last["hindi"] = u["hindi"]
      rec.pop("ended", None)
    for uid in set(prev_ids) - set(cur_ids):
      units_out[uid]["ended"] = s
    frames_out.append({"series": s, "date": fr["date"], "notification": ", ".join(fr["docs"]), "file": fr["file"],
                       **({"flags": flags} if flags else {}),
                       "sizes": {cur_ids[j]: u["size"] for j, u in enumerate(us)},
                       "eids": {cur_ids[j]: [u.get("eid"), u.get("first_eid")] for j, u in enumerate(us)}})
    prev, prev_ids, prev_first = us, cur_ids, first
    prev_eids = {cur_ids[j]: [x for x in (u.get("eid"), u.get("first_eid")) if x] for j, u in enumerate(us)}
  used = {e["key"] for e in events_out} | {e["key"] for e in review["dropped_untouched"]}
  first = frames_out[0]["series"] if frames_out else 0   # a call before the run's first frame is not this run's
  review["unused_calls"] = sorted(k for k in calls if " " in str(k) and k not in used
                                  and not (str(k).split()[0].isdigit() and int(str(k).split()[0]) <= first))
  for uid in sorted(units_out):  # a unit's sector: by any of its names, else its first parent's (ui-requirements U19)
    rec = units_out[uid]
    sec = next((sector_of[n["name"]] for n in rec["names"] if n["name"] in sector_of), None)
    if sec is None and rec.get("parents"):
      sec = units_out.get(rec["parents"][0], {}).get("sector")
    rec["sector"] = sec
    if sec is None:
      review["no_sector"].append({"unit": uid, "name": rec["names"][-1]["name"]})
  for uid, over in (names_cfg.get("units") or {}).items():
    if uid in units_out:
      units_out[uid]["display"] = over
  cells = {"source": {"states": str(cfg["states"]), "states_commit": _commit(states),
                      "made": date.today().isoformat(), "start": start, "least": least, "share": share,
                      "counted": "numbered subjects of each top-level Second Schedule unit, omitted ones left out"},
           "units": units_out, "frames": frames_out, "events": events_out}
  return cells, review
