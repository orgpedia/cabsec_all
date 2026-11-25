"""The ministry pages (ui-requirements §9b): one page for each top-level unit, telling its story through its own
changes (U52–U57), a small page at each of its earlier names that sends the reader on, and the index /ministry/
(U57a). Reads ui/timeline.json (units, frames, events, office-holders, each unit's address) and this task's
cells.json (the subjects each change moved, the amendment's changes behind it); the subjects today come from the
states. Written into <site>/ministry/."""

import json
from pathlib import Path
from typing import Any

from . import count, read, slugs
from .site import CHEV, E, clip, day_before, fmt, page

SECTORS = {"econ": ("Economy & industry", "#3D5A80"), "infra": ("Infrastructure & energy", "#5B5788"),
           "land": ("Land, water & rural", "#4A7766"), "social": ("Social & culture", "#9C6B3F"),
           "secur": ("Security & external", "#93525A"), "sci": ("Science", "#3C7480"), "gov": ("Centre of government", "#5A6472")}
KIND = {"born": "Created", "ended": "Abolished", "split": "Split", "merged": "Merged", "spun_off": "Spun off",
        "absorbed": "Absorbed", "moved": "Moved", "renamed": "Renamed", "grew": "Grew", "shrank": "Shrank"}


def build(tl: dict[str, Any], cells: dict[str, Any], states: Path, base: Path, base_date: str, site: Path,
          reissues: set[int]) -> int:
  units, frames, people = tl["units"], tl["frames"], tl["people"]
  date_of = {f["series"]: f["date"] for f in frames}
  order = [f["series"] for f in frames]
  slug = {u: v["slug"] for u, v in units.items()}
  ckey = {(e["series"], e["kind"], tuple(e["from"]), tuple(e["to"])): e for e in cells["events"]}
  pms = sorted((p for p in people if p["office"] == "pm"), key=lambda p: p["from"])
  rp = "../../"

  def pm_at(d: str) -> str:
    p = next((p for p in reversed(pms) if p["from"] <= d), None)
    return p["name"].replace(" (acting)", "") if p else ""

  def yr(s: Any) -> str:
    return (date_of.get(s) or "")[:4]

  def name_at(uid: str, s: int) -> dict[str, Any]:
    ns = units[uid]["names"]; n = ns[0]
    for x in ns:
      if x["from"] <= s: n = x
    return n

  def link(uid: str, s: int) -> str:
    return f'<a href="{rp}ministry/{slug[uid]}/">{E(name_at(uid, s)["name"])}</a>'

  def years(u: dict[str, Any]) -> str:
    a = yr(u["born"]); b = yr(u["ended"]) if u.get("ended") is not None else None
    return f"since {a}" if b is None else (a if a == b else f"{a}–{b}")

  # each unit's subjects when last seen: read only the frames some unit ends at (or the last)
  last_of = {}
  for f in frames:
    for uid in f["sizes"]:
      last_of[uid] = f["series"]
  want = set(s for s in last_of.values() if s >= 0)
  texts: dict[str, list[str]] = {}
  cframes = {f["series"]: f for f in cells["frames"]}
  for fr in read.frames(states, base, base_date):
    if fr["series"] not in want:
      continue
    got = [u for u in count.units(fr["tree"])["units"] if u["name"].strip() or u["size"]]
    for u, uid in zip(got, list(cframes[fr["series"]]["sizes"])):
      if last_of.get(uid) == fr["series"]:
        texts[uid] = u["texts"]

  evs_of: dict[str, list[dict[str, Any]]] = {}
  for e in tl["events"]:
    for uid in set(e["from"] + e["to"]):
      evs_of.setdefault(uid, []).append(e)

  n_pages = 0
  # whose lines each unit is part of (U67): an earlier unit's page says where its line goes on
  goes_on: dict[str, list[str]] = {}
  for x, v in units.items():
    for a in (v.get("line") or [])[:-1]:
      goes_on.setdefault(a, []).append(x)

  for uid, u in units.items():
    line = u.get("line") or [uid]; inline = set(line)
    line_evs = sorted({id(e): e for x in line for e in evs_of.get(x, [])}.values(), key=lambda e: (e["date"], e["series"]))
    last = u["names"][-1]; sec = SECTORS.get(u.get("sector"), ("", "#9ca3af"))
    kind = {"ministry": "Ministry", "department": "Department", "office": "Office"}.get(last.get("kind"), "Unit")
    alive = u.get("ended") is None
    # names over time (U52)
    nm = []
    for k, n in enumerate(u["names"]):
      a = yr(n["from"]) if n["from"] != u["born"] or k else yr(u["born"])
      nxt = u["names"][k + 1]["from"] if k + 1 < len(u["names"]) else u.get("ended")
      b = yr(nxt) if nxt is not None else "today"
      nm.append((n["name"], a if a == b else f"{a}–{b}"))
    earlier = [x for x in nm[:-1]][::-1]
    # the family (U53)
    came, gave, succ = {}, {}, {}
    for e in line_evs:
      if inline & set(e["to"]):
        for o in e["from"]:
          if o not in inline: came[o] = e["series"]
      if inline & set(e["from"]):
        for o in e["to"]:
          if o not in inline: (succ if e["kind"] in ("absorbed", "merged", "split") and u.get("ended") == e["series"] and o not in e["from"] else gave)[o] = e["series"]
    for p in cells["units"].get(uid, {}).get("parents", []) or []:
      came.setdefault(p, u["born"])
    def lst(d: dict[str, int]) -> str:
      return ", ".join(link(o, s if o not in units or not units[o].get("ended") or units[o]["ended"] > s else units[o]["born"]) for o, s in d.items() if o in units)
    fam = []
    if came: fam.append(f"<p><b>Came from:</b> {lst(came)}</p>")
    if gave: fam.append(f"<p><b>Gave subjects to:</b> {lst(gave)}</p>")
    if succ: fam.append(f"<p><b>Succeeded by:</b> {lst(succ)}</p>")
    if u.get("parents") or cells["units"].get(uid, {}).get("parents"):
      fam.append('<p class="meta" style="font-size:12.5px">Where a merger or a split kept one unit going, it is the one that brought or kept the larger share of subjects.</p>')
    # size over time (U55): an SVG strip, a bar a year, shaded by Prime Minister
    y0 = int(yr(units[line[0]]["born"])); y1 = int(yr(u["ended"])) if u.get("ended") is not None else int(frames[-1]["date"][:4])
    size_y: dict[int, int] = {}
    cur = None
    for f in frames:
      y = int(f["date"][:4])
      if y < y0 or y > y1: continue
      if uid in f["sizes"]: cur = f["sizes"][uid]
      if cur is not None: size_y[y] = cur
    ys = list(range(y0, y1 + 1)); W = max(len(ys), 1) * 12; H = 90
    mx = max(size_y.values() or [1]) or 1
    bands = []
    for k, p in enumerate(pms):
      a = max(int(p["from"][:4]), y0); b = min(int((p["to"] or "9999")[:4]), y1)
      if b < a: continue
      bands.append(f'<rect x="{(a - y0) * 12}" y="0" width="{(b - a + 1) * 12}" height="{H}" fill="{"#f3f4f6" if k % 2 else "#e5e7eb"}" opacity=".7"><title>{E(p["name"])}</title></rect>')
    bars = []
    for y in ys:
      v = size_y.get(y)
      if v is None: continue
      h = max(2, 74 * v / mx)
      bars.append(f'<rect x="{(y - y0) * 12 + 2}" y="{H - h}" width="8" height="{h}" rx="1.5" fill="{sec[1]}"><title>{y}: {v} subject{"s" if v != 1 else ""} · {E(pm_at(f"{y}-07-01"))}</title></rect>')
    marks = sorted({int(e["date"][:4]) for e in evs_of.get(uid, []) if e["kind"] not in ("grew", "shrank")})
    mk = "".join(f'<circle cx="{(y - y0) * 12 + 6}" cy="5" r="3" fill="#d97706"><title>{y}: a change</title></circle>' for y in marks if y0 <= y <= y1)
    ticks = "".join(f'<text x="{(y - y0) * 12 + 6}" y="{H + 13}" font-size="10" text-anchor="middle" fill="#6b7280">{y}</text>' for y in ys if (y % 10 == 0) or y in (y0, y1))
    strip = (f'<svg class="strip" viewBox="0 0 {W} {H + 16}" role="img" aria-label="Number of subjects by year">{"".join(bands)}{"".join(bars)}{mk}{ticks}</svg>'
             f'<p class="meta" style="font-size:12.5px;margin:4px 0 0">Bars: its number of subjects at the end of each year{" (before 1961, worked back from 1961)" if y0 < 1961 else ""}; '
             'shading: the Prime Ministers\' terms; dots: its changes. Point at a bar for the year.</p>')
    # its changes (U56)
    rows = []
    for e in line_evs:
      s = e["series"]; approx = "approx" in (e.get("flags") or []); re_ = s in reissues
      ce = ckey.get((s, e["kind"], tuple(e["from"]), tuple(e["to"])), {})
      others = [o for o in dict.fromkeys(e["from"] + e["to"]) if o not in inline and o in units]
      prev = order[order.index(s) - 1] if s in order and order.index(s) else s
      oth = ", ".join(link(o, prev if o in e["from"] else s) for o in others)
      am = ""
      if s > 0 and not approx:
        cs = (e.get("changes") or [])[:8]
        am = (f'<a class="doc" href="{rp}amend/{s}/" target="_blank" rel="noopener">{"Re-issue" if re_ else "Amendment"} #{s}</a>'
              + (" · change " + ", ".join(f'<a href="{rp}amend/{s}/#c{c}" target="_blank" rel="noopener">{c}</a>' for c in cs) if cs and not re_ else ""))
        sz = cframes.get(s, {}).get("sizes") or {}; who = next((x for x in reversed(line) if x in sz), None)
        am += (f' · <a href="{rp}rules/{s}/#{who}" target="_blank" rel="noopener">the Rules after it</a>' if who
               else f' · <a href="{rp}rules/{s - 1}/" target="_blank" rel="noopener">the Rules before it</a>')
      subs = ce.get("subjects") or {}
      to_line = [x for x in e["to"] if x in inline]
      mine = [t for x in to_line for t in subs.get(x, [])] if to_line else [t for ts in subs.values() for t in ts] if inline & set(e["from"]) else []
      sub = ""
      if mine and not re_:
        li = "".join(f"<li>{E(clip(t, 220))}</li>" for t in mine)
        sub = (f'<details class="subs"><summary>{"The subjects it took" if to_line else "The subjects that left"} ({len(mine)})</summary><ul>{li}</ul></details>')
      rows.append(f'<li class="mev"><div class="when">{fmt(e["date"])}<br><span>{E(pm_at(e["date"]))}</span></div><div class="what">'
                  f'<span class="k{" b" if e.get("salient") else ""}">{KIND.get(e["kind"], e["kind"])}</span>{E(e.get("story") or e["caption"])}'
                  + (f'<div class="oth">With: {oth}</div>' if oth else "") + (f'<div class="am">{am}</div>' if am else "") + sub + "</div></li>")
    # its subjects (U57)
    ls = last_of.get(uid)
    ts = texts.get(uid, [])
    if ts:
      subj = (f'<details class="card subj"{" open" if len(ts) <= 12 else ""}><summary><b>{"Its subjects today" if alive else f"Its subjects when it ended ({yr(ls)})"}</b> · {len(ts)}</summary>'
              f'<ol>{"".join(f"<li>{E(clip(t, 400))}</li>" for t in ts)}</ol>'
              f'<p class="meta" style="font-size:13px">As in the <a href="{rp}rules/{ls}/#{uid}">Rules after amendment #{ls}</a> (an inferred text). For another date, follow a change\'s link to the Rules after it.</p></details>')
    elif ls is not None and ls < 0:
      subj = '<p class="note">This unit ended before the Allocation of Business Rules of 1961, so there are no subjects to show: only its names and changes, from the cabinet lists.</p>'
    else:
      subj = ""
    lsec = ""
    if len(line) > 1:
      lsec = ('<div class="card line"><b>Its line</b>: ' + ' <span class="arr">→</span> '.join(
        (f'<b>{E(units[x]["names"][-1]["short"])}</b> <span>{years(units[x])}</span>' if x == uid else
         f'<a href="{rp}ministry/{slug[x]}/">{E(units[x]["names"][-1]["short"])}</a> <span>{years(units[x])}</span>') for x in line)
        + '<p class="meta" style="font-size:12.5px;margin:4px 0 0">The units it carries on, through its splits and mergers, back to where it began. '
          'Its changes and its story in cells below follow the whole line.</p></div>')
    on = [x for x in goes_on.get(uid, []) if x != uid]
    if on:
      lsec += ('<div class="card line"><b>Its line goes on in</b>: ' + ", ".join(f'<a href="{rp}ministry/{slug[x]}/">{E(units[x]["names"][-1]["name"])}</a> <span>{years(units[x])}</span>' for x in on) + "</div>")
    gaps = '<p class="note">Before 2004 the readings of the scanned gazettes have known gaps, so some changes may be missing or read loosely.</p>' if y0 < 2004 else ""
    title = last["name"]
    head = (f'<h1>{E(title)}</h1><p class="meta"><span class="dot" style="background:{sec[1]}"></span>{E(kind)} · {E(sec[0])} · {years(u)}'
            + (f' · its line since {yr(units[line[0]]["born"])}' if len(line) > 1 else "")
            + (" · abolished" if not alive else "") + "</p>"
            + (f'<p class="formerly">{"Formerly" if alive else "Earlier"}: ' + " · ".join(f"{E(n)} <span>{y}</span>" for n, y in earlier) + "</p>" if earlier else ""))
    links = [f'<a href="{rp}#at={date_of.get(max(u["born"], 0)) or ""}">On the chart</a>']
    if ls is not None and ls >= 0: links.append(f'<a href="{rp}rules/{ls}/#{uid}">Its section of the Rules</a>')
    links.append(f'<a href="{rp}ministry/">All ministries</a>')
    body = (head + f'<div class="links">{"".join(links)}</div>{gaps}'
            + lsec + (f'<div class="card fam">{"".join(fam)}</div>' if fam else "")
            + f'<h2>Its story in cells</h2><div class="card anim"><iframe src="{rp}index.html?unit={uid}" title="{E(title)}: its changes, as cells" loading="lazy"></iframe>'
              f'<p class="meta" style="font-size:12.5px;margin:6px 0 0">Only its own changes play, with a caption; the rest of the government changes quietly in the background. '
              f'The units it dealt with stand out. Click a cell for its subjects in the Rules.</p></div>'
            + f'<h2>Its changes</h2><ol class="mevs">{"".join(rows) or "<li>No change recorded.</li>"}</ol>'
            + (f"<h2>Its subjects</h2>{subj}" if subj else ""))
    alln = [n for n, _ in nm]
    desc = (f"The history of the {title}" + (f" (formerly {', '.join(dict.fromkeys(alln[:-1][::-1]))})" if len(alln) > 1 else "")
            + f": its names, the ministries it came from and gave rise to, its {len(line_evs)} changes and its subjects, from the Allocation of Business Rules.")
    ld = {"@context": "https://schema.org", "@type": "GovernmentOrganization", "name": title,
          "alternateName": list(dict.fromkeys(alln[:-1])), "parentOrganization": {"@type": "GovernmentOrganization", "name": "Government of India"},
          "foundingDate": date_of.get(u["born"]), **({"dissolutionDate": date_of.get(u["ended"])} if not alive else {})}
    html_ = page(rp, f"{title}: its history", clip(desc, 300),
                 [("Home", "https://www.orgpedia.in/"), ("Ministries as cells", rp), ("Ministries", f"{rp}ministry/"), (last["short"], None)], body, "", ld)
    d = site / "ministry" / slug[uid]; d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(html_, encoding="utf-8"); n_pages += 1

  # the earlier names (U52): a page that sends the reader on, or a choice where two units bore the name
  for s, uids in slugs.former(units, slug).items():
    d = site / "ministry" / s; d.mkdir(parents=True, exist_ok=True)
    if len(uids) == 1:
      to = f"{rp}ministry/{slug[uids[0]]}/"
      html_ = (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>{E(units[uids[0]]["names"][-1]["name"])}</title>'
               f'<link rel="canonical" href="{to}"><meta http-equiv="refresh" content="0; url={to}"></head><body>'
               f'<p>This ministry is now the <a href="{to}">{E(units[uids[0]]["names"][-1]["name"])}</a>.</p></body></html>')
    else:
      lis = "".join(f'<li><a href="{rp}ministry/{slug[x]}/">{E(units[x]["names"][-1]["name"])}</a> ({years(units[x])})</li>' for x in uids)
      html_ = page(rp, "More than one ministry bore this name", "More than one ministry of the Government of India bore this name.",
                   [("Home", "https://www.orgpedia.in/"), ("Ministries", f"{rp}ministry/"), ("Which one?", None)],
                   f"<h1>More than one ministry bore this name</h1><ul class='evs'>{lis}</ul>")
    (d / "index.html").write_text(html_, encoding="utf-8")

  # the index (U57a)
  groups = []
  for key, (label, col) in SECTORS.items():
    us = [x for x in units if units[x].get("sector") == key]
    if not us: continue
    now = sorted((x for x in us if units[x].get("ended") is None), key=lambda x: units[x]["names"][-1]["name"])
    past = sorted((x for x in us if units[x].get("ended") is not None), key=lambda x: (units[x]["born"], units[x]["names"][-1]["name"]))
    li = lambda x: (f'<li><a href="{x and slug[x]}/">{E(units[x]["names"][-1]["name"])}</a> <span>{years(units[x])} · {len(evs_of.get(x, []))} change{"" if len(evs_of.get(x, [])) == 1 else "s"}</span></li>')
    groups.append(f'<div class="card sect"><h3><i style="background:{col}"></i>{E(label)}</h3>'
                  + (f'<ul class="ix">{"".join(li(x) for x in now)}</ul>' if now else "")
                  + (f'<details><summary>Abolished ({len(past)})</summary><ul class="ix past">{"".join(li(x) for x in past)}</ul></details>' if past else "") + "</div>")
  body = ('<h1>The ministries of the Government of India, and their histories</h1>'
          f'<p class="meta">Every ministry, department and office at the top of the Allocation of Business Rules since 1947: {sum(1 for x in units.values() if x.get("ended") is None)} today and '
          f'{sum(1 for x in units.values() if x.get("ended") is not None)} abolished, each with its names, its changes and its subjects.</p>' + "".join(groups))
  html_ = page("../", "The ministries of the Government of India: their histories", "Every ministry, department and office of the Government of India since 1947, with its names, changes and subjects.",
               [("Home", "https://www.orgpedia.in/"), ("Ministries as cells", "../"), ("Ministries", None)], body)
  (site / "ministry").mkdir(parents=True, exist_ok=True)
  (site / "ministry/index.html").write_text(html_, encoding="utf-8")
  return n_pages
