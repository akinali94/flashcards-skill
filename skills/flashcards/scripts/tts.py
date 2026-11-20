#!/usr/bin/env python3
"""Add text-to-speech audio to cards, using the TTS command set in flashcards.json.

Usage (from inside the project):
    python3 -I tts.py --dry-run              # list what would be voiced (cards/approved.csv)
    python3 -I tts.py                        # make the audio, add [sound:...] to Media
    python3 -I tts.py --csv cards/review.csv 1-5

flashcards.json needs a "tts" block, for example (macOS):
    "tts": {
      "command": ["say", "-v", "Anna", "-o", "{out}", "-f", "{text_file}"],
      "output_ext": "aiff",
      "field": "Back"
    }
Placeholders in "command": {out} = file to write, {text_file} = a UTF-8 file holding the
text, {text} = the text itself. Set "stdin": true to pipe the text in instead.
Optional keys: "field" (Front or Back, default Back), "skip_tags" (default ["no-audio"]),
"max_chars" (default 200), "allow_multiline" (default false).

Text cleanup: <small>...</small> and <span class="no-tts">...</span> are left out, other
HTML is stripped. Cards are skipped when they already have a [sound:] ref, carry a skip tag,
or the text is empty, too long, or spans several lines (<br>).
Files are named <prefix>tts_<words>_<hash>.mp3; the hash covers text + command, so the same
text with the same voice is reused and a new voice makes new files. Non-mp3 output is
converted with ffmpeg when it is installed (wav is kept as is without it).
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
from cardfile import COLUMNS, MEDIA, TAGS, find_project, load, pick, save


def clean(field: str) -> tuple[str, str]:
    """Return (text, reason). reason is non-empty when the card should be skipped."""
    s = re.sub(r"<small\b.*?</small>", " ", field, flags=re.S | re.I)
    s = re.sub(r"""<span\b[^>]*class=["'][^"']*no-tts[^"']*["'][^>]*>.*?</span>""", " ", s, flags=re.S | re.I)
    s = re.sub(r"\[sound:[^\]]*\]", " ", s)
    lines = [ln for ln in re.split(r"<br\s*/?>|</p>|</div>|</li>|\n", s, flags=re.I)
             if re.sub(r"<[^>]+>", "", ln).strip()]
    multi = len(lines) > 1
    s = html.unescape(re.sub(r"<[^>]+>", " ", " ".join(lines)))
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return "", "no text"
    return s, ("several lines" if multi else "")


def file_stem(prefix: str, text: str, command: list[str]) -> str:
    words = re.sub(r"[^\w]+", "_", text.lower(), flags=re.U).strip("_")[:32].rstrip("_")
    h = hashlib.sha1((json.dumps(command) + "\n" + text).encode("utf-8")).hexdigest()[:8]
    return f"{prefix}tts_{words}_{h}"


def synth(cfg: dict, text: str, out: Path, tmp: Path) -> None:
    text_file = tmp / "text.txt"
    text_file.write_text(text, encoding="utf-8")
    args = [a.replace("{out}", str(out)).replace("{text_file}", str(text_file)).replace("{text}", text)
            for a in cfg["command"]]
    subprocess.run(args, input=text.encode("utf-8") if cfg.get("stdin") else None,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True, timeout=120)
    if not out.exists() or out.stat().st_size < 100:
        raise RuntimeError(f"no audio written to {out.name}")


def main() -> None:
    proj = find_project()
    ap = argparse.ArgumentParser()
    ap.add_argument("numbers", nargs="*", help="card numbers (#N); default all")
    ap.add_argument("--csv", help=f"card CSV (default: {proj['approved_csv']})")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    cfg = proj["tts"]
    if not cfg or not cfg.get("command"):
        sys.exit('No "tts" block with a "command" in flashcards.json. See references/media.md.')
    field = COLUMNS.index(cfg.get("field", "Back"))
    skip_tags = set(cfg.get("skip_tags", ["no-audio"]))
    max_chars = int(cfg.get("max_chars", 200))
    ext = cfg.get("output_ext", "mp3").lstrip(".").lower()
    ffmpeg = shutil.which("ffmpeg")
    final_ext = "mp3" if ext == "mp3" or ffmpeg else ext
    if final_ext not in ("mp3", "wav", "ogg", "m4a"):
        sys.exit(f"output_ext {ext!r} needs ffmpeg to become mp3, and ffmpeg is not installed.")

    path = Path(a.csv).resolve() if a.csv else proj.approved
    rows = load(path)
    picks = pick(rows, a.numbers) if rows else set()
    plan, skipped = [], {}
    for n in sorted(picks):
        r = rows[n - 1]
        if "[sound:" in r[MEDIA]:
            skipped["has audio"] = skipped.get("has audio", 0) + 1
            continue
        if skip_tags & set(r[TAGS].split()):
            skipped["skip tag"] = skipped.get("skip tag", 0) + 1
            continue
        text, why = clean(r[field])
        if not why and len(text) > max_chars:
            why = f"longer than {max_chars} chars"
        if why and not (why == "several lines" and cfg.get("allow_multiline")):
            skipped[why] = skipped.get(why, 0) + 1
            continue
        plan.append((n, text, file_stem(proj["media_prefix"], text, cfg["command"]) + "." + final_ext))

    print(f"{path.name}: {len(plan)} card(s) to voice; skipped: "
          + (", ".join(f"{v} {k}" for k, v in skipped.items()) or "none"))
    if a.dry_run:
        for n, text, name in plan[:40]:
            state = "exists" if (proj.media_dir / name).exists() else "new"
            print(f"  #{n} [{state}] {text[:70]}")
        if len(plan) > 40:
            print(f"  ... and {len(plan) - 40} more")
        return
    if not plan:
        return
    exe = cfg["command"][0]
    if not (shutil.which(exe) or Path(exe).exists()):
        sys.exit(f"TTS program {exe!r} not found. Install it or change tts.command (references/media.md).")

    tmp = proj.media_dir / ".tts_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    made = reused = failed = 0
    try:
        for n, text, name in plan:
            dst = proj.media_dir / name
            if not dst.exists():
                try:
                    raw = tmp / ("out." + ext)
                    raw.unlink(missing_ok=True)
                    synth(cfg, text, raw, tmp)
                    if ext == final_ext:
                        shutil.move(str(raw), str(dst))
                    else:
                        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(raw),
                                        "-codec:a", "libmp3lame", "-qscale:a", "4", str(dst)],
                                       check=True, timeout=120)
                    made += 1
                except (subprocess.SubprocessError, OSError, RuntimeError) as e:
                    detail = getattr(e, "stderr", b"") or b""
                    print(f"  FAIL #{n}: {e} {detail.decode(errors='replace')[:200]}".rstrip())
                    failed += 1
                    continue
            else:
                reused += 1
            media = rows[n - 1][MEDIA].strip()
            rows[n - 1][MEDIA] = (media + " " if media else "") + f"[sound:{name}]"
    finally:
        save(path, rows)
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"audio: {made} made, {reused} reused, {failed} failed; {path.name} updated")


if __name__ == "__main__":
    main()
