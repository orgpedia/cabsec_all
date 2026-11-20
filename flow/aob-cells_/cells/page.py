"""cells-review.html: what to check before the chart is shared (requirements.md)."""

import html
from typing import Any

CSS = """body{font:14px/1.45 -apple-system,system-ui,sans-serif;margin:24px;max-width:1100px;color:#222}
h1{font-size:22px}h2{font-size:17px;margin-top:28px}table{border-collapse:collapse;width:100%}
td,th{border-bottom:1px solid #ddd;padding:4px 8px;text-align:left;vertical-align:top}th{background:#f4f4f4}
.k{font-family:ui-monospace,monospace;font-size:12px}.f{color:#a15c00}.n{color:#777}"""


def _t(rows: list[list[Any]], head: list[str]) -> str:
  h = "".join(f"<th>{html.escape(x)}</th>" for x in head)
  b = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>" for r in rows)
  return f"<table><tr>{h}</tr>{b}</table>" if rows else "<p class=n>None.</p>"


def review_page(cells: dict[str, Any], review: dict[str, Any]) -> str:
  evs = [e for e in cells["events"] if e["series"] > 0]
  kinds = sorted({e["kind"] for e in evs})
  decades = sorted({e["date"][:3] + "0s" for e in evs})
  grid = [[d] + [sum(1 for e in evs if e["kind"] == k and e["date"][:3] + "0s" == d) for k in kinds] for d in decades]
  low = [[s["series"], s["followed"], s["before"], s["after"], f"{s['followed'] / max(s['before'], 1):.0%}",
          " ".join(s["flags"])] for s in review["steps"] if s["followed"] < 0.9 * max(s["before"], 1)]
  parts = [
    f"<h1>Cells: review</h1><p>{len(cells['frames'])} frames, {len(cells['units'])} units, {len(evs)} events after "
    f"1961. Ids are in <span class=k>cells.json</span>; calls on events go in <span class=k>src/cells-names.yml</span> "
    f"as <span class=k>&lt;series&gt;:&lt;kind&gt;:&lt;first id&gt;: keep | drop | &lt;kind&gt;</span>.</p>",
    "<h2>Events by decade</h2>", _t(grid, ["decade"] + kinds),
    "<h2>Events at re-issues and restarts (check these first)</h2>",
    _t([[e["series"], e["date"], e["kind"], e["caption"], " ".join(e.get("flags", []))] for e in review["flagged"]],
       ["series", "date", "kind", "caption", "frame"]),
    "<h2>All events</h2>",
    _t([[e["series"], e["date"], e["kind"], e["caption"], " ".join(e["from"]) + " → " + " ".join(e["to"])]
        for e in evs], ["series", "date", "kind", "caption", "ids"]),
    "<h2>Left out: differences at units the amendment does not touch</h2>"
    "<p class=n>Usually a reading or matching fault. If one is real, add a call to keep it.</p>",
    _t([[e["series"], e["kind"], e["caption"]] for e in review["dropped_untouched"]], ["series", "kind", "caption"]),
    "<h2>Steps where under 90% of subjects were followed</h2>",
    _t(low, ["series", "followed", "before", "after", "share", "frame"]),
    "<h2>Units with no name</h2>", _t([[x["series"], x["heading"], x["size"]] for x in review["unnamed"]],
                                       ["series", "heading", "subjects"]),
    "<h2>First Schedule items with no Second Schedule unit</h2>",
    _t([[x["series"], ", ".join(x["units"])] for x in review["first_only"]], ["series", "units"]),
    "<h2>Units with no subjects</h2>", _t([[x["series"], x["unit"]] for x in review["empty"]], ["series", "unit"]),
  ]
  return f"<!doctype html><meta charset=utf-8><title>Cells review</title><style>{CSS}</style>" + "".join(parts)
