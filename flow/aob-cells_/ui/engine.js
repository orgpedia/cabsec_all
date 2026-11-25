// The AoB units as cells: the engine (ui-requirements.md §2, §3, §6, §7).
// Deterministic: a fixed physics step, randomness from hashes, every event a function of time. Seekable: the run is
// simulated once, with a snapshot every second; going to time t restores the snapshot before it and steps forward.
(() => {
"use strict";

const SECTORS = {
  econ:   {label: "Economy & industry",      c: "#3D5A80", d: "#2F4663"},
  infra:  {label: "Infrastructure & energy", c: "#5B5788", d: "#46436A"},
  land:   {label: "Land, water & rural",     c: "#4A7766", d: "#395C4F"},
  social: {label: "Social & culture",        c: "#9C6B3F", d: "#795331"},
  secur:  {label: "Security & external",     c: "#93525A", d: "#723F46"},
  sci:    {label: "Science",                 c: "#3C7480", d: "#2E5A63"},
  gov:    {label: "Centre of government",    c: "#5A6472", d: "#464E58"},
};
const KIND_LABEL = {merged: "Merged", absorbed: "Absorbed", split: "Split", spun_off: "Spun off", moved: "Moved",
  born: "Created", ended: "Abolished", renamed: "Renamed", grew: "Grew", shrank: "Shrank"};
// how long each kind of event animates, in seconds (the Story plays them at this speed; the Full run a little faster)
const DUR = {merged: 1.9, absorbed: 1.7, split: 2.1, spun_off: 2.5, moved: 1.4, born: 1.3, ended: 1.5, renamed: 1.2,
  grew: 0.9, shrank: 0.9};
const DT = 1 / 60;

// ---------- small helpers ----------
function hash(...xs){ let h = 2166136261; for (const x of xs){ const s = String(x); for (let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } } return ((h >>> 0) % 100000) / 100000; }
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const ease = p => p < 0 ? 0 : p > 1 ? 1 : p * p * (3 - 2 * p);
function parseDate(s){ const [y, m, d] = s.split("-").map(Number); return Date.UTC(y, m - 1, d); }
function yearFrac(s){ const t = parseDate(s), y = +s.slice(0, 4); return (t - Date.UTC(y, 0, 1)) / (Date.UTC(y + 1, 0, 1) - Date.UTC(y, 0, 1)); }
function fmtDate(ms){ return new Date(ms).toLocaleDateString("en-GB", {day: "numeric", month: "long", year: "numeric", timeZone: "UTC"}); }

// ---------- the data ----------
class Data {
  constructor(tl){
    this.tl = tl;
    this.units = tl.units;
    this.frames = tl.frames;
    this.bySeries = new Map(tl.frames.map((f, i) => [f.series, i]));
    this.events = tl.events.map((e, i) => ({...e, i}));
    this.people = tl.people;
    this.reissues = tl.reissues || {};   // series -> what the page says at a re-issue (U24)
  }
  nameAt(uid, series){ const ns = this.units[uid].names; let n = ns[0]; for (const x of ns) if (x.from <= series) n = x; return n; }
  sector(uid){ return this.units[uid].sector || "gov"; }
  sizes(series){ return this.frames[this.bySeries.get(series)].sizes; }
  prevSeries(series){ const i = this.bySeries.get(series); return this.frames[Math.max(0, i - 1)].series; }
}

// ---------- the director: when everything happens, for one view ----------
// Full run: a steady pace per year, events at their date's place in the year. Story: faster years, and a hold with
// focus and a caption at each salient event (U8, U9).
function direct(data, view, hidden){
  hidden = hidden || new Set();
  const full = view === "full", isHidden = e => hidden.has(e.kind) || e.mute;   // mute: not this run's to show (a ministry's own run, U54)
  const fast = !!data.tl.center;   // a ministry's own run (U54): the rest goes by as fast as it can
  const yearDur = full ? 1.8 : 1.05, quietYear = fast ? 0.12 : full ? 0.5 : 0.35, INTRO = 1.6, END = 3.0;
  const frames = data.frames, y0 = +frames[0].date.slice(0, 4), y1 = +frames[frames.length - 1].date.slice(0, 4);
  const beats = [], times = [], focus = [], captions = [];
  const busy = {};
  let shift = 0, cursor = INTRO;
  const evBySeries = new Map();
  for (const e of data.events){ if (!evBySeries.has(e.series)) evBySeries.set(e.series, []); evBySeries.get(e.series).push(e); }
  times.push([0, parseDate(frames[0].date)]);
  // a year with no shown change passes quickly (the hidden ones still happen, quietly)
  const yd = {}, base = {}; let acc = INTRO;
  for (let y = y0; y <= y1; y++){
    const shown = data.events.some(e => +e.date.slice(0, 4) === y && !isHidden(e));
    yd[y] = shown ? yearDur : quietYear; base[y] = acc; acc += yd[y];
  }
  base[y1 + 1] = acc;
  const nat = (y, frac) => base[y] + frac * yd[y];
  for (let y = y0; y <= y1; y++){
    const yStart = Math.max(nat(y, 0) + shift, cursor);
    shift = yStart - nat(y, 0);
    if (y > y0) times.push([yStart, Date.UTC(y, 0, 1)]);
    for (const f of frames){
      if (+f.date.slice(0, 4) !== y || f === frames[0]) continue;
      let t = Math.max(nat(y, yearFrac(f.date)) + shift, cursor);
      shift = t - nat(y, yearFrac(f.date));
      times.push([t, parseDate(f.date)]);
      const evs = (evBySeries.get(f.series) || []).map(e => ({...e}));
      const beat = {series: f.series, date: f.date, t, events: evs};
      for (const e of evs) e.beatT = t;   // the frame's time: the safety net waits for its events
      const r = data.reissues[f.series];   // a re-issue, or the Rules beginning: one caption first, then its changes (U24)
      const note = r && (r.text || r);
      if (note) captions.push({t0: t, t1: t + 3.4, note, label: r.label || "Re-issue", date: f.date});
      let stagger = note ? 0.6 : 0;
      const sal = full ? [] : evs.filter(e => e.salient && !isHidden(e));
      for (const e of evs.filter(e => !sal.includes(e))){   // the quick ones; a hidden kind plays quietly and faster
        const ids = [...e.from, ...e.to];
        e.quiet = isHidden(e);
        let s = t + stagger; for (const u of ids) s = Math.max(s, busy[u] || 0);
        e.t0 = s; e.dur = DUR[e.kind] * (e.quiet ? (fast ? 0.22 : 0.55) : full ? 0.85 : 0.8); stagger += e.quiet ? (fast ? 0.005 : 0.04) : 0.12;
        for (const u of ids) busy[u] = Math.max(busy[u] || 0, e.quiet ? s + 0.1 : s + e.dur);   // a hidden change holds up no one
      }
      let hold = note ? t + 3.4 : t + (sal.length ? 0.2 : 0);
      for (const e of sal){                                   // the Story's salient events, one after the other
        const ids = [...e.from, ...e.to];
        let s = hold; for (const u of ids) s = Math.max(s, (busy[u] || 0) - 1.1);
        const fs = s, a0 = fs + 1.1, a1 = a0 + DUR[e.kind], fe = a1 + 1.5;
        e.t0 = a0; e.dur = DUR[e.kind];
        focus.push({t0: fs, t1: fe, ids, sector: data.sector((e.to[0] || e.from[0])), e});
        captions.push({t0: fs, t1: fe, e});
        for (const u of ids) busy[u] = a1;
        hold = fe;
      }
      if (sal.length || note){ times.push([t + 0.01, parseDate(f.date)], [hold, parseDate(f.date)]); cursor = hold; }
      beats.push(beat);
    }
  }
  const lastT = Math.max(base[y1 + 1] + shift, cursor);
  let tEnd = lastT;
  for (const b of beats) for (const e of b.events) tEnd = Math.max(tEnd, e.t0 + e.dur + 0.5);
  const endMs = data.tl.endDate ? parseDate(data.tl.endDate) : Date.UTC(y1, 11, 31);   // a past term ends the day before the next PM
  times.push([tEnd, endMs]);
  const T = tEnd + END;
  times.push([T, endMs]);
  // keep the date mapping monotonic
  for (let i = 1; i < times.length; i++) if (times[i][0] < times[i - 1][0]) times[i][0] = times[i - 1][0];
  const all = beats.flatMap(b => b.events).sort((a, b) => a.t0 - b.t0);
  return {view, T, INTRO, beats, events: all, times, focus, captions, yearDur, hidden};
}

function dateAt(dir, t){
  const ts = dir.times;
  if (t <= ts[0][0]) return ts[0][1];
  for (let i = 1; i < ts.length; i++) if (t <= ts[i][0]){
    const [a, da] = ts[i - 1], [b, db] = ts[i];
    return b > a ? da + (db - da) * (t - a) / (b - a) : db;
  }
  return ts[ts.length - 1][1];
}

// ---------- the simulation ----------
class Sim {
  constructor(data, dir, W, H){
    this.data = data; this.dir = dir; this.W = W; this.H = H;
    // a ministry's own run (U54): its line held in the middle (U67), its kin drawn in
    this.line = data.tl.center ? [].concat(data.tl.center) : null; this.center = this.line ? new Set(this.line) : null;
    this.kin = data.tl.kin ? new Set(data.tl.kin) : null;
    this.CX = W / 2; this.CY = H / 2 + 6;
    // cells sized for the run's largest frame, so the government fits the stage in every year (864 subjects in
    // 1961, 1,846 at most)
    const area = W * H * 0.40, total = data.tl.scaleTotal || Math.max(...data.frames.map(f => Object.values(f.sizes).reduce((a, b) => a + b, 0)));   // a term uses the whole run's scale
    this.K = Math.sqrt(area / (Math.PI * Math.max(total, 1)));
    this.RMIN = Math.max(7, this.K * 1.25); this.PAD = 13;
    this.anchor = {};
    const order = ["econ", "infra", "sci", "land", "social", "gov", "secur"];
    order.forEach((s, i) => { const a = -Math.PI / 2 + i * 2 * Math.PI / order.length;
      this.anchor[s] = {x: this.CX + Math.cos(a) * W * 0.28, y: this.CY + Math.sin(a) * H * 0.27}; });
    this.cues = null;  // sound cues, collected only while playing live
    // each unit's event windows, from its frame's time to its last event's end: while one is open, the safety net
    // leaves the unit's cell to the event
    this.windows = new Map();
    for (const e of dir.events) for (const u of [...e.from, ...e.to]){
      if (!this.windows.has(u)) this.windows.set(u, []);
      this.windows.get(u).push([e.beatT, e.t0 + e.dur + 0.7]);
    }
  }
  pending(uid, t){ const w = this.windows.get(uid); return !!w && w.some(([b, e]) => b <= t + 1e-9 && t < e); }
  rad(s){ return Math.max(this.RMIN, this.K * Math.sqrt(Math.max(0, s))); }

  initial(){
    const f = this.data.frames[0], st = {t: 0, bi: -1, cells: {}, fx: [], mem: {}, gone: {}, cam: {x: this.CX, y: this.CY, s: 1}, veil: 0};
    for (const uid of Object.keys(f.sizes).sort()){
      const a = this.anchor[this.data.sector(uid)];
      const c = this.cell(uid, f.sizes[uid], f.series, a.x + (hash(uid, 1) - .5) * 160, a.y + (hash(uid, 2) - .5) * 110);
      c.r = c.rt; st.cells[uid] = c;
    }
    for (let i = 0; i < 500; i++) this.physics(st, true);
    for (const c of Object.values(st.cells)){ c.r = 0; c.rv = 0; c.hold = c.rt; c.rt0 = c.rt; c.rt = 0; c.vx = c.vy = 0; }
    return st;
  }
  cell(uid, size, series, x, y){
    const n = this.data.nameAt(uid, series);
    return {id: uid, x, y, vx: 0, vy: 0, r: 0, rt: this.rad(size), rv: 0, size, sector: this.data.sector(uid),
      phase: hash(uid) * 6.283, pin: null, ghost: [], hold: 0, label: n.short, kind: n.kind, morph: null, hideLabel: false};
  }

  // one fixed step
  step(st){
    const t0 = st.t, t1 = t0 + DT;
    if (t0 < this.dir.INTRO + 1){   // the cells pop in from the centre outwards
      for (const c of Object.values(st.cells)) if (c.rt0 && t1 >= Math.hypot(c.x - this.CX, c.y - this.CY) / 900){ c.rt = c.rt0; c.rt0 = 0; c.hold = 0; c.rv = 2; }
    }
    // frames: small changes resize at the frame's time; events run in their windows
    for (const b of this.dir.beats){
      if (t0 < b.t && t1 >= b.t){
        const sz = this.data.sizes(b.series), busyIds = new Set(b.events.flatMap(e => [...e.from, ...e.to]));
        for (const c of Object.values(st.cells)) if (!busyIds.has(c.id) && sz[c.id] != null && sz[c.id] !== c.size){ c.size = sz[c.id]; c.rt = this.rad(c.size); }
      }
    }
    for (const e of this.dir.events){
      if (t1 < e.t0 || t0 > e.t0 + e.dur + 0.6) continue;
      this.run(st, e, Math.max(0, t1 - e.t0), t0 - e.t0);
    }
    this.reconcile(st, t1);
    this.physics(st, false);
    this.effects(st);
    this.camera(st, t1);
    st.t = t1;
  }

  cue(name){ if (this.cues) this.cues.push(name); }

  // the safety net: at every frame the stage holds the frame's units, whatever the events say. A cell whose unit is
  // not in the frame fades out; a unit with no cell fades in; while an event on the unit plays, it is left alone
  reconcile(st, t1){
    const beats = this.dir.beats;
    while (st.bi + 1 < beats.length && beats[st.bi + 1].t <= t1) st.bi++;
    if (t1 < this.dir.INTRO) return;
    const series = st.bi < 0 ? this.data.frames[0].series : beats[st.bi].series, exp = this.data.sizes(series);
    for (const c of Object.values(st.cells)){
      if (exp[c.id] == null && !c.vanish && !this.pending(c.id, t1)){ c.vanish = true; c.rt = 0; c.hideLabel = true; c.pin = null; c.ghost = []; }
      if (c.vanish && c.rt === 0 && c.r < 0.6) delete st.cells[c.id];
    }
    for (const id in exp){
      if (st.cells[id] || this.pending(id, t1)) continue;
      const a = this.anchor[this.data.sector(id)];
      const c = this.cell(id, exp[id], series, a.x + (hash(id, "rx") - .5) * 60, a.y + (hash(id, "ry") - .5) * 60);
      c.r = 0; c.rv = 1.5; st.cells[id] = c;
    }
  }

  // ---------- the event animations (U24 table §7) ----------
  run(st, e, tau, prev){
    const cue = e.quiet ? () => {} : n => this.cue(n), ring = e.quiet ? () => {} : (...a) => this.ring(...a);
    const cr = x => prev < x && tau >= x;
    const C = id => st.cells[id];
    const sz = this.data.sizes(e.series), m = st.mem[e.i] || (st.mem[e.i] = {}), D = e.dur, k = DUR[e.kind] / D;
    const T = x => x / k;   // the script's times, scaled to this event's duration
    const end = tau >= D;
    switch (e.kind){
      case "merged": {
        const srcIds = e.from, newId = e.to[0];
        if (cr(0)){
          const srcs = srcIds.map(C).filter(Boolean); if (!srcs.length) return;
          const big = srcs.reduce((a, b) => a.size >= b.size ? a : b);
          m.big = big.id; m.small = srcs.filter(s => s !== big).map(s => s.id);
          for (const s of srcs) for (const o of srcs) if (s !== o && !s.ghost.includes(o.id)) s.ghost.push(o.id);
          m.bx = big.x; m.by = big.y;
        }
        if (!m.big) return;
        const big = C(m.big) || C(newId);
        if (!big) return;
        if (tau < T(1.4)){
          big.pin = {x: m.bx, y: m.by, k: .05};
          for (const sid of m.small){ const s = C(sid); if (!s) continue;
            const f = tau < T(.9) ? .5 : 1; s.pin = {x: s.x + (big.x - s.x) * f, y: s.y + (big.y - s.y) * f, k: tau < T(.9) ? .035 : .07}; }
        }
        if (cr(T(1.4))){
          cue("squelch");
          for (const sid of m.small){ const s = C(sid); if (s){ s.rt = 0; s.ghost.push(newId); s.hideLabel = true; } }
          this.rekey(st, big, newId, e.series);
          big.size = sz[newId] ?? big.size; big.rt = this.rad(big.size); big.rv += 4;
          ring(st, big.id, SECTORS[big.sector].c, 26, .9);
        }
        if (cr(T(1.85)) || (end && !m.done)){
          m.done = true;
          for (const sid of m.small) delete st.cells[sid];
          const b = C(newId); if (b){ b.pin = null; b.ghost = []; }
        }
        break;
      }
      case "absorbed": {
        const s0 = e.from[0], into = e.to[0];
        const s = C(s0), b = C(into);
        if (cr(0) && s && b){ s.ghost.push(into); b.ghost.push(s0); }
        if (s && b && tau < T(1.3)) s.pin = {x: s.x + (b.x - s.x) * (tau < T(.7) ? .4 : 1), y: s.y + (b.y - s.y) * (tau < T(.7) ? .4 : 1), k: tau < T(.7) ? .04 : .09};
        if (cr(T(1.0)) && s){ cue("squelch"); s.rt = 0; s.hideLabel = true; if (b){ b.size = sz[into] ?? b.size; b.rt = this.rad(b.size); b.rv += 3; } }
        if ((cr(T(1.5)) || (end && !m.done))){ m.done = true; delete st.cells[s0]; if (b){ b.ghost = b.ghost.filter(x => x !== s0); b.pin = null; } }
        break;
      }
      case "split": {
        const p0 = e.from[0];
        if (cr(0)){
          const p = C(p0); if (!p) return;
          const ang = -0.35 + hash(e.key, "a") * 0.7;
          m.cx = p.x; m.cy = p.y; m.ang = ang; m.ids = e.to.slice();
          const tot = e.to.reduce((a, id) => a + (sz[id] || 1), 0);
          for (const id of e.to){
            const kc = this.cell(id, sz[id] || 1, e.series, p.x, p.y);
            kc.r = p.r * Math.sqrt((sz[id] || 1) / tot) * 1.15; kc.ghost = e.to.filter(x => x !== id);
            st.cells[id] = kc;
          }
          delete st.cells[p0];
        }
        if (!m.ids) return;
        const kids = m.ids.map(C).filter(Boolean), n = kids.length;
        const rs = kids.map(kc => kc.rt), sum = rs.reduce((a, b) => a + b, 0);
        let sep;
        if (tau < T(.85)) sep = .32 * ease(tau / T(.85));
        else if (tau < T(1.27)) sep = .32 + .30 * ease((tau - T(.85)) / T(.42));
        else sep = .62 + .12 * ease((tau - T(1.27)) / T(.2));
        if (cr(T(.85))) kids.forEach(kc => kc.rv += 1.5);
        if (cr(T(1.27))){ cue("snap"); }
        if (cr(T(1.45))) kids.forEach(kc => kc.rv += 3);
        if (tau < T(2.0)){
          kids.forEach((kc, i) => {
            let ox, oy;
            if (n === 2){ const d = sep * sum * 2, w = i === 0 ? -rs[1] / sum : rs[0] / sum; ox = Math.cos(m.ang) * d * w; oy = Math.sin(m.ang) * d * w; }
            else { const a = m.ang + i * 2 * Math.PI / n, d = sep * sum * 0.9; ox = Math.cos(a) * d; oy = Math.sin(a) * d; }
            kc.pin = {x: m.cx + ox, y: m.cy + oy, k: .2};
          });
        }
        if (cr(T(2.0)) || (end && !m.done)){ m.done = true; kids.forEach(kc => { kc.pin = null; kc.ghost = []; }); }
        break;
      }
      case "spun_off": {
        const p0 = e.from[0], id = e.to[0];
        if (cr(0)){
          const p = C(p0); if (!p) return;
          let dx = p.x - this.CX, dy = p.y - this.CY; const dl = Math.hypot(dx, dy) || 1; dx /= dl; dy /= dl;
          const rot = 0.6 * (hash(e.key) > .5 ? 1 : -1);
          m.ux = dx * Math.cos(rot) - dy * Math.sin(rot); m.uy = dx * Math.sin(rot) + dy * Math.cos(rot);
          m.px = p.x; m.py = p.y;
          const kc = this.cell(id, sz[id] || 1, e.series, p.x + m.ux * p.r * .5, p.y + m.uy * p.r * .5);
          kc.r = 3; kc.rt = this.rad(kc.size) * .7; kc.ghost = [p0]; kc.hideLabel = true; p.ghost.push(id);
          st.cells[id] = kc;
        }
        const p = C(p0), kc = C(id);
        if (!p || !kc || m.ux == null) return;
        const full = this.rad(kc.size);
        if (tau < T(1.1)){ const q = tau / T(1.1), d = .45 + .55 * q; kc.rt = full * (.7 + .3 * q);
          p.pin = {x: m.px, y: m.py, k: .08}; kc.pin = {x: p.x + m.ux * p.r * d, y: p.y + m.uy * p.r * d, k: .25}; }
        if (cr(T(1.1))){ p.size = sz[p0] ?? p.size; p.rt = this.rad(p.size); }
        if (tau >= T(1.1) && tau < T(1.8)) kc.pin = {x: p.x + m.ux * (p.r + kc.r * .55), y: p.y + m.uy * (p.r + kc.r * .55), k: .15};
        if (cr(T(1.8))){ cue("snap"); kc.hideLabel = false; kc.morph = {to: kc.label, t0: st.t, dur: .5}; kc.rv += 3; p.rv += 2; }
        if (tau >= T(1.8) && tau < T(2.4)) kc.pin = {x: p.x + m.ux * (p.r + kc.r + 20), y: p.y + m.uy * (p.r + kc.r + 20), k: .2};
        if (cr(T(2.4)) || (end && !m.done)){ m.done = true; kc.pin = null; p.pin = null; kc.ghost = []; p.ghost = p.ghost.filter(x => x !== id); kc.hideLabel = false; }
        break;
      }
      case "moved": {
        const a = C(e.from[0]), b = C(e.to[0]);
        if (cr(0) && a && b){ cue("pop"); st.fx.push({kind: "flow", a: a.id, b: b.id, t0: st.t, life: T(1.0), color: SECTORS[a.sector].c, r: Math.max(5, this.rad(e.moved[0] || 3) * .45)});
          a.size = sz[a.id] ?? a.size; a.rt = this.rad(a.size); }
        if (cr(T(1.0)) && b){ b.size = sz[b.id] ?? b.size; b.rt = this.rad(b.size); b.rv += 3; }
        break;
      }
      case "born": {
        const id = e.to[0];
        if (cr(0)){
          const sec = this.data.sector(id), g = st.gone[e.series + ":" + sec], a = this.anchor[sec];
          const x = g ? g.x : a.x + (hash(id, "x") - .5) * 60, y = g ? g.y : a.y + (hash(id, "y") - .5) * 60;
          const c = this.cell(id, sz[id] || 1, e.series, x, y); c.rv = 5; c.pin = {x, y, k: .3};
          st.cells[id] = c; cue("born"); ring(st, id, "#3D5A80", 34, 1.1);
        }
        if (cr(T(.25)) && C(id)) ring(st, id, "#94a3b8", 52, 1.2);
        if ((cr(T(1.2)) || end) && C(id)) C(id).pin = null;
        break;
      }
      case "ended": {
        const c = C(e.from[0]);
        if (!c) return;
        if (cr(0)){ m.x = c.x; m.y = c.y; }
        if (tau < T(.95)){ c.pin = {x: m.x, y: m.y, k: .2}; for (let i = 0; i < 6; i++) if (cr(T(.12 * i))) c.rv += (i % 2 ? -2.2 : 2.2); }
        if (cr(T(.75))) c.rt = c.r * 1.18;
        if (cr(T(.95))){ cue("burst"); this.drops(st, c, 16, e.key); ring(st, c.id, SECTORS[c.sector].d, 30, .6);
          c.rt = 0; c.r *= .4; c.hideLabel = true; st.gone[e.series + ":" + c.sector] = {x: c.x, y: c.y}; }
        if (cr(T(1.4)) || (end && !m.done)){ m.done = true; delete st.cells[c.id]; }
        break;
      }
      case "renamed": {
        const c = C(e.to[0]); if (!c) return;
        if (cr(0)){
          const n = this.data.nameAt(c.id, e.series); c.label = n.short; c.kind = n.kind;
          if (!e.quiet) c.morph = {to: n.short, t0: st.t, dur: T(1.1)}; ring(st, c.id, "#3D5A80", 22, 1.0); cue("chime");
          if (sz[c.id] != null && sz[c.id] !== c.size){ c.size = sz[c.id]; c.rt = this.rad(c.size); c.rv += 3; }
        }
        break;
      }
      case "grew": case "shrank": {
        const c = C(e.to[0]); if (!c) return;
        if (cr(0)){ c.size = sz[c.id] ?? c.size; c.rt = this.rad(c.size); c.rv += e.kind === "grew" ? 4 : -2; cue("grow"); }
        break;
      }
    }
  }
  rekey(st, c, newId, series){
    delete st.cells[c.id]; const old = c.id; c.id = newId; st.cells[newId] = c;
    for (const o of Object.values(st.cells)) o.ghost = o.ghost.map(g => g === old ? newId : g);
    const n = this.data.nameAt(newId, series); c.label = n.short; c.kind = n.kind; c.sector = this.data.sector(newId);
    c.morph = {to: n.short, t0: st.t, dur: .7};
  }
  ring(st, id, color, grow, life){ st.fx.push({kind: "ring", id, color, grow, t0: st.t, life}); }
  drops(st, c, n, seed){
    for (let i = 0; i < n; i++){
      const a = i / n * 6.283 + hash(seed, i, "a") * .5, v = 90 + hash(seed, i, "v") * 130;
      st.fx.push({kind: "drop", x: c.x + Math.cos(a) * c.r * .6, y: c.y + Math.sin(a) * c.r * .6, vx: Math.cos(a) * v, vy: Math.sin(a) * v,
        r: 2.5 + hash(seed, i, "r") * 4, t0: st.t, life: .7 + hash(seed, i, "l") * .5, color: SECTORS[c.sector].c});
    }
  }

  physics(st, settling){
    const arr = Object.values(st.cells), W = this.W, H = this.H, t = st.t;
    for (const c of arr){
      c.rv += (c.rt - c.r) * 0.085; c.rv *= 0.80; c.r += c.rv; if (c.r < 0){ c.r = 0; c.rv = 0; }
      if (settling) c.r = c.rt;
      if (c.pin){ c.x += (c.pin.x - c.x) * c.pin.k; c.y += (c.pin.y - c.y) * c.pin.k; c.vx = c.vy = 0; }
      else if (this.center && this.center.has(c.id)){   // a ministry's own run: it keeps the middle
        c.vx += (this.CX - c.x) * 0.03; c.vy += (this.CY - c.y) * 0.03; c.vx *= 0.8; c.vy *= 0.8; c.x += c.vx; c.y += c.vy;
      }
      else {
        const a = this.kin && this.kin.has(c.id) ? {x: this.CX, y: this.CY} : this.anchor[c.sector];
        const k = this.kin && !this.kin.has(c.id) ? 0.0010 : 0.0016;
        c.vx += (a.x - c.x) * k + (this.CX - c.x) * 0.0012;
        c.vy += (a.y - c.y) * k + (this.CY - c.y) * 0.0018;
        c.vx += Math.sin(t * 0.6 + c.phase) * 0.012; c.vy += Math.cos(t * 0.5 + c.phase) * 0.012;
        c.vx *= 0.86; c.vy *= 0.86; c.x += c.vx; c.y += c.vy;
      }
    }
    for (let it = 0; it < 3; it++){
      for (let i = 0; i < arr.length; i++) for (let j = i + 1; j < arr.length; j++){
        const a = arr[i], b = arr[j];
        if (a.ghost.includes(b.id) || b.ghost.includes(a.id)) continue;
        const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 0.01;
        const min = Math.max(a.r, a.rt * 0.6, a.hold) + Math.max(b.r, b.rt * 0.6, b.hold) + this.PAD;
        if (d < min){
          const o = (min - d) / d * 0.5;
          const wa = a.pin ? 0 : (b.pin ? 1 : 0.5), wb = b.pin ? 0 : (a.pin ? 1 : 0.5);
          a.x -= dx * o * wa; a.y -= dy * o * wa; b.x += dx * o * wb; b.y += dy * o * wb;
        }
      }
    }
    for (const c of arr){ const r = Math.max(c.r, c.hold); c.x = clamp(c.x, r + 6, W - r - 6); c.y = clamp(c.y, r + 6, H - r - 6); }
  }

  effects(st){
    for (const f of st.fx) if (f.kind === "drop"){ f.x += f.vx * DT; f.y += f.vy * DT; f.vx *= .96; f.vy = f.vy * .96 + 30 * DT; }
    st.fx = st.fx.filter(f => st.t - f.t0 < f.life);
  }

  focusAt(t){ for (const f of this.dir.focus) if (t >= f.t0 && t < f.t1) return f; return null; }
  camera(st, t){
    const f = this.focusAt(t);
    let tx = this.CX, ty = this.CY, ts = 1;
    const mc = this.line && [...this.line].reverse().map(id => st.cells[id]).find(Boolean);   // the line's latest unit on stage
    if (mc && !f){ tx = this.CX + (mc.x - this.CX) * 0.7; ty = this.CY + (mc.y - this.CY) * 0.7; ts = 1.12; }   // the camera stays with it
    if (f){
      const cs = f.ids.map(id => st.cells[id]).filter(Boolean);
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      const add = (x, y, r) => { x0 = Math.min(x0, x - r); x1 = Math.max(x1, x + r); y0 = Math.min(y0, y - r); y1 = Math.max(y1, y + r); };
      for (const c of cs) add(c.x, c.y, Math.max(c.r, c.rt) + 40);
      if (!cs.length){ const g = st.gone[f.e.series + ":" + f.sector] || this.anchor[f.sector]; add(g.x, g.y, 90); }
      ts = clamp(Math.min(this.W / (x1 - x0), this.H / (y1 - y0)) * 0.5, 1, (typeof window !== "undefined" && window.CELLS_MAXZOOM) || 1.75);   // the video zooms in less
      tx = (x0 + x1) / 2; ty = (y0 + y1) / 2 + 14 / ts;
    }
    st.cam.x += (tx - st.cam.x) * 0.045; st.cam.y += (ty - st.cam.y) * 0.045; st.cam.s += (ts - st.cam.s) * 0.045;
    st.veil += ((f ? 0.62 : 0) - st.veil) * 0.06;
    st.focusIds = f ? f.ids : null;
  }
}

// ---------- the player: snapshots, seeking, playing ----------
class Player {
  constructor(data, view, W, H, hidden){
    this.data = data; this.W = W; this.H = H; this.setView(view, hidden);
  }
  setView(view, hidden){
    this.view = view; this.hidden = hidden || new Set();
    this.dir = direct(this.data, view, this.hidden);
    this.sim = new Sim(this.data, this.dir, this.W, this.H);
    const st = this.sim.initial();
    this.snaps = [structuredClone(st)];
    let next = 1;
    while (st.t < this.dir.T){ this.sim.step(st); if (st.t >= next){ this.snaps.push(structuredClone(st)); next += 1; } }
    this.st = structuredClone(this.snaps[0]);
  }
  seek(t){
    t = clamp(t, 0, this.dir.T);
    if (!(this.st.t <= t && t - this.st.t < 1.5)){
      const i = clamp(Math.floor(t), 0, this.snaps.length - 1);
      this.st = structuredClone(this.snaps[i]);
    }
    this.sim.cues = null;
    while (this.st.t + DT <= t + 1e-9) this.sim.step(this.st);
  }
  advance(dt){   // play forward live, with the sound cues
    const cues = []; this.sim.cues = cues;
    const target = Math.min(this.dir.T, this.st.t + dt);
    while (this.st.t + DT <= target + 1e-9) this.sim.step(this.st);
    this.sim.cues = null; return cues;
  }
}

// ---------- drawing (SVG) ----------
const NS = "http://www.w3.org/2000/svg";
function svgEl(tag, attrs, parent){ const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }

const GREY = {c: "#dfe2e6", d: "#c9cdd3"};   // the cells a ministry's own run leaves out

class Renderer {
  constructor(svg, W, H){
    this.svg = svg; this.W = W; this.H = H;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.innerHTML = `<defs>
      <filter id="goo" filterUnits="userSpaceOnUse" x="-600" y="-600" width="${W + 1200}" height="${H + 1200}" color-interpolation-filters="sRGB">
        <feGaussianBlur in="SourceGraphic" stdDeviation="4.5" result="b"/>
        <feColorMatrix in="b" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 24 -11" result="g"/>
        <feComposite in="SourceGraphic" in2="g" operator="atop"/></filter>
      <radialGradient id="shine" cx="35%" cy="30%" r="70%"><stop offset="0" stop-color="#fff" stop-opacity=".28"/><stop offset=".45" stop-color="#fff" stop-opacity=".05"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    </defs><g id="cam"><g filter="url(#goo)"><g id="mem"></g><g id="fill"></g></g><g id="deco"></g><g id="labels"></g>
      <rect id="veil" x="-4000" y="-4000" width="9000" height="9000" fill="#f8fafc" opacity="0"/>
      <g filter="url(#goo)"><g id="memF"></g><g id="fillF"></g></g><g id="decoF"></g><g id="fx"></g><g id="labelsF"></g></g>`;
    this.g = id => svg.querySelector("#" + id);
    for (const id of ["labels", "labelsF"]) this.g(id).setAttribute("font-family", "ui-sans-serif,system-ui,sans-serif");
    this.els = new Map(); this.fxEls = []; this.highlight = null;   // a Set of ids picked by search
  }
  draw(st){
    const s = st.cam.s, tx = this.W / 2 - st.cam.x * s, ty = this.H / 2 - st.cam.y * s;
    this.g("cam").setAttribute("transform", `translate(${tx.toFixed(2)} ${ty.toFixed(2)}) scale(${s.toFixed(4)})`);
    const hl = this.highlight && this.highlight.size ? this.highlight : null;
    this.g("veil").setAttribute("opacity", Math.max(st.veil, hl && !st.focusIds ? 0.55 : 0).toFixed(3));
    const seen = new Set();
    for (const c of Object.values(st.cells)){
      seen.add(c.id);
      let E = this.els.get(c.id);
      if (!E){
        const col = SECTORS[c.sector] || SECTORS.gov;
        E = {mem: svgEl("circle", {fill: col.d}), fill: svgEl("circle", {fill: col.c}), nuc: svgEl("circle", {fill: col.d, "fill-opacity": .22}),
             shine: svgEl("circle", {fill: "url(#shine)"}), text: svgEl("text", {"text-anchor": "middle", "font-weight": 600}), front: null, key: "", sector: c.sector};
        this.els.set(c.id, E);
      }
      const grey = !!this.keep && !this.keep.has(c.id), ck = c.sector + (grey ? "-" : "");   // a ministry's own run: only its kin in colour
      if (E.sector !== ck){ const col = grey ? GREY : SECTORS[c.sector] || SECTORS.gov; E.mem.setAttribute("fill", col.d); E.fill.setAttribute("fill", col.c); E.nuc.setAttribute("fill", col.d); E.sector = ck; E.key = ""; }
      const front = (!!st.focusIds && st.focusIds.includes(c.id)) || (!st.focusIds && !!hl && hl.has(c.id));
      if (E.front !== front){
        const f = front ? "F" : "";
        this.g("mem" + f).appendChild(E.mem); this.g("fill" + f).appendChild(E.fill);
        this.g("deco" + f).appendChild(E.nuc); this.g("deco" + f).appendChild(E.shine); this.g("labels" + f).appendChild(E.text);
        E.front = front; E.key = "";
      }
      const br = c.r * (1 + 0.018 * Math.sin(st.t * 1.6 + c.phase)), vis = br > 0.3;
      const set = (el, cx, cy, r) => { el.setAttribute("cx", cx.toFixed(1)); el.setAttribute("cy", cy.toFixed(1)); el.setAttribute("r", vis ? r.toFixed(2) : 0); };
      set(E.mem, c.x, c.y, br + 2); set(E.fill, c.x, c.y, br);
      set(E.nuc, c.x + br * .12, c.y + br * .16, br * .3); set(E.shine, c.x, c.y, br);
      // label
      let text = c.hideLabel ? "" : c.label;
      if (c.morph && !c.hideLabel){
        const p = (st.t - c.morph.t0) / c.morph.dur;
        if (p < 1){ const to = c.morph.to, n = Math.round(to.length * Math.max(0, p)), az = "abcdefghijklmnopqrstuvwxyz";
          text = to.slice(0, n) + [...to.slice(n, Math.min(to.length, n + 5))].map((ch, i) => ch === " " ? " " : az[Math.floor(hash(c.id, Math.floor(st.t * 20), i) * 26)]).join(""); }
      }
      const lr = Math.round(c.r / 3) * 3;
      const key = text + "|" + lr + "|" + front + "|" + (front ? Math.round(s * 20) : 0);
      if (E.key !== key){ E.key = key; E.L = layoutLabel(text, lr, front, s); E.text.textContent = "";
        if (E.L){ E.L.lines.forEach((ln, i) => { const t = svgEl("tspan", {x: 0, dy: i ? "1.1em" : 0}, E.text); t.textContent = ln; });
          E.text.setAttribute("font-size", E.L.fs.toFixed(2)); E.text.setAttribute("fill", E.L.out ? "#111827" : (this.keep && !this.keep.has(c.id) ? "#6b7280" : "#fff"));
          E.text.setAttribute("stroke", E.L.out ? "#fff" : "none"); E.text.setAttribute("stroke-width", E.L.out ? 3.5 / s : 0); E.text.setAttribute("paint-order", "stroke"); } }
      if (E.L){ const h = E.L.fs * 1.1 * E.L.lines.length, y = E.L.out ? c.y + br + 6 + E.L.fs : c.y - h / 2 + E.L.fs * .82;
        E.text.setAttribute("transform", `translate(${c.x.toFixed(1)} ${y.toFixed(1)})`); E.text.setAttribute("opacity", vis && br > 6 ? 1 : 0); }
    }
    for (const [id, E] of this.els) if (!seen.has(id)){ [E.mem, E.fill, E.nuc, E.shine, E.text].forEach(x => x.remove()); this.els.delete(id); }
    // effects
    this.fxEls.forEach(x => x.remove()); this.fxEls = [];
    const fxg = this.g("fx");
    for (const f of st.fx){
      const p = (st.t - f.t0) / f.life;
      if (f.kind === "drop") this.fxEls.push(svgEl("circle", {cx: f.x, cy: f.y, r: Math.max(0, f.r * (1 - p)), fill: f.color, opacity: 1 - p * p}, fxg));
      else if (f.kind === "ring"){ const c = st.cells[f.id]; if (!c) continue; const e = 1 - Math.pow(1 - p, 3);
        this.fxEls.push(svgEl("circle", {cx: c.x, cy: c.y, r: c.r + f.grow * e, fill: "none", stroke: f.color, "stroke-width": 2.5, opacity: (1 - p) * .9}, fxg)); }
      else if (f.kind === "flow"){ const a = st.cells[f.a], b = st.cells[f.b]; if (!a || !b) continue; const q = ease(p);
        this.fxEls.push(svgEl("circle", {cx: a.x + (b.x - a.x) * q, cy: a.y + (b.y - a.y) * q, r: f.r * (1 - .3 * Math.abs(q - .5)), fill: f.color, opacity: .95}, fxg)); }
    }
  }
  toScreen(st, x, y){ const s = st.cam.s; return [(x - st.cam.x) * s + this.W / 2, (y - st.cam.y) * s + this.H / 2]; }
}

function wrapLines(text, maxChars, maxLines){
  const words = text.split(" "), lines = []; let cur = "";
  for (const w of words){ if ((cur + " " + w).trim().length <= maxChars) cur = (cur + " " + w).trim(); else { if (cur) lines.push(cur); cur = w; } }
  if (cur) lines.push(cur);
  return lines.length <= maxLines && lines.every(l => l.length <= maxChars + 2) ? lines : null;
}
function layoutLabel(text, r, front, camS){
  if (!text) return null;
  text = text.replace(/ and /g, " & ");
  let lines = null, fs = Math.max(9, Math.min(15, r * 0.24));
  if (r >= 21) for (let f = fs; f >= 8 && !lines; f -= 0.5){ fs = f; lines = wrapLines(text, Math.floor(1.8 * r / (f * 0.56)), r > 32 ? 4 : 3); }
  if (!lines && front) return {out: true, fs: 13 / camS, lines: wrapLines(text, 24, 4) || [text]};
  return lines ? {out: false, fs, lines} : null;
}

// ---------- sound ----------
class Sound {
  constructor(){ this.on = false; this.ctx = null; }
  toggle(){ this.on = !this.on; if (this.on && !this.ctx){ try { this.ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e){ this.on = false; } }
    if (this.ctx && this.ctx.state === "suspended") this.ctx.resume(); if (this.on) this.play("pop"); return this.on; }
  tone(type, f0, f1, dur, vol, at = 0){ const c = this.ctx, t = c.currentTime + at, o = c.createOscillator(), g = c.createGain();
    o.type = type; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f1, t + dur);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + 0.012); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(c.destination); o.start(t); o.stop(t + dur + 0.02); }
  noise(dur, f, vol){ const c = this.ctx, n = c.sampleRate * dur, b = c.createBuffer(1, n, c.sampleRate), d = b.getChannelData(0);
    for (let i = 0; i < n; i++) d[i] = (hash(i) * 2 - 1) * (1 - i / n);
    const s = c.createBufferSource(), fl = c.createBiquadFilter(), g = c.createGain(); s.buffer = b; fl.type = "bandpass"; fl.frequency.value = f; fl.Q.value = 1.2; g.gain.value = vol;
    s.connect(fl).connect(g).connect(c.destination); s.start(); }
  play(name){
    if (!this.on || !this.ctx) return;
    ({pop: () => this.tone("sine", 700, 160, .13, .3), snap: () => { this.tone("sine", 950, 260, .1, .28); this.noise(.05, 3000, .14); },
      squelch: () => { this.tone("triangle", 240, 70, .32, .26); this.noise(.25, 500, .18); }, burst: () => { this.noise(.35, 1400, .32); this.tone("sine", 180, 50, .25, .28); },
      born: () => { this.tone("sine", 320, 980, .16, .26); this.tone("sine", 980, 1320, .12, .1, .14); },
      chime: () => { this.tone("sine", 880, 880, .25, .12); this.tone("sine", 1320, 1320, .3, .08, .08); }, grow: () => this.tone("sine", 200, 420, .3, .12)}[name] || (() => {}))();
  }
}

window.Cells = {SECTORS, KIND_LABEL, Data, direct, dateAt, Player, Renderer, Sound, fmtDate, hash};
})();
