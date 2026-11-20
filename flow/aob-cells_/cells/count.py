"""A frame's top-level units and their subjects: the Second Schedule's top-level units (a ministry, or a department,
secretariat or office in no ministry), each with its numbered entries, named from the First Schedule's top-level
item with the same heading (its English and its Hindi name)."""

import re
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


def first_items(tree: dict[str, Any]) -> list[dict[str, Any]]:
  """The First Schedule's top-level items still there: {num, heading, name, hindi}."""
  out = []
  for m in schedule(tree, "1").get("children", []):
    if m.get("type") in TOP and not _omitted(m) and (m.get("heading") or "").strip():
      h = m["heading"]
      out.append({"num": m.get("num"), "heading": h, "name": name(h),
                  "hindi": (m.get("heading_hi") or "").strip() or hindi_in(h)})
  return out


def _pair(heading: str, items: list[dict[str, Any]], taken: set[int]) -> Optional[int]:
  hk = hkey(heading)
  for i, it in enumerate(items):
    if i not in taken and hkey(it["heading"]) == hk:
      return i
  best = max(((similar(name(heading), it["name"]), i) for i, it in enumerate(items) if i not in taken), default=(0, None))
  return best[1] if best[0] >= 0.6 else None


def units(tree: dict[str, Any]) -> dict[str, Any]:
  """{units: [{name, heading, hindi, first (the First Schedule's heading or None), size, texts}], first_only: […]}."""
  items = first_items(tree)
  taken: set[int] = set()
  out = []
  for m in schedule(tree, "2").get("children", []):
    if m.get("type") not in TOP:
      continue
    h = m.get("heading") or m.get("text") or ""
    if _omitted(m):
      continue
    i = _pair(h, items, taken)
    it = items[i] if i is not None else None
    if i is not None:
      taken.add(i)
    subs = subjects(m)
    out.append({"name": it["name"] if it else name(h), "heading": h, "hkey": hkey(h),
                "hindi": (it["hindi"] if it else None) or hindi_in(h),
                "first": it["heading"] if it else None, "first_num": it["num"] if it else None,
                "size": len(subs), "texts": [unmarked(full(e)) for e in subs]})
  return {"units": out, "first_only": [it["name"] for i, it in enumerate(items) if i not in taken]}
