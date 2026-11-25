"""A ministry's line (ui-requirements U67): the units it carries on, back to where it began. From the unit, step
back to the unit that fed it most when it was made: the unit split (or, of a merger, the units merged), and any unit
absorbed into it the same day. Of these, the one whose names share most words with the ministry the line is
traced for comes first, then the one that brought the most subjects. A unit created from nothing, or spun off from
another, begins a line of its own. The corrections file's `lines` overrides a step: `U109: U014` (Railways from
1986 carries on Railways 1957–1985), or `U123: stop`."""

import re
from typing import Any

PLAIN = {"ministry", "department", "of", "and", "the", "for", "affairs", "development", "&"}


def _words(u: dict[str, Any]) -> set[str]:
  return {w for n in u["names"] for w in re.findall(r"[a-z]+", n["name"].lower()) if w not in PLAIN}


def lines(units: dict[str, Any], events: list[dict[str, Any]], overrides: dict[str, str] | None = None) -> dict[str, list[str]]:
  """{uid: [the line's units, oldest first, ending with uid]}."""
  made: dict[str, dict[str, Any]] = {}
  for e in events:
    for x in e["to"]:
      if e["kind"] in ("born", "split", "merged", "spun_off") and x not in e["from"] and x not in made:
        made[x] = e
  over = {str(k): str(v) for k, v in (overrides or {}).items()}

  def feeders(uid: str) -> list[tuple[str, int]]:
    """The units that fed uid when it was made, with the subjects each brought."""
    e = made.get(uid)
    if not e or e["kind"] in ("born", "spun_off") or not e["from"]:
      return []
    mv = e.get("moved") or []
    if e["kind"] == "merged":
      got = [(f, mv[i] if i < len(mv) else 0) for i, f in enumerate(e["from"])]
    else:   # split: the unit split, with what it gave this part
      i = e["to"].index(uid)
      got = [(e["from"][0], mv[i] if i < len(mv) else 0)]
    for a in events:   # and what was absorbed into it, or moved to it, the same day
      if a["series"] == e["series"] and a["kind"] in ("absorbed", "moved") and a["to"] == [uid] and a["from"]:
        got.append((a["from"][0], (a.get("moved") or [0])[0]))
    return [(u, n) for u, n in got if u in units and u != uid]

  out = {}
  for uid in units:
    want = _words(units[uid])
    chain, cur = [uid], uid
    while True:
      if cur in over:
        p = None if over[cur] == "stop" else over[cur] if over[cur] in units else None
      else:
        fs = feeders(cur)
        p = max(fs, key=lambda f: (len(_words(units[f[0]]) & want), f[1]))[0] if fs else None
      if not p or p in chain:
        break
      chain.append(p); cur = p
    out[uid] = chain[::-1]
  return out
