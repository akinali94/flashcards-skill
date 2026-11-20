#!/usr/bin/env python3
"""Check a card CSV: columns, empty fields, duplicates, deck, raw `<` in code, media files.

Usage (from inside the project):
    python3 -I validate.py                       # cards/review.csv, checked against approved
    python3 -I validate.py cards/approved.csv    # any card CSV

Exit code 1 when there are errors. Warnings don't fail. Ends with cards per deck.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
from cardfile import (BACK, DECK, FRONT, HEADER, MEDIA, NCOLS, NOTES, TAGS, find_project,
                      load, media_refs, raw_column_counts)

# HTML tags allowed in fields. Anything else after `<` is probably unescaped code
# such as List<String> and must be written as List&lt;String&gt;.
HTML_TAGS = {
    "a", "abbr", "b", "blockquote", "br", "cite", "code", "dd", "del", "div", "dl", "dt",
    "em", "figcaption", "figure", "font", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "i",
    "img", "ins", "kbd", "li", "mark", "ol", "p", "pre", "q", "rp", "rt", "ruby", "s",
    "samp", "small", "span", "strong", "sub", "sup", "table", "tbody", "td", "tfoot", "th",
    "thead", "tr", "u", "ul", "var",
}
TAG_RE = re.compile(r"</?([A-Za-z][\w-]*)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", nargs="?", help="card CSV (default: the review CSV)")
    a = ap.parse_args()
    proj = find_project()
    target = Path(a.csv).resolve() if a.csv else proj.review
    if not target.exists():
        sys.exit(f"{target} does not exist")
    rows = load(target)
    errors = warns = 0

    def err(msg: str) -> None:
        nonlocal errors
        print("ERROR " + msg)
        errors += 1

    def warn(msg: str) -> None:
        nonlocal warns
        print("warn  " + msg)
        warns += 1

    if not target.read_text(encoding="utf-8").startswith(HEADER):
        warn(f"{target.name}: header differs from the standard Anki header "
             "(any approve/set_deck run rewrites it)")

    others: dict[str, str] = {}
    other_backs: dict[str, str] = {}
    if proj.approved.exists() and proj.approved.resolve() != target:
        for r in load(proj.approved):
            others.setdefault(r[FRONT], proj.approved.name)
            other_backs.setdefault(r[BACK], proj.approved.name)

    counts = raw_column_counts(target)
    prefix = proj["media_prefix"]
    seen: set[str] = set()
    backs: set[str] = set()
    for i, (r, n) in enumerate(zip(rows, counts), 1):
        if n != NCOLS:
            err(f"#{i}: {n} columns, expected {NCOLS} ({';'.join(['Front', 'Back', 'Notes', 'Media', 'Tags', 'Deck'])}); "
                'check for an unescaped " inside a field (write it as "")')
            continue
        front, back = r[FRONT], r[BACK]
        if not front.strip() or not back.strip():
            err(f"#{i}: empty Front or Back")
        if front in seen:
            err(f"#{i}: same Front twice in this file: {front[:70]!r}")
        if front in others:
            err(f"#{i}: Front already in {others[front]}: {front[:70]!r}")
        if back.strip() and (back in backs or back in other_backs):
            where = "this file" if back in backs else other_backs[back]
            warn(f"#{i}: same Back already in {where}: {back[:70]!r}")
        if not r[DECK].strip():  # a short deck like "Unit 1" is fine: approve puts it under the root
            err(f"#{i}: no Deck (set it with set_deck.py)")
        if r[TAGS] != r[TAGS].strip() or "  " in r[TAGS]:
            warn(f"#{i}: extra spaces in Tags")
        for name, col in (("Front", FRONT), ("Back", BACK), ("Notes", NOTES), ("Media", MEDIA)):
            bad = sorted({t for t in TAG_RE.findall(r[col]) if t.lower() not in HTML_TAGS})
            if bad:
                err(f"#{i}: {name} has raw <{', <'.join(bad)}: escape code as &lt; &gt; &amp;")
        for col in (FRONT, BACK, NOTES, MEDIA):
            for ref in media_refs(r[col]):
                if "/" in ref or "\\" in ref:
                    err(f"#{i}: media ref {ref!r} must be a bare file name in {proj['media_dir']}/")
                elif not (proj.media_dir / ref).exists():
                    err(f"#{i}: missing media file {proj['media_dir']}/{ref}")
                elif prefix and not ref.startswith(prefix):
                    warn(f"#{i}: media file {ref!r} has no project prefix {prefix!r} "
                         "(risk of a name clash in Anki's shared media folder)")
        seen.add(front)
        backs.add(back)

    decks = Counter(proj.short_deck(r[DECK]) or "(no deck)" for r in rows)
    print(f"{target.name}: {len(rows)} cards, {errors} error(s), {warns} warning(s)")
    for d, c in sorted(decks.items()):
        print(f"  {c:>4}  {d}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
