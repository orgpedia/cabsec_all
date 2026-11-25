"""The ministry pages' addresses (ui-requirements U52): each unit by its name today, or its last name if it was
abolished, "Ministry of " left off ("Ministry of Education" → education); a name two units share gets the first
one's years after it. Its earlier names point to it unless another unit's page has that address."""

import re
from typing import Any, Callable


def slug_of(name: str) -> str:
  s = name.lower().replace("&", " and ")
  s = re.sub(r"^ministry of\s+", "", s.strip())
  return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "unit"


def assign(units: dict[str, Any], year: Callable[[Any], str]) -> dict[str, str]:
  """{uid: slug}; `year(series)` gives a series' year, for the units that share a name."""
  by: dict[str, list[str]] = {}
  for uid, u in units.items():
    by.setdefault(slug_of(u["names"][-1]["name"]), []).append(uid)
  out: dict[str, str] = {}
  for s, uids in by.items():
    if len(uids) == 1:
      out[uids[0]] = s
      continue
    alive = [u for u in uids if units[u].get("ended") is None]
    for uid in uids:   # the one alive today keeps the plain name; the others get their years
      u = units[uid]
      out[uid] = s if alive and uid == alive[0] else f"{s}-{year(u['born'])}-{year(u['ended']) if u.get('ended') is not None else 'now'}"
  return out


def former(units: dict[str, Any], main: dict[str, str]) -> dict[str, list[str]]:
  """{slug: [uids]} for the earlier names' addresses that are not a page of their own."""
  taken = set(main.values())
  out: dict[str, list[str]] = {}
  for uid, u in units.items():
    for n in u["names"][:-1]:
      s = slug_of(n["name"])
      if s not in taken and uid not in out.get(s, []):
        out.setdefault(s, []).append(uid)
  return out
