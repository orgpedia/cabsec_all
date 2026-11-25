"""The 4:5 video (ui-requirements §5, U32): the page in its video layout (index.html?video=1), stepped frame by
frame in headless Chrome and encoded by ffmpeg. A title card, the whole run (or a term, or a ministry followed) in
the Story view at the given speed, and an end card; an .srt of the captions beside it. Needs Playwright (with
Chrome) and ffmpeg.

  python -m cells.video --site ../../../site.cabsec-aob --out output/video/ministries-1947-2026.mp4 --speed 2
"""

import argparse
import asyncio
import http.server
import subprocess
import threading
from functools import partial
from pathlib import Path

from playwright.async_api import async_playwright

FPS = 30


def serve(root: Path) -> int:
  class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
  h = partial(Quiet, directory=str(root))
  srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
  threading.Thread(target=srv.serve_forever, daemon=True).start()
  return srv.server_address[1]


def ts(s: float) -> str:
  ms = int(round(s * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); sec, ms = divmod(ms, 1000)
  return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


async def render(site: Path, out: Path, speed: float, view: str, query: str, chrome: str | None,
                 title: tuple[str, str], end: tuple[str, str], intro: float, outro: float) -> None:
  port = serve(site)
  out.parent.mkdir(parents=True, exist_ok=True)
  enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                          "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
  async with async_playwright() as p:
    b = await p.chromium.launch(**({"executable_path": chrome} if chrome else {}), args=["--no-sandbox", "--no-proxy-server"])
    pg = await b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
    await pg.goto(f"http://127.0.0.1:{port}/index.html?video=1{query}")
    await pg.wait_for_function("window.cellsReady === true", timeout=120000)
    await pg.evaluate(f"setView('{view}')")
    # the photos, loaded before the first frame
    await pg.evaluate("""() => Promise.all(data.people.filter(p => p.image).map(p => new Promise(r => { const i = new Image(); i.onload = i.onerror = r; i.src = p.image; })))""")
    T = await pg.evaluate("player.dir.T")
    shot = lambda: pg.screenshot(type="jpeg", quality=92)
    n = 0
    await pg.evaluate("t => renderAt(t)", 0)
    await pg.evaluate("([a, b]) => videoCard(a, b)", list(title)); await pg.wait_for_timeout(100)
    img = await shot()
    for _ in range(int(intro * FPS)):
      enc.stdin.write(img); n += 1
    await pg.evaluate("videoCard(null)")
    frames = int(T / speed * FPS) + 1
    for k in range(frames):
      await pg.evaluate("t => renderAt(t)", min(T, k * speed / FPS))
      if k % 15 == 0: await pg.wait_for_timeout(30)   # let the photo crossfades and images settle
      enc.stdin.write(await shot()); n += 1
      if k % 300 == 0: print(f"{k}/{frames}", flush=True)
    await pg.evaluate("([a, b]) => videoCard(a, b)", list(end)); await pg.wait_for_timeout(100)
    img = await shot()
    for _ in range(int(outro * FPS)):
      enc.stdin.write(img); n += 1
    caps = await pg.evaluate("videoCaptions()")
    await b.close()
  enc.stdin.close(); enc.wait()
  srt = []
  for i, c in enumerate(caps, 1):
    a, z = intro + c["t0"] / speed, intro + c["t1"] / speed
    srt.append(f"{i}\n{ts(a)} --> {ts(z)}\n{c['text']}\n")
  out.with_suffix(".srt").write_text("\n".join(srt), encoding="utf-8")
  print(f"{out}: {n} frames, {n / FPS:.1f} s")


def main() -> None:
  ap = argparse.ArgumentParser()
  ap.add_argument("--site", default="../../../site.cabsec-aob")
  ap.add_argument("--out", default="output/video/ministries-1947-2026.mp4")
  ap.add_argument("--speed", type=float, default=2.0)
  ap.add_argument("--view", default="story")
  ap.add_argument("--query", default="", help="&pm=… or a #… is not used; e.g. '' for the whole run")
  ap.add_argument("--chrome", default=None)
  a = ap.parse_args()
  title = ("How India's ministries divided,<br>fused and popped", "1947 → 2026<br>every change to the Allocation of Business Rules")
  end = ("orgpedia.in", "Each cell is a ministry; its size, the subjects it is given.<br>Source: Allocation of Business Rules, cabsec.gov.in")
  asyncio.run(render(Path(a.site).resolve(), Path(a.out), a.speed, a.view, a.query, a.chrome, title, end, 2.5, 3.0))


if __name__ == "__main__":
  main()
