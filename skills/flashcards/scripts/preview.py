#!/usr/bin/env python3
"""Render a card CSV as Anki-like cards in an HTML page, optionally with a live server.

Usage (from inside the project):
    python3 -I preview.py --serve                  # cards/review.csv, live reload (run in background)
    python3 -I preview.py cards/approved.csv       # any CSV, build once, print the file path

--serve prints the URL. The server tries the configured port, then the next 19 ports.
The page rebuilds when the CSV, card.css or flashcards.json changes, and reloads itself.
Each card shows its number (#N), which the user uses to ask for changes.
"""
from __future__ import annotations

import argparse
import html
import http.server
import re
import sys
import threading
import time
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
from cardfile import COLUMNS, CONFIG_NAME, IMG_RE, SOUND_RE, Project, find_project, load


def resolve_media(field: str, proj: Project) -> str:
    """[sound:x] -> <audio>; <img src="x"> -> points at media/x. Missing files show in red."""
    rel = "../" + proj["media_dir"].strip("/") + "/"

    def missing(name: str) -> str:
        return f'<span class="missing">missing media: {html.escape(name)}</span>'

    def sound(m: re.Match) -> str:
        name = m.group(1)
        if not (proj.media_dir / name).exists():
            return missing(name)
        return f'<audio controls preload="none" src="{rel}{html.escape(name)}"></audio>'

    def img(m: re.Match) -> str:
        tag, name = m.group(0), m.group(1)
        if not (proj.media_dir / name).exists():
            return missing(name) + tag
        s, e = m.start(1) - m.start(0), m.end(1) - m.start(0)
        return tag[:s] + rel + name + tag[e:]

    field = SOUND_RE.sub(sound, field)
    return re.sub(IMG_RE.pattern + r"[^>]*>", img, field, flags=re.I)


def card_html(i: int, c: dict, proj: Project) -> str:
    def field(name: str) -> str:
        return resolve_media(c.get(name, ""), proj)

    notes = f'<div class="notes">{field("Notes")}</div>' if c.get("Notes", "").strip() else ""
    media = f'<div class="media">{field("Media")}</div>' if c.get("Media", "").strip() else ""
    tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in c.get("Tags", "").split())
    deck = proj.short_deck(c.get("Deck", "").strip())
    deck = (f'<span class="deck">{html.escape(deck)}</span>' if deck
            else '<span class="deck nodeck">no deck</span>')
    return f"""
<section class="wrap" id="c{i}">
  <div class="meta"><span class="num">#{i}</span>{deck}{tags}</div>
  <div class="card">
    <div class="front">{field("Front")}</div>
    <div class="answer">
      <hr id="answer">
      <div class="back">{field("Back")}</div>
      {notes}{media}
    </div>
  </div>
</section>"""


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
{css}
:root {{ --page: #eaeef2; --box: #ffffff; --ink: #1f2328; --muted: #57606a; }}
body {{ margin: 0; background: var(--page); color: var(--ink);
        font-family: -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; }}
header {{ position: sticky; top: 0; z-index: 1; background: #24292f; color: #fff;
          padding: 10px 16px; display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }}
header h1 {{ font-size: 16px; margin: 0; font-weight: 600; }}
header label {{ font-size: 14px; cursor: pointer; }}
main {{ padding: 16px; display: grid; gap: 16px; }}
.wrap {{ background: var(--box); border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.12);
         padding: 12px 16px 18px; max-width: 760px; width: 100%; margin: 0 auto; box-sizing: border-box; }}
.meta {{ display: flex; gap: 8px; align-items: center; margin-bottom: 6px; font-size: 12px; flex-wrap: wrap; }}
.num {{ font-weight: 700; color: #0969da; font-size: 14px; }}
.tag {{ background: #ddf4ff; color: #0550ae; padding: 1px 8px; border-radius: 10px; }}
.deck {{ background: #fff8c5; color: #7d4e00; padding: 1px 8px; border-radius: 10px; }}
.nodeck, .missing {{ background: #ffebe9; color: #cf222e; padding: 1px 8px; border-radius: 10px; }}
.empty {{ text-align: center; color: var(--muted); }}
body.quiz .answer {{ display: none; }}
body.quiz .wrap.open .answer {{ display: block; }}
body.quiz .wrap {{ cursor: pointer; }}
body.dark {{ --page: #111; --box: #1e1e1e; --ink: #e6edf3; --muted: #9aa4af; }}
</style></head>
<body>
<header>
  <h1>{title} &middot; {n} cards</h1>
  <label><input type="checkbox" id="quiz"> Quiz mode (click a card to reveal)</label>
  <label><input type="checkbox" id="dark"> Night mode</label>
</header>
<main>{cards}</main>
<script>
const b = document.body;
const pref = k => {{ try {{ return localStorage.getItem("fc-" + k) === "1"; }} catch (e) {{ return false; }} }};
const keep = (k, v) => {{ try {{ localStorage.setItem("fc-" + k, v ? "1" : "0"); }} catch (e) {{}} }};
function applyDark() {{
  document.querySelectorAll(".card").forEach(c => c.classList.toggle("nightMode", b.classList.contains("dark")));
}}
for (const id of ["quiz", "dark"]) {{
  const box = document.getElementById(id);
  box.checked = pref(id); b.classList.toggle(id, box.checked);
  box.onchange = () => {{ b.classList.toggle(id, box.checked); keep(id, box.checked); applyDark(); }};
}}
applyDark();
document.querySelectorAll(".wrap").forEach(w => w.onclick = e => {{
  if (e.target.closest("audio, a") || getSelection().toString()) return;
  w.classList.toggle("open");
}});
if (location.protocol.startsWith("http")) {{
  let last = null;
  setInterval(async () => {{
    try {{
      const r = await fetch(location.href, {{ method: "HEAD", cache: "no-store" }});
      const m = r.headers.get("Last-Modified");
      if (last && m && m !== last) location.reload();
      last = m;
    }} catch (e) {{}}
  }}, 1000);
}}
</script>
</body></html>
"""


def build(csv_path: Path) -> Path:
    proj = find_project(csv_path.parent)
    cards = [dict(zip(COLUMNS, r)) for r in load(csv_path)]
    out_dir = proj.root / "preview"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{csv_path.stem}.html"
    body = "".join(card_html(i, c, proj) for i, c in enumerate(cards, 1))
    out.write_text(PAGE.format(
        title=html.escape(f"{proj['name']}: {csv_path.stem}"), n=len(cards),
        css=proj.css.read_text(encoding="utf-8"),
        cards=body or '<p class="empty">No cards here yet.</p>'), encoding="utf-8")
    return out


def serve(csv_path: Path) -> None:
    proj = find_project(csv_path.parent)
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(proj.root))
    handler.log_message = lambda *a, **k: None
    first = int(proj["port"])
    srv = port = None
    for p in range(first, first + 20):
        try:
            srv = http.server.ThreadingHTTPServer(("127.0.0.1", p), handler)
            port = p
            break
        except OSError:
            continue
    if srv is None:
        sys.exit(f"no free port in {first}..{first + 19}; change 'port' in {CONFIG_NAME}")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"Serving: http://localhost:{port}/preview/{csv_path.stem}.html  (Ctrl+C to stop)", flush=True)
    watched = [csv_path, proj.css, proj.root / CONFIG_NAME]
    mtimes = None
    while True:
        now = [p.stat().st_mtime if p.exists() else 0 for p in watched]
        if now != mtimes:
            try:
                build(csv_path)
                print(time.strftime("%H:%M:%S"), "rebuilt", flush=True)
            except Exception as e:  # keep serving through a half-written CSV
                print("build error:", e, flush=True)
            mtimes = now
        time.sleep(0.5)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?", help="card CSV (default: the review CSV)")
    ap.add_argument("--serve", action="store_true", help="serve with live reload")
    a = ap.parse_args()
    path = Path(a.csv).resolve() if a.csv else find_project().review
    if not path.exists():
        sys.exit(f"{path} does not exist")
    if a.serve:
        serve(path)
    else:
        print(build(path))


if __name__ == "__main__":
    main()
