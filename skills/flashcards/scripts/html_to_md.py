#!/usr/bin/env python3
"""Extract the article text of a saved web page (.html) as Markdown, for card writing.

Usage:
    python3 -I html_to_md.py <page.html> <out.md> [--start h1|none] [--stop "TEXT" ...]

Keeps headings (h1-h4), paragraphs, list items, code blocks, tables and figure captions.
Drops scripts, styles, inline SVG diagrams (extract_svgs.py saves those), buttons, nav,
forms and footers. By default it starts at the first <h1> (skipping site chrome above
the article); --start none keeps everything. --stop ends the output at the first block
whose whole text equals TEXT (e.g. a "Comments" or "Related articles" heading).
"""
from __future__ import annotations

import argparse
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

SKIP = {"script", "style", "svg", "button", "nav", "noscript", "head", "form", "footer", "template"}
BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "pre", "tr", "figcaption", "blockquote", "div", "section", "article"}
VOID = {"br", "img", "hr", "input", "meta", "link", "source", "wbr", "col", "area", "base", "embed",
        "param", "track"}


class Extractor(HTMLParser):
    def __init__(self, start_tag: str | None) -> None:
        super().__init__(convert_charrefs=True)
        self.start_tag = start_tag
        self.skip = 0
        self.started = start_tag is None
        self.out: list[str] = []
        self.buf: list[str] = []
        self.stack: list[str] = []
        self.pre = 0

    def flush(self, prefix: str = "") -> None:
        text = "".join(self.buf)
        if not self.pre:
            text = re.sub(r"\s+", " ", text).strip()
        if text.strip():
            self.out.append(prefix + text)
        self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            if tag == "br" and self.started and not self.skip:
                self.buf.append("\n" if self.pre else " ")
            return
        self.stack.append(tag)
        if tag in SKIP:
            self.skip += 1
            return
        if tag == self.start_tag:
            self.started = True
        if self.skip or not self.started:
            return
        if tag in BLOCK:
            self.flush()
        if tag == "pre":
            self.pre += 1
        if tag in ("td", "th"):
            self.buf.append(" | ")

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:  # pop to the matching tag (tolerates sloppy HTML)
            top = self.stack.pop()
            if top in SKIP:
                self.skip -= 1
            if top == tag:
                break
        if self.skip or not self.started:
            return
        if tag == "pre":
            self.out.append("```\n" + "".join(self.buf).strip("\n") + "\n```")
            self.buf = []
            self.pre -= 1
        elif tag in ("h1", "h2", "h3", "h4"):
            self.flush("#" * int(tag[1]) + " ")
        elif tag == "li":
            self.flush("- ")
        elif tag == "figcaption":
            self.flush("_Figure: ")
            if self.out and self.out[-1].startswith("_Figure: "):
                self.out[-1] += "_"
        elif tag in BLOCK:
            self.flush()

    def handle_data(self, data):
        if self.skip or not self.started:
            return
        self.buf.append(data)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("out")
    ap.add_argument("--start", default="h1", help="tag that starts the article, or 'none'")
    ap.add_argument("--stop", action="append", default=[], help="block text that ends the article")
    a = ap.parse_args()

    p = Extractor(None if a.start == "none" else a.start)
    p.feed(Path(a.html).read_text(encoding="utf-8", errors="replace"))
    p.flush()
    if not p.out and a.start != "none":
        sys.exit(f"no <{a.start}> found; try --start none")
    stops = {s.strip() for s in a.stop}
    lines, prev = [], None
    for line in p.out:
        if line.strip() in stops:
            break
        if line != prev:  # nested divs repeat the same text
            lines.append(html.unescape(line))
        prev = line
    Path(a.out).write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(lines)} blocks -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
