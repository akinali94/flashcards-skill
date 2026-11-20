#!/usr/bin/env python3
"""Save the diagram SVGs embedded in a saved web page (.html) as small .svg files.

Usage:
    python3 -I extract_svgs.py <page.html> <out_dir> --prefix <media_prefix> [--min-size 5000]

Each large inline <svg> becomes <out_dir>/<prefix><caption_slug>.svg, where the caption is
the first text after the SVG on the page. Small SVGs (icons) are skipped. Output is
minified (comments and metadata removed, long decimals rounded) to keep Anki's media
folder small. Existing files are never overwritten. Prints a size report.
Use the project's media_prefix (flashcards.json) so names can't clash in Anki.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SVG_RE = re.compile(r"<svg\b.*?</svg>", re.S | re.I)
TAG_RE = re.compile(r"<[^>]+>")
NUM_RE = re.compile(r"-?\d+\.\d{2,}")


def caption_after(page: str, end: int) -> str:
    text = TAG_RE.sub("\n", page[end:end + 3000])
    for line in (ln.strip() for ln in text.splitlines()):
        if line:
            return line
    return ""


def slugify(text: str, maxlen: int = 50) -> str:
    text = re.split(r"\s+-\s+", text)[0]  # drop a " - long explanation" tail
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:maxlen].rstrip("_") or "diagram"


def round_numbers(svg: str, precision: int) -> str:
    """Round long decimals, but not inside embedded base64 data (fonts, images)."""
    parts = re.split(r"(url\(data:[^)]*\)|data:[^\"')\s]+)", svg)
    for i in range(0, len(parts), 2):
        parts[i] = NUM_RE.sub(lambda m: f"{float(m.group()):.{precision}f}".rstrip("0").rstrip("."), parts[i])
    return "".join(parts)


def minify(svg: str, precision: int = 1) -> str:
    svg = round_numbers(svg, precision)
    svg = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
    svg = re.sub(r"<metadata\b.*?</metadata>", "", svg, flags=re.S)
    svg = re.sub(r">\s+<", "><", svg)
    svg = re.sub(r"[ \t\r\n]+", " ", svg)
    if "xmlns=" not in svg[:300]:
        svg = svg.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
    return svg.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("out_dir")
    ap.add_argument("--prefix", default="", help="file name prefix (the project's media_prefix)")
    ap.add_argument("--min-size", type=int, default=5000, help="skip SVGs shorter than this (icons)")
    a = ap.parse_args()

    page = Path(a.html).read_text(encoding="utf-8", errors="replace")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    seen: dict[str, int] = {}
    total_in = total_out = 0
    for m in SVG_RE.finditer(page):
        raw = m.group(0)
        if len(raw) < a.min_size:
            continue
        slug = slugify(caption_after(page, m.end()))
        seen[slug] = seen.get(slug, 0) + 1
        if seen[slug] > 1:
            slug = f"{slug}_{seen[slug]}"
        path = out / f"{a.prefix}{slug}.svg"
        if path.exists():
            print(f"skip (exists): {path.name}", file=sys.stderr)
            continue
        small = minify(raw)
        path.write_text(small, encoding="utf-8")
        total_in += len(raw.encode())
        total_out += len(small.encode())
        print(f"{len(raw.encode()):>7} -> {len(small.encode()):>7} B  {path.name}")
    print(f"total {total_in} -> {total_out} B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
