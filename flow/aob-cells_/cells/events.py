"""The events between two frames, and the ids that last (requirements.md §4–5).

A count is a good share when it is at least `least` subjects and at least `share` of the unit's subjects."""

import re
from typing import Any, Optional

from difflib import SequenceMatcher

from cells.text import hkey, plain, words

ORDER = ["ended", "born", "split", "spun_off", "merged", "absorbed", "moved", "renamed", "grew", "shrank"]


class Ids:
  def __init__(self) -> None:
    self.n = 0

  def new(self) -> str:
    self.n += 1
    return f"U{self.n:03d}"


def touched(changes: list[dict[str, Any]], firsts: list[list[dict[str, Any]]]) -> set[str]:
  """The headings (hkey) of the top-level units an amendment's changes reach, in either schedule: "schedule 2 ›
  ministry MINISTRY OF LAW. › department B", "schedule 1 › ministry 14" (by its number, in the frames' First
  Schedules)."""
  out: set[str] = set()
  for c in changes:
    for side in ("before", "after"):
      for x in c.get(side) or []:
        parts = [p.strip() for p in str(x.get("path") or "").split("›")]
        if len(parts) < 2:
          continue  # the schedule itself: an insert's place; its other side names the unit
        m = re.match(r"^(?:ministry|department)\s*(.*)$", parts[1])
        if not m:
          continue
        label = m.group(1).strip()
        if parts[0] == "schedule 1" and re.fullmatch(r"[0-9]+[A-Z]{0,3}|[ivxl]+", label or "x", re.I):
          for items in firsts:
            out |= {hkey(it["heading"]) for it in items if str(it["num"]).lower() == label.lower()}
        elif label:
          out.add(hkey(label))
          out |= {hkey(x.get("text") or "")} if parts[0] == "schedule 1" and len(parts) == 2 else set()
  out.discard("")
  return out


def step(a: list[dict[str, Any]], a_ids: list[str], b: list[dict[str, Any]], f: dict[str, Any], ids: Ids,
         least: int, share: float) -> tuple[list[str], list[dict[str, Any]]]:
  """The ids of the after units, and the events: [{kind, from: [before index], to: [after index], moved: [n]}]."""
  out_of: dict[int, dict[int, int]] = {}
  into: dict[int, dict[int, int]] = {}
  for (i, j), n in f["pairs"].items():
    out_of.setdefault(i, {})[j] = n
    into.setdefault(j, {})[i] = n

  def good(n: int, size: int) -> bool:
    return n >= least and n >= share * max(size, 1)

  def big_out(i: int) -> list[int]:
    return sorted((j for j, n in out_of.get(i, {}).items() if good(n, a[i]["size"])), key=lambda j: -out_of[i][j])

  def big_in(j: int) -> list[int]:
    return sorted((i for i, n in into.get(j, {}).items() if good(n, b[j]["size"])), key=lambda i: -into[j][i])

  src: dict[int, int] = {}  # after unit -> the before unit whose id it keeps
  by_heading = {}
  for i, u in enumerate(a):
    by_heading.setdefault(u["hkey"], []).append(i)
  for j, u in enumerate(b):  # the same heading
    for i in by_heading.get(u["hkey"], []):
      if i not in src.values():
        src[j] = i
        break
  for j, u in enumerate(b):  # renamed: its subjects mostly from one unit, which sent them mostly to it
    if j in src or not into.get(j):
      continue
    i = max(into[j], key=lambda k: into[j][k])
    if i in src.values() or len(big_out(i)) >= 2 or not good(into[j][i], b[j]["size"]):
      continue
    if max(out_of[i], key=lambda k: out_of[i][k]) == j and len(big_in(j)) <= 1:
      src[j] = i
  name_splits = []
  for j, u in enumerate(b):
    if j in src or big_in(j):
      continue
    for j2, i in list(src.items()):
      old, w1, w2 = words(a[i]["name"]), words(b[j2]["name"]), words(u["name"])
      if a[i]["hkey"] != b[j2]["hkey"] and old & w1 and old & w2 and old <= w1 | w2:
        del src[j2]
        name_splits.append((i, [j2, j]))
        break
  b_ids = [a_ids[src[j]] if j in src else ids.new() for j in range(len(b))]
  kept = set(src.values())
  events: list[dict[str, Any]] = []
  busy: set[tuple[str, int]] = set()

  def add(kind: str, frm: list[int], to: list[int], moved: list[int], **more: Any) -> None:
    events.append({"kind": kind, "from": frm, "to": to, "moved": moved, **more})
    busy.update(("a", i) for i in frm)
    busy.update(("b", j) for j in to)

  for i, parts in name_splits:  # "Steel, Mines and Fuel" into "Steel & Heavy Industries" and "Mines & Fuel"
    add("split", [i], parts, [b[j]["size"] for j in parts])
  for i, u in enumerate(a):  # the units that end
    if i in kept or ("a", i) in busy:
      continue
    d = big_out(i)
    if len(d) >= 2:
      add("split", [i], d, [out_of[i][j] for j in d])
    elif len(d) == 1 and d[0] in src:
      add("absorbed", [i], d, [out_of[i][d[0]]], was=a[src[d[0]]]["size"])
    elif not d:
      add("ended", [i], [], [u["size"]])
  for j, u in enumerate(b):  # the new units
    if j in src or ("b", j) in busy:
      continue
    s = big_in(j)
    ended = [i for i in s if i not in kept]
    if not s:
      add("born", [], [j], [u["size"]])
    elif len(ended) >= 2:
      add("merged", s, [j], [into[j][i] for i in s])
    elif not ended:
      for i in s:
        add("spun_off", [i], [j], [into[j][i]])
    elif not any(e["kind"] == "split" and ended[0] in e["from"] for e in events):
      b_ids[j] = a_ids[ended[0]]  # its one successor, the rest gone or moved: the same unit, another name
      src[j] = ended[0]
      busy.add(("a", ended[0]))
  for (i, j), n in sorted(f["pairs"].items()):  # moved between two units that stay
    if i in kept and j in src and src[j] != i and good(n, a[i]["size"]):
      add("moved", [i], [j], [n])
  for j, i in sorted(src.items()):
    if renamed(a[i]["name"], b[j]["name"]):
      events.append({"kind": "renamed", "from": [i], "to": [j], "moved": []})
    if ("a", i) in busy or ("b", j) in busy:
      continue
    was, now = a[i]["size"], b[j]["size"]
    if abs(now - was) >= least and abs(now - was) >= share * max(was, 1):
      events.append({"kind": "grew" if now > was else "shrank", "from": [i], "to": [j], "moved": [was, now]})
  events.sort(key=lambda e: ORDER.index(e["kind"]))
  return b_ids, events


def renamed(old: str, new: str) -> bool:
  """Another name, not the same one spelt or read apart ("Environment. and Forest", "Environment and Forests")."""
  a, b = plain(old), plain(new)
  return a != b and SequenceMatcher(None, a, b).ratio() < 0.9


def caption(e: dict[str, Any], a: list[dict[str, Any]], b: list[dict[str, Any]]) -> str:
  fa = [a[i]["name"] for i in e["from"]]
  tb = [b[j]["name"] for j in e["to"]]
  k = e["kind"]
  if k == "born":
    return f"{tb[0]} is created ({b[e['to'][0]]['size']} subjects)"
  if k == "ended":
    return f"{fa[0]} is abolished"
  if k == "split":
    parts = " and ".join(f"{n} ({m})" for n, m in zip(tb, e["moved"]))
    return f"{fa[0]} splits into {parts}"
  if k == "spun_off":
    return f"{tb[0]} is separated from {fa[0]} ({e['moved'][0]} subjects)"
  if k == "merged":
    return f"{' and '.join(fa)} merge into {tb[0]}"
  if k == "absorbed":
    return f"{fa[0]} joins {tb[0]} ({e['was']} → {b[e['to'][0]]['size']})"
  if k == "moved":
    return f"{e['moved'][0]} subjects move from {fa[0]} to {tb[0]}"
  if k == "renamed":
    return f"{fa[0]} is renamed {tb[0]}"
  if k == "grew":
    return f"{tb[0]} grows from {e['moved'][0]} to {e['moved'][1]} subjects"
  return f"{tb[0]} shrinks from {e['moved'][0]} to {e['moved'][1]} subjects"


def involved(e: dict[str, Any], a: list[dict[str, Any]], b: list[dict[str, Any]]) -> set[str]:
  return {a[i]["hkey"] for i in e["from"]} | {b[j]["hkey"] for j in e["to"]}


def is_touched(e: dict[str, Any], a: list[dict[str, Any]], b: list[dict[str, Any]], heads: set[str],
               whole: bool) -> bool:
  if whole or "*" in heads:
    return True
  return bool(involved(e, a, b) & heads)

