#!/usr/bin/env python3
"""Set up a flashcards project in the current folder (or --dir).

Usage:
    python3 -I init.py --name "German A1" --deck-root "German::A1" [--reverse] [--port 8040]

Creates only what is missing; never overwrites existing files:
    flashcards.json       project config (deck root, note type, media prefix, port, ...)
    FLASHCARDS.md         project brief: goal, sources, card rules agreed with the user
    CLAUDE.md             one-line pointer to the skill + brief (only if there is none)
    card.css              card styling, shared by the preview and the Anki note type
    sources/README.md     tells the user what material to drop into sources/
    cards/review.csv      staging: new cards go here first
    cards/approved.csv    approved cards (what gets imported into Anki)
    media/  sources/  preview/   and a .gitignore entry for preview/
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
from cardfile import CONFIG_NAME, DEFAULTS, SKILL_DIR, save

BRIEF = """# {name}: flashcards brief

Read this before writing cards. Update it whenever the user settles a rule or decision.

## Goal
- What is being studied, and why (exam, interview, language level, hobby):
- Card language(s):

## Sources (priority order)
- Files in `sources/`, links, or notes the user gave:

## Card rules for this deck
- Front:
- Back:
- Notes:
- Tags:

## Deck structure
- Root deck: `{root}`
- Sub-decks (one per study unit):

## Media
- Audio: no
- Images: no

## Anki
- Connection: AnkiConnect / manual import (decided at setup)
- Note type: `{note_type}`{reverse}

## Decisions log
"""

SOURCES_README = """# Put your study material here

Drop the files you want flashcards from into this folder:

- PDFs: course books, study guides, lecture notes
- Slides: export them to PDF first (PowerPoint, Keynote and Google Slides all can).
  A PDF keeps the pictures and diagrams; Claude reads it page by page.
- Notes: Markdown or text files, Notion or Obsidian exports
- Saved web pages: File > Save Page As > "Webpage, Complete"
- Images: photos of book pages, diagrams

Then tell Claude which file (and which chapter or section) to start with.
Claude reads these files but never changes or deletes them. This folder is in
.gitignore, so course material doesn't end up in a shared repo by accident.
"""

CLAUDE_MD = """# Flashcards project

Use the `flashcards` skill for any card work in this folder.
Project brief: @FLASHCARDS.md
"""


def slug(text: str) -> str:
    """'Español B1' -> 'espanol_b1'. Non-Latin names fall back to a short hash."""
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")[:24].rstrip("_")
    return s or "deck_" + hashlib.sha1(text.encode("utf-8")).hexdigest()[:6]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help='project name, e.g. "German A1"')
    ap.add_argument("--deck-root", help="Anki root deck (default: the name)")
    ap.add_argument("--note-type", help='Anki note type (default: "Flashcards: <name>")')
    ap.add_argument("--reverse", action="store_true", help="also create a reversed card (Back -> Front)")
    ap.add_argument("--port", type=int, default=DEFAULTS["port"], help="preview server port")
    ap.add_argument("--dir", default=".", help="project folder (default: current folder)")
    a = ap.parse_args()

    root = Path(a.dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    made, kept = [], []

    note_type = a.note_type or f"Flashcards: {a.name}" + (" (+reverse)" if a.reverse else "")
    cfg_path = root / CONFIG_NAME
    if cfg_path.exists():
        kept.append(CONFIG_NAME)
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    else:
        cfg = {
            "name": a.name,
            "deck_root": a.deck_root or a.name,
            "note_type": note_type,
            "reverse_cards": a.reverse,
            "media_prefix": slug(a.name) + "_",
            "port": a.port,
            "anki_connect_url": DEFAULTS["anki_connect_url"],
            "duplicate_scope": DEFAULTS["duplicate_scope"],
            "tts": None,
        }
        cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        made.append(CONFIG_NAME)

    files = {
        "FLASHCARDS.md": lambda p: p.write_text(BRIEF.format(
            name=cfg["name"], root=cfg["deck_root"], note_type=cfg["note_type"],
            reverse=" (with reversed cards)" if cfg.get("reverse_cards") else ""), encoding="utf-8"),
        "CLAUDE.md": lambda p: p.write_text(CLAUDE_MD, encoding="utf-8"),
        "card.css": lambda p: shutil.copyfile(SKILL_DIR / "assets" / "card.css", p),
        "sources/README.md": lambda p: p.write_text(SOURCES_README, encoding="utf-8"),
        "cards/review.csv": lambda p: save(p, []),
        "cards/approved.csv": lambda p: save(p, []),
    }
    for rel, create in files.items():
        p = root / rel
        if p.exists():
            kept.append(rel)
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            create(p)
            made.append(rel)

    for d in ("media", "sources", "preview"):
        if not (root / d).is_dir():
            (root / d).mkdir()
            made.append(d + "/")

    gi = root / ".gitignore"
    lines = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    if "preview/" not in lines:
        extra = ["preview/", "__pycache__/", ".DS_Store",
                 "# course material is often copyrighted: keep it out of shared repos", "sources/"]
        gi.write_text("\n".join(lines + [x for x in extra if x not in lines]) + "\n", encoding="utf-8")
        made.append(".gitignore (preview/, sources/)")

    print(f"project: {root}")
    print(f"deck root: {cfg['deck_root']} | note type: {cfg['note_type']} | media prefix: {cfg['media_prefix']}")
    if made:
        print("created: " + ", ".join(made))
    if kept:
        print("already there (left unchanged): " + ", ".join(kept))


if __name__ == "__main__":
    main()
