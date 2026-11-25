"""The document pages of the site (ui-requirements §9a): an amendment page for each amendment (U43–U46) and a Rules
page for each version of the Rules (U47), written out as HTML (U48) into <site>/amend/<n>/ and <site>/rules/<n>/.
Reads the states' output (chain, changes, inferences, known issues), the amendments' extracted files and edits, the
cabsec listings, this task's cells.json (each unit's places in the schedules) and <site>/data/pages.json (from
pageimages). Links are relative, so the site works wherever it is served."""

import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from . import count, read

E = html.escape
MONTHS = "January February March April May June July August September October November December".split()


def fmt(iso: str | None) -> str:
  if not iso:
    return ""
  y, m, d = (int(x) for x in iso[:10].split("-"))
  return f"{d} {MONTHS[m - 1]} {y}"


def clip(s: str, n: int = 240) -> str:
  s = " ".join(str(s or "").split())
  return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


CHEV = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6 4l4 4-4 4" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def page(root: str, title: str, desc: str, crumbs: list[tuple[str, str | None]], body: str, script: str = "",
         ld: dict[str, Any] | None = None) -> str:
  """One page in orgpedia's style (U51): the header bar, the breadcrumb, the body, the footer."""
  cr = CHEV.join(f'<a href="{E(h)}">{E(t)}</a>' if h else f'<span class="here">{E(t)}</span>' for t, h in crumbs)
  ldj = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
  return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="article">
<meta name="twitter:card" content="summary"><link rel="icon" href="data:,"><link rel="stylesheet" href="{root}assets/site.css">{ldj}</head>
<body><header><div class="site-bar"><div class="site-in">
<a href="https://www.orgpedia.in/" class="site-brand" title="orgpedia"><div class="site-op"><p><span>o</span>p</p></div><div class="site-word"><img src="{root}l-en.svg" alt="Orgpedia"></div></a><a class="site-title" href="{root}">Evolution of Ministries</a>
</div></div></header>
<main><div class="crumbs">{cr}</div>
{body}
<p class="srcnote">From the Government of India (Allocation of Business) Rules, 1961 and their amendments, as published by the Cabinet Secretariat (cabsec.gov.in), read by orgpedia. The readings of the older scanned gazettes have known gaps.</p>
</main>
<footer class="site-foot"><div class="in"><a href="https://www.orgpedia.in/"><img src="{root}l-en.svg" alt="Orgpedia"></a><a href="https://www.orgpedia.in/disclaimer.html">Disclaimer</a><a href="https://github.com/orgpedia/site.cabsec-aob/issues">Report an error</a><a href="https://github.com/orgpedia/site.cabsec-aob">View on GitHub</a><a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a></div></footer>{script}</body></html>
'''


def cited(cs: Any) -> str:
  """"Schedule 2 › Ministry of Law › entry 8" from a change's cited parts."""
  out = []
  for c in cs or []:
    t = c.get("type", "")
    if t == "schedule":
      out.append(f"Schedule {c.get('num', '')}")
    elif c.get("heading"):
      out.append(c["heading"].strip())
    else:
      out.append(f"{t.replace('_', ' ')} {c.get('num', '')}".strip())
  return " › ".join(out)


def targets(op: dict[str, Any]) -> list[dict[str, Any]]:
  t = op.get("target")
  return t if isinstance(t, list) else [t] if isinstance(t, dict) else []


def content(op: dict[str, Any]) -> str:
  items = []
  for c in op.get("content") or []:
    if not isinstance(c, dict):
      continue
    num = f'{E(str(c["num"]))}. ' if c.get("num") else ""
    txt = c.get("heading") or c.get("text") or ""
    items.append(f"<li>{num}{E(clip(txt, 300))}</li>")
  if not items:
    return ""
  head, rest = items[:6], items[6:]
  more = f'<details><summary>and {len(rest)} more</summary><ul>{"".join(rest)}</ul></details>' if rest else ""
  return f'<ul>{"".join(head)}</ul>{more}'


OPS = {"insert": "Insert", "omit": "Omit", "replace": "Replace", "substitute_text": "Substitute words", "renumber": "Renumber"}


def card(op: dict[str, Any], res: dict[str, Any] | None, root: str, after: int) -> str:
  n = op["seq"]
  bits = [f'<div class="hd"><a class="n" href="#c{n}">Change {n}</a><span class="k b">{E(OPS.get(op["op"], op["op"]))}</span>'
          f'<span class="ref">clause {E(str(op.get("source_ref") or ""))}</span></div>']
  ts = [cited(t.get("cited")) for t in targets(op)]
  if ts:
    bits.append(f'<div class="cite">{"; ".join(E(t) for t in ts if t)}</div>')
  if op.get("anchor"):
    bits.append(f'<div class="cite">{E(op.get("position") or "at")} {E(cited(op["anchor"].get("cited")))}</div>')
  if op.get("old") is not None or op.get("new") is not None:
    bits.append(f'<div>for “{E(clip(op.get("old") or "", 200))}” read “{E(clip(op.get("new") or "", 200))}”</div>')
  if op.get("new_num"):
    bits.append(f'<div>renumbered as {E(str(op["new_num"]))}</div>')
  bits.append(content(op))
  if res:
    ok = res.get("status") == "applied"
    b = (res.get("before") or [{}])[0]; a = (res.get("after") or [{}])[0]
    where = (a or b).get("path", "")
    line = f'<span class="k {"ok" if ok else "no"}">{"applied" if ok else "not applied"}</span>'
    if ok:
      line += f' at <b>{E(clip(where, 120))}</b> in the <a href="{root}rules/{after}/">Rules after #{after}</a>'
    else:
      line += " (the change could not be placed in the Rules as read; see How this document was read)"
    bits.append(f'<div class="res">{line}</div>')
  fl = [f for f in op.get("flags") or []]
  if fl:
    bits.append(f'<div class="fl">{E(", ".join(f.replace("_", " ") for f in fl))}</div>')
  return f'<div class="ch" id="c{n}" data-c="{n}">{"".join(bits)}</div>'


def day_before(iso: str) -> str:
  y, m, d = (int(x) for x in iso[:10].split("-"))
  return date.fromordinal(date(y, m, d).toordinal() - 1).isoformat()


def seqlink(x: dict[str, Any]) -> str:
  return f'<a href="#c{x["seq"]}">{x["seq"]}</a>' if x.get("seq") else ""


def edits_table(file: str, flow: Path) -> str:
  p = flow / "aob-ammend_/conf" / f"{file}.edits.yml"
  if not p.exists():
    return ""
  y = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
  rows = []
  for r in y.get("runs") or []:
    who, at = r.get("by", ""), fmt(str(r.get("at", ""))[:10])
    for e in r.get("edits") or []:
      op = e.get("op", "")
      b, a = e.get("before"), e.get("after")
      def txt(x):
        if isinstance(x, dict):
          if "text" in x: return str(x["text"])
          if "word" in x and isinstance(x["word"], dict): return str(x["word"].get("text", ""))
          return ", ".join(f"{k}: {clip(json.dumps(v, ensure_ascii=False), 80)}" for k, v in x.items() if k not in ("page", "line", "after", "bbox"))
        return "" if x is None else str(x)
      what = {"text": "word corrected", "remove_word": "word removed", "add_word": "word added", "fields": "fields set"}.get(op, op)
      rows.append(f"<tr><td>{E(at)}</td><td>{E(str(who))}</td><td>{E(what)}</td><td><del>{E(clip(txt(b), 120))}</del> → <ins>{E(clip(txt(a), 120))}</ins></td></tr>")
  if not rows:
    return ""
  return ('<h3 style="margin:14px 0 6px">Edits to the reading</h3><table class="ed"><tr><th>Date</th><th>By</th><th>Edit</th>'
          f'<th>Before → after</th></tr>{"".join(rows)}</table>')


def main(cfg_path: str, site_dir: str) -> None:
  cfg_path = Path(cfg_path).resolve(); root_dir = cfg_path.parent
  cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
  flow = root_dir.parent.parent
  states = (root_dir / cfg["states"]).resolve()
  base = (root_dir / cfg["base"]).resolve()
  site = Path(site_dir).resolve()
  inputs = flow.parent / "input/documents"
  chain = read.chain(states)
  changes = read.changes(states)
  items = {int(i["source_key"]): i for i in json.loads((inputs / "aob-ammend/items.json").read_text(encoding="utf-8"))
           if str(i.get("source_key", "")).isdigit()}
  rules_items = {i["file_key"] + ".pdf": i for i in json.loads((inputs / "aob-rules/items.json").read_text(encoding="utf-8"))}
  infer: dict[int, list[dict[str, Any]]] = {}
  for x in json.loads((states / "inferences.json").read_text(encoding="utf-8")):
    infer.setdefault(x["series"], []).append(x)
  known_titles = {k["id"]: k.get("title", k["id"]) for k in (yaml.safe_load((flow / "aob-states_/src/known.yml").read_text(encoding="utf-8")) or {}).get("changes", [])}
  known: dict[int, list[dict[str, Any]]] = {}
  kj = read.known(states) or {}
  for seg in kj.get("segments", []):
    for x in seg.get("changes", []):
      known.setdefault(x["series"], []).append(x)
  pages = json.loads((site / "data/pages.json").read_text(encoding="utf-8"))
  cells = json.loads((root_dir / cfg.get("out", "../output") / f'{cfg.get("stem", "cells")}.json').resolve().read_text(encoding="utf-8"))
  frames = {f["series"]: f for f in cells["frames"]}
  tl = json.loads(((root_dir / cfg.get("ui", "../ui")).resolve() / "timeline.json").read_text(encoding="utf-8"))
  slug = {u: v.get("slug") for u, v in tl["units"].items()}
  units = cells["units"]
  evs: dict[int, list[dict[str, Any]]] = {}
  for e in cells["events"]:
    if e["series"]:
      evs.setdefault(e["series"], []).append(e)
  reissues = set(cfg.get("reissues") or [])
  notes = {int(k): v for k, v in (cfg.get("reissue_notes") or {}).items()}
  last = max(chain)
  n_amend = n_rules = 0

  # ---------- amendment pages ----------
  for s, c in sorted(chain.items()):
    file = c["file"]; it = items.get(s, {})
    out_p = flow / "aob-ammend_/output" / f"{file}.json"
    ops = []
    if out_p.exists():
      for doc in json.loads(out_p.read_text(encoding="utf-8")).get("documents", []):
        ops += (doc.get("amendment") or {}).get("ops", [])
    res = {x["seq"]: x for x in changes.get(s, [])}
    rp = "../../"
    so = it.get("gazette") or ""
    title = f"Amendment #{s}" + (f" ({so}, {fmt(it.get('gazette_date'))[-4:]})" if so else "")
    is_re = s in reissues
    meta = []
    if it.get("date"): meta.append(f"Order dated {fmt(it['date'])}")
    if so: meta.append(f"{E(so)}, published {fmt(it.get('gazette_date'))}" if it.get("gazette_date") else E(so))
    if c.get("date"): meta.append(f"in force from {fmt(c['date'])}")
    links = []
    if it.get("file_url") or out_p.exists():
      url = it.get("file_url") or ""
      if url: links.append(f'<a class="ext" href="{E(url)}" rel="noopener" target="_blank">The order on cabsec.gov.in (PDF)</a>')
    links.append(f'<a href="{rp}rules/{s - 1}/">The Rules before (after #{s - 1})</a>' if s > 1 else f'<a href="{rp}rules/0/">The Rules before (1961)</a>')
    links.append(f'<a href="{rp}rules/{s}/">The Rules after #{s}</a>')
    links.append(f'<a href="{rp}amend/{s - 1}/">← #{s - 1}</a>' if s > 1 else '<span>← first</span>')
    links.append(f'<a href="{rp}amend/{s + 1}/">#{s + 1} →</a>' if s < last else '<span>latest →</span>')
    body = [f'<h1>{E(title)}</h1><p class="meta">{" · ".join(meta)}</p><div class="links">{"".join(links)}</div>']
    sched: dict[str, int] = {}
    seqs = sorted({op["seq"] for op in ops} | set(res))
    for q in seqs:
      op = next((o for o in ops if o["seq"] == q), None); sc = None
      for t in (targets(op) + ([op["anchor"]] if op.get("anchor") else [])) if op else []:
        sc = next((str(x.get("num")) for x in t.get("cited") or [] if x.get("type") == "schedule"), None) or sc
      if not sc and q in res:
        pth = ((res[q].get("after") or res[q].get("before") or [{}])[0]).get("path", "")
        m_ = re.match(r"schedule (\d)", pth); sc = m_[1] if m_ else None
      sched[sc or "other"] = sched.get(sc or "other", 0) + 1
    if seqs:
      ok = sum(1 for q in seqs if res.get(q, {}).get("status") == "applied")
      parts = [f'<b>{sched.get("1", 0)}</b> to the First Schedule', f'<b>{sched.get("2", 0)}</b> to the Second Schedule']
      if sched.get("other"): parts.append(f'<b>{sched["other"]}</b> to the rules of the Order or not placed')
      body.append(f'<div class="card counts"><b style="font-size:20px">{len(seqs)}</b> change{"s" if len(seqs) != 1 else ""}: {", ".join(parts)}. '
                  f'<span class="k ok">{ok} applied</span>' + (f'<span class="k no">{len(seqs) - ok} not applied</span>' if len(seqs) - ok else "") + '</div>')
    if is_re:
      body.append(f'<p class="note"><b>A re-issue, not an amendment.</b> {E(notes.get(s, "The schedules are printed afresh."))} '
                  'Its pages are not shown here; the order is on cabsec.gov.in.</p>')
    ce = evs.get(s, [])
    if ce:
      lis = "".join(f'<li><span class="k">{E(e["kind"].replace("_", " "))}</span>{E(e.get("story") or e["caption"])}'
                    + (f' <a href="#c{e["changes"][0]}">change {", ".join(str(x) for x in e["changes"][:6])}</a>' if e.get("changes") and not is_re else "")
                    + (' <span class="hists">· histories: ' + ", ".join(f'<a href="{rp}ministry/{slug[x]}/">{E(tl["units"][x]["names"][-1]["short"])}</a>' for x in dict.fromkeys(e["from"] + e["to"]) if slug.get(x)) + "</span>")
                    + "</li>" for e in ce)
      body.append(f'<div class="card"><h3 style="margin-bottom:4px">What it did to the ministries</h3><ul class="evs">{lis}</ul>'
                  f'<p class="meta" style="margin:6px 0 0;font-size:13px"><a href="{rp}#at={c.get("date") or ""}">See it on the chart</a></p></div>')
    if not is_re and file in pages and ops:
      pg = pages[file]
      onpage: dict[int, list[dict[str, Any]]] = {}
      boxes: dict[int, list[tuple[int, list[int]]]] = {}
      for op in ops:
        bs = list(op.get("boxes") or []) + [b for t in targets(op) for b in (t.get("boxes") or [])]
        first = min((b["page"] for b in bs), default=len(pg))
        onpage.setdefault(first, []).append(op)
        for b in op.get("boxes") or []:
          boxes.setdefault(b["page"], []).append((op["seq"], b["bbox"]))
      body.append(f'<h2>The order, page by page</h2><p class="meta" style="font-size:14px">Each change the reading found is boxed and numbered on the page; '
                  f'beside it, what was read and what it did to the Rules. Point at one to mark the other.</p>')
      for p in range(1, len(pg) + 1):
        dim = pg[p - 1]
        bx = "".join(
          f'<a class="bx" data-c="{n}" href="#c{n}" style="left:{100 * b[0] / dim["w"]:.2f}%;top:{100 * b[1] / dim["h"]:.2f}%;'
          f'width:{100 * (b[2] - b[0]) / dim["w"]:.2f}%;height:{100 * (b[3] - b[1]) / dim["h"]:.2f}%"><span>{n}</span></a>'
          for n, b in boxes.get(p, []))
        cards = "".join(card(op, res.get(op["seq"]), rp, s) for op in onpage.get(p, []))
        body.append(f'<section class="pg" id="p{p}"><h2>Page {p} of {len(pg)}</h2><figure class="img">'
                    f'<img src="{rp}pages/{file[:-4]}/{p}.webp" width="{dim["iw"]}" height="{dim["ih"]}" loading="{"eager" if p == 1 else "lazy"}" '
                    f'alt="{E(title)}, page {p} of the order">{bx}</figure><div class="cards">{cards or "<p class=meta>No change on this page.</p>"}</div></section>')
    elif res:
      body.append("<h2>Its changes</h2><div class='cards'>" + "".join(
        f'<div class="ch" id="c{x["seq"]}"><div class="hd"><a class="n" href="#c{x["seq"]}">Change {x["seq"]}</a><span class="k b">{E(OPS.get(x["op"], x["op"]))}</span>'
        f'<span class="k {"ok" if x["status"] == "applied" else "no"}">{"applied" if x["status"] == "applied" else "not applied"}</span></div>'
        f'<div class="cite">{E(clip(((x.get("after") or x.get("before") or [{}])[0]).get("path", ""), 160))}</div></div>'
        for x in sorted(res.values(), key=lambda x: x["seq"])) + "</div>")
    # how the document was read (U45)
    how = [edits_table(file, flow)]
    inf = infer.get(s, [])
    if inf:
      how.append('<h3 style="margin:14px 0 6px">Changes placed by an inference rule</h3><table class="ed"><tr><th>Change</th><th>Rule</th><th>Status</th><th>What</th></tr>'
                 + "".join(f'<tr><td>{seqlink(x)}</td><td>{E(x.get("rule", ""))}</td><td>{E(x.get("status", ""))}</td><td>{E(clip(x.get("message", ""), 200))}</td></tr>' for x in inf)
                 + "</table>")
    kn = known.get(s, [])
    if kn:
      how.append('<h3 style="margin:14px 0 6px">Known issues</h3><table class="ed"><tr><th>Change</th><th>Issue</th><th>Known as</th></tr>'
                 + "".join(f'<tr><td>{seqlink(x)}</td><td>{E(clip(x.get("message", ""), 200))}</td><td>{E(known_titles.get(x.get("known"), x.get("known") or "not yet explained"))}</td></tr>' for x in kn)
                 + "</table>")
    how = [h for h in how if h]
    body.append('<h2>How this document was read</h2>' + ("".join(how) if how else '<p class="meta">No edits: the reading was used as made.</p>'))
    desc = f'{title}: ' + ("; ".join(clip(e.get("story") or e["caption"], 90) for e in ce[:3]) or "a change to the Allocation of Business Rules, 1961") + "."
    ld = {"@context": "https://schema.org", "@type": "Legislation", "name": title, "legislationIdentifier": so or f"AoB amendment {s}",
          "legislationDate": it.get("date") or c.get("date"), "datePublished": it.get("gazette_date"),
          "legislationJurisdiction": "India", "isPartOf": "Government of India (Allocation of Business) Rules, 1961",
          **({"url": it["file_url"]} if it.get("file_url") else {})}
    html_ = page(rp, f"{title}: Allocation of Business Rules", desc,
                 [("Home", "https://www.orgpedia.in/"), ("Ministries as cells", rp), (f"Amendment #{s}", None)],
                 "\n".join(body), f'<script src="{rp}assets/amend.js"></script>', ld)
    d = site / "amend" / str(s); d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(html_, encoding="utf-8"); n_amend += 1

  # ---------- Rules pages ----------
  for fr in read.frames(states, base, cfg.get("base_date", "1961-01-14")):
    s = fr["series"]; tree = fr["tree"]; f = frames.get(s, {})
    eids = f.get("eids", {})
    s2uid = {v[0]: u for u, v in eids.items() if v and v[0]}
    s1uid = {v[1]: u for u, v in eids.items() if v and len(v) > 1 and v[1]}
    s2obj: dict[int, str] = {}; s1head: dict[str, str] = {}
    if f.get("sizes"):   # the units in the order the build read them (eIds can repeat, and the 1961 Rules have none)
      got = [u for u in count.units(tree)["units"] if u["name"].strip() or u["size"]]
      tops = [m for m in count.schedule(tree, "2").get("children", []) if m.get("type") in count.TOP and not count._omitted(m)]
      tops = [m for m, u in zip(tops, count.units(tree)["units"]) if u["name"].strip() or u["size"]]
      for m, u, uid in zip(tops, got, list(f["sizes"])):
        s2obj[id(m)] = uid
        if u.get("first"): s1head[u["first"]] = uid
    rp = "../../"
    def by(n: dict[str, Any]) -> str:
      m = re.match(r"^(\d+):(\d+)$", str(n.get("by") or ""))
      return f'<a class="by" href="{rp}amend/{m[1]}/#c{m[2]}" title="Put in by amendment #{m[1]}, change {m[2]}">#{m[1]}</a>' if m else ""
    def render(n: dict[str, Any], lv: int) -> str:
      t = n.get("type"); num = n.get("num"); head = (n.get("heading") or "").strip(); text = (n.get("text") or "").strip()
      om = n.get("omitted")
      cls = f' class="lv{min(lv, 4)}"' if lv > 1 else ""
      if t in ("entry", "item", "rule", "sub_rule"):
        body_ = '<span class="om">Omitted.</span>' if om else E(text or head)
        sub = "".join(render(k, lv + 1) for k in n.get("children", []))   # an entry's own items: (a), (b), …
        lab = (f"({num})" if t == "item" and not str(num).startswith("(") else f"{num}.") if num else ""
        return f'<p class="e{" lv" + str(min(lv, 4)) if lv > 1 else ""}"><span class="n">{E(str(lab))}</span><span class="t">{body_}{by(n)}</span></p>{sub}'
      out = []
      if head or num:
        out.append(f'<h4{cls}>{E(str(num)) + ". " if num and not head.upper().startswith("PART") else ""}{E(head)}{by(n)}</h4>')
      if text:
        out.append(f'<p{cls}>{E(text)}</p>')
      for k in n.get("children", []):
        out.append(render(k, lv + 1))
      return "".join(out)
    sch1 = count.schedule(tree, "1"); sch2 = count.schedule(tree, "2")
    order = next((k for k in tree.get("children", []) if k.get("type") == "order"), None)
    lis = []
    for m in sch1.get("children", []):
      if m.get("omitted") or not (m.get("heading") or "").strip():
        continue
      uid = s1head.get(m["heading"]) or s1uid.get(m.get("eId"))
      h = E(m["heading"].strip())
      head = f'<a href="#{uid}">{h}</a>' if uid else h
      deps = "".join(f'<li>{E(str(d.get("num") or ""))}. {E((d.get("heading") or "").strip())}</li>' for d in m.get("children", [])
                     if (d.get("heading") or "").strip() and not d.get("omitted"))
      lis.append(f'<li><span class="n">{E(str(m.get("num") or ""))}.</span>{head}{"<ul>" + deps + "</ul>" if deps else ""}</li>')
    secs = []; seen_e: set[str] = set()
    for m in sch2.get("children", []):
      if m.get("omitted"):
        continue
      uid = s2obj.get(id(m)) or s2uid.get(m.get("eId")) or (m.get("eId") or "").replace("__", "-")
      u = units.get(uid, {})
      sec = u.get("sector")
      col = {"econ": "#3D5A80", "infra": "#5B5788", "land": "#4A7766", "social": "#9C6B3F", "secur": "#93525A", "sci": "#3C7480", "gov": "#5A6472"}.get(sec, "#9ca3af")
      head = (m.get("heading") or m.get("text") or "").strip()
      inner = "".join(render(k, 1) for k in m.get("children", []))
      if not m.get("children") and m.get("text") and m.get("heading"):
        inner = f'<p>{E(m["text"])}</p>'
      hi = f'<p class="hi">{E(m["heading_hi"])}</p>' if m.get("heading_hi") else ""
      e_ = m.get("eId") or ""
      anchor = f'<span id="{E(e_)}"></span>' if e_ and e_ not in seen_e and e_ != uid else ""; seen_e.add(e_)
      secs.append(f'<section class="u" id="{E(uid)}">{anchor}<h3><i style="background:{col}"></i>{E(head)}{by(m)}'
                  f'<a class="hl" href="#{E(uid)}" title="Link to this section">#</a>'
                  + (f'<a class="hist" href="{rp}ministry/{slug[uid]}/">Its history →</a>' if slug.get(uid) else "") + f'</h3>{hi}{inner}</section>')
    c = chain.get(s, {})
    src = c.get("applied_to") if s else base.name.replace(".json", "")
    ri = rules_items.get(src or "", {})
    title = "The Allocation of Business Rules, 1961, as made" if s == 0 else f"The Allocation of Business Rules after amendment #{s}"
    nxt = frames.get(s + 1, {}).get("date")
    d0 = fr["date"]
    if not nxt: when = f"In force from {fmt(d0)} to today"
    elif nxt <= d0: when = f"In force on {fmt(d0)}, replaced the same day"
    elif day_before(nxt) == d0: when = f"In force on {fmt(d0)} only"
    else: when = f"In force from {fmt(d0)} to {fmt(day_before(nxt))}"
    meta = [when]
    if s: meta.append(f'made by <a href="{rp}amend/{s}/">amendment #{s}</a>')
    if nxt: meta.append(f'replaced by <a href="{rp}amend/{s + 1}/">amendment #{s + 1}</a>')
    links = []
    if ri.get("file_url"):
      links.append(f'<a class="ext" href="{E(ri["file_url"])}" rel="noopener" target="_blank">{"The Rules" if s == 0 else "The consolidated Rules it was built from"} on cabsec.gov.in (PDF)</a>')
    if s: links.append(f'<a href="{rp}rules/{s - 1}/">← after #{s - 1}</a>' if s > 1 else f'<a href="{rp}rules/0/">← 1961</a>')
    links.append(f'<a href="{rp}rules/{s + 1}/">after #{s + 1} →</a>' if s < last else '<span>latest</span>')
    upto = c.get("applied_to_upto") or 0
    frm = "the Rules of 1961" if not src or src == base.name.replace(".json", "") else (f"the consolidated Rules on cabsec.gov.in (with the amendments up to #{upto})" if upto else "the consolidated Rules on cabsec.gov.in")
    span = f"amendment #{s}" if upto + 1 >= s else f"amendments #{upto + 1} to #{s}"
    note = ('<p class="note"><b>The Rules as printed in 1961</b>, read from the scanned order. The readings of the older scanned gazettes have known gaps.</p>' if s == 0 else
            f'<p class="note"><b>An inferred text, not an official one.</b> The Cabinet Secretariat does not publish the Rules after every amendment; '
            f'this version is worked out by applying {span}, as read from the gazettes, to {frm}. '
            'Where an amendment could not be placed, the text may differ from the real one; see each amendment\'s page. '
            'A small mark beside an entry names the amendment that put it in.</p>')
    od = ""
    if order:
      od = ('<details class="order card"><summary>The rules of the Order</summary>' + (f'<p>{E(order.get("heading") or "")}</p>' if order.get("heading") else "")
            + "".join(render(k, 1) for k in order.get("children", [])) + "</details>")
    body = (f'<h1>{E(title)}</h1><p class="meta">{" · ".join(meta)}</p><div class="links">{"".join(links)}</div>{note}{od}'
            f'<div class="toc"><a href="#first">The First Schedule</a><a href="#second">The Second Schedule</a></div>'
            f'<h2 id="first">The First Schedule</h2><div class="card"><ol class="s1">{"".join(lis)}</ol></div>'
            f'<h2 id="second">The Second Schedule</h2>{"".join(secs)}')
    desc = f"{title}: the ministries, departments and offices of the Government of India (First Schedule) and the subjects allotted to each (Second Schedule), in force from {fmt(fr['date'])}."
    ld = {"@context": "https://schema.org", "@type": "Legislation", "name": title, "legislationDate": fr["date"],
          "legislationJurisdiction": "India", "legislationType": "Rules"}
    html_ = page(rp, title, desc, [("Home", "https://www.orgpedia.in/"), ("Ministries as cells", rp), ("The Rules" if s == 0 else f"The Rules after #{s}", None)], body, "", ld)
    d = site / "rules" / str(s); d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(html_, encoding="utf-8"); n_rules += 1
  from . import ministry   # the ministry pages (§9b)
  n_min = ministry.build(tl, cells, states, base, cfg.get("base_date", "1961-01-14"), site, reissues)
  print(f"{n_min} ministry pages")
  tot = sum(p.stat().st_size for p in (site / "rules").rglob("*.html")) + sum(p.stat().st_size for p in (site / "amend").rglob("*.html"))
  print(f"{n_amend} amendment pages, {n_rules} Rules pages ({tot / 1e6:.0f} MB of HTML)")


if __name__ == "__main__":
  main(sys.argv[1] if len(sys.argv) > 1 else "src/cells.yml", sys.argv[2] if len(sys.argv) > 2 else "../../../site.cabsec-aob")
