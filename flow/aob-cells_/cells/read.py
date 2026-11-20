"""The frames: the Rules after each amendment, from the states' output, and the 1961 base. The only module that
knows the states' file layout."""

import json
from pathlib import Path
from typing import Any, Iterator


def chain(states: Path) -> dict[int, dict[str, Any]]:
  return {c["series"]: c for c in json.loads((states / "chain.json").read_text(encoding="utf-8"))}


def changes(states: Path) -> dict[int, list[dict[str, Any]]]:
  out: dict[int, list[dict[str, Any]]] = {}
  for c in json.loads((states / "changes.json").read_text(encoding="utf-8")):
    out.setdefault(c["series"], []).append(c)
  return out


def evolution(states: Path) -> dict[str, Any]:
  p = states / "evolution.json"
  return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"epochs": []}


def known(states: Path) -> Any:
  p = states / "known-issues.json"
  return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def base(path: Path) -> dict[str, Any]:
  return json.loads(path.read_text(encoding="utf-8"))["documents"][0]["tree"]


def frames(states: Path, base_path: Path, base_date: str) -> Iterator[dict[str, Any]]:
  """Frame 0, the 1961 Rules, then one frame per amendment in series order: {series, date, file, docs, tree}."""
  links = chain(states)
  yield {"series": 0, "date": base_date, "file": base_path.name.replace(".json", ""), "docs": [], "tree": base(base_path)}
  for p in sorted((states / "states").glob("*.json"), key=lambda p: int(p.stem)):
    s = json.loads(p.read_text(encoding="utf-8"))
    c = links.get(s["series"], {})
    yield {"series": s["series"], "date": s.get("date") or c.get("date"), "file": c.get("file") or s.get("amendment"),
           "docs": c.get("docs", []), "start": s.get("start"), "tree": s["tree"]}
