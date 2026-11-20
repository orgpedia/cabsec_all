"""The subjects followed from one frame to the next: the same text first, then the entries sharing most of their
rare words. Copied from docflow's bridge.match_entries, so that this folder stands alone."""

import math
import re
from typing import Any

from cells.text import SMALL, key


def _subject(s: str) -> set[str]:
  return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 2 and w not in SMALL}


def match(before: list[dict[str, Any]], after: list[dict[str, Any]], peer: dict[int, int],
          least: float = 0.45, held: float = 0.9) -> dict[int, int]:
  """{after index: before index}. Each entry is {text, unit}; `peer` maps an after unit to the before unit with its
  heading, preferred when the same text is in more than one."""
  same: dict[str, list[int]] = {}
  for i, e in enumerate(before):
    same.setdefault(key(e["text"]), []).append(i)
  got: dict[int, int] = {}
  used: set[int] = set()
  for j, e in enumerate(after):
    hits = [i for i in same.get(key(e["text"]), []) if i not in used]
    if hits:
      home = [i for i in hits if peer.get(e["unit"]) == before[i]["unit"]]
      got[j] = (home or hits)[0]
      used.add(got[j])
  wb = [_subject(e["text"]) for e in before]
  wa = [_subject(e["text"]) for e in after]
  df: dict[str, int] = {}
  for ws in wb + wa:
    for w in ws:
      df[w] = df.get(w, 0) + 1
  n = len(wb) + len(wa)
  weight = {w: math.log(n / (1 + c)) for w, c in df.items()}

  def mass(ws: set[str]) -> float:
    return sum(weight[w] for w in ws)
  holding: dict[str, set[int]] = {}
  for i, ws in enumerate(wb):
    if i not in used:
      for w in ws:
        holding.setdefault(w, set()).add(i)
  scored = []
  for j in range(len(after)):
    if j in got:
      continue
    for i in {i for w in wa[j] for i in holding.get(w, ())}:
      both, either = mass(wa[j] & wb[i]), mass(wa[j] | wb[i])
      one = min(mass(wa[j]), mass(wb[i]))
      sim = both / either if either > 0 else 0.0
      if sim >= least or (one > 0 and both / one >= held and sim >= least * 2 / 3):
        scored.append((sim, peer.get(after[j]["unit"]) == before[i]["unit"], i, j))
  for _, _, i, j in sorted(scored, reverse=True):
    if j not in got and i not in used:
      got[j] = i
      used.add(i)
  return got


def flows(a: list[dict[str, Any]], b: list[dict[str, Any]], peer: dict[int, int]) -> dict[str, Any]:
  """Between two frames' units: {pairs: {(i, j): n}, gone: [per before unit], new: [per after unit]}."""
  eb = [{"text": t, "unit": i} for i, u in enumerate(a) for t in u["texts"]]
  ea = [{"text": t, "unit": j} for j, u in enumerate(b) for t in u["texts"]]
  got = match(eb, ea, peer)
  pairs: dict[tuple[int, int], int] = {}
  for j, i in got.items():
    k = (eb[i]["unit"], ea[j]["unit"])
    pairs[k] = pairs.get(k, 0) + 1
  followed = set(got.values())
  gone = [0] * len(a)
  for i, e in enumerate(eb):
    if i not in followed:
      gone[e["unit"]] += 1
  new = [0] * len(b)
  for j, e in enumerate(ea):
    if j not in got:
      new[e["unit"]] += 1
  return {"pairs": pairs, "gone": gone, "new": new, "followed": len(got), "before": len(eb), "after": len(ea)}
