"""A frame's top-level units and their subjects: the Second Schedule's top-level units (a ministry, or a department,
secretariat or office in no ministry), each with its numbered entries, named from the First Schedule's top-level
item with the same heading (its English and its Hindi name)."""

import re
from difflib import SequenceMatcher
from typing import Any, Optional

from cells.text import full, hindi_in, hkey, key, name, similar, unmarked

TOP = ("ministry", "department")


def schedule(tree: dict[str, Any], num: str) -> dict[str, Any]:
  return next((c for c in tree.get("children", []) if c.get("type") == "schedule" and str(c.get("num")) == num), {})


def _numbered(n: dict[str, Any]) -> bool:
  return (n.get("type") == "entry" and bool(re.fullmatch(r"\d+[A-Z]*", str(n.get("num") or "")))
          and key(n.get("text") or "") != "omitted")


def subjects(unit: dict[str, Any]) -> list[dict[str, Any]]:
  """A unit's numbered entries in order, through its departments, group headings and parts."""
  out: list[dict[str, Any]] = []

  def walk(n: dict[str, Any]) -> None:
    for c in n.get("children", []):
      if c.get("type") == "entry":
        if _numbered(c):
          out.append(c)
      elif c.get("type") in ("group_heading", "part", "department", "ministry"):
        walk(c)
  walk(unit)
  return out


def _omitted(n: dict[str, Any]) -> bool:
  return bool(n.get("omitted")) or key(n.get("heading") or n.get("text") or "").startswith("omitted")


def kind_of(typ: Optional[str], nm: str) -> str:
  """ministry, department, or office (a secretariat, office, commission or aayog in no ministry), for the count of
  units under the year (ui-requirements U28)."""
  if typ == "ministry" or re.sub(r"^[^\w]+", "", nm).lower().startswith("ministry"):
    return "ministry"
  if re.search(r"(?i)secretariat|office|commission|aayog", nm):
    return "office"
  return "department"


def first_items(tree: dict[str, Any]) -> list[dict[str, Any]]:
  """The First Schedule's top-level items still there: {num, heading, name, hindi}."""
  out = []
  for m in schedule(tree, "1").get("children", []):
    if m.get("type") in TOP and not _omitted(m) and (m.get("heading") or "").strip():
      h = m["heading"]
      out.append({"num": m.get("num"), "heading": h, "name": name(h), "type": m.get("type"), "eid": m.get("eId"),
                  "hindi": (m.get("heading_hi") or "").strip() or hindi_in(h)})
  return out


def _closeness(heading: str, it: dict[str, Any]) -> float:
  """How surely a Second Schedule heading is a First Schedule item, read past the OCR in either: 1 for the same
  heading; else the best of the letters' likeness, a cut-off heading ("MINISTRY OF CORPORATE" for "Ministry of
  Corporate Affairs", or one with words run on after it), its Hindi name, and the words in common."""
  a, b = hkey(heading), hkey(it["heading"])
  if not a or not b:
    return 0.0
  if a == b:
    return 1.0
  got = SequenceMatcher(None, a, b).ratio()
  short, long_ = sorted((a, b), key=len)
  if len(short) >= 12 and long_.startswith(short):
    got = max(got, 0.9)
  hi = key(it.get("hindi") or "")
  if hi and len(hi) >= 8:
    got = max(got, SequenceMatcher(None, key(name(heading)), hi).ratio())
  w = similar(name(heading), it["name"])
  return max(got, w if w >= 0.6 else 0.0)


PAIRED = 0.85  # the least closeness taken as the same unit


def _pairs(headings: list[str], items: list[dict[str, Any]]) -> dict[int, int]:
  """{Second Schedule unit: First Schedule item}. The same headings first, so that a near one cannot take an item
  that another unit carries exactly; then the rest, closest first."""
  got: dict[int, int] = {}
  taken: set[int] = set()
  for j, h in enumerate(headings):
    hk = hkey(h)
    for i, it in enumerate(items):
      if i not in taken and hk and hkey(it["heading"]) == hk:
        got[j] = i
        taken.add(i)
        break
  scored = sorted(((_closeness(h, it), j, i) for j, h in enumerate(headings) if j not in got
                   for i, it in enumerate(items) if i not in taken), reverse=True)
  for sc, j, i in scored:
    if sc < PAIRED:
      break
    if j not in got and i not in taken:
      got[j] = i
      taken.add(i)
  return got


def units(tree: dict[str, Any]) -> dict[str, Any]:
  """{units: [{name, heading, hindi, first (the First Schedule's heading or None), size, texts}], first_only: […]}."""
  items = first_items(tree)
  tops = [m for m in schedule(tree, "2").get("children", []) if m.get("type") in TOP and not _omitted(m)]
  heads = [m.get("heading") or m.get("text") or "" for m in tops]
  pair = _pairs(heads, items)
  out = []
  for j, (m, h) in enumerate(zip(tops, heads)):
    it = items[pair[j]] if j in pair else None
    subs = subjects(m)
    out.append({"name": it["name"] if it else name(h), "heading": h, "hkey": hkey(h),
                "hindi": (it["hindi"] if it else None) or hindi_in(h),
                "first": it["heading"] if it else None, "first_num": it["num"] if it else None,
                "eid": m.get("eId"), "first_eid": it.get("eid") if it else None,   # its places in the two schedules
                "kind": kind_of(it["type"] if it else m.get("type"), it["name"] if it else name(h)),
                "size": len(subs), "texts": [unmarked(full(e)) for e in subs]})
  taken = set(pair.values())
  return {"units": out, "first_only": [it["name"] for i, it in enumerate(items) if i not in taken]}
