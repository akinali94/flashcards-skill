"""Shared helpers for a flashcards project: config, CSV I/O, card numbers, media refs.

A project is any folder holding a `flashcards.json` (created by init.py). Scripts find
it by walking up from the current directory, so run them from inside the project.

Card CSV columns (same in every project):  Front;Back;Notes;Media;Tags;Deck
  - Front/Back/Notes are HTML.
  - Media holds Anki media refs: [sound:x.mp3] and/or <img src="x.svg">. Files live in media/.
  - Tags are space-separated (Anki style, `::` for hierarchy).
  - Deck is the full Anki deck path, e.g. "German::A1::Greetings".
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CONFIG_NAME = "flashcards.json"
COLUMNS = ["Front", "Back", "Notes", "Media", "Tags", "Deck"]
NCOLS = len(COLUMNS)
FRONT, BACK, NOTES, MEDIA, TAGS, DECK = range(NCOLS)
HEADER = (
    "#separator:comma\n#html:true\n"
    f"#columns:{';'.join(COLUMNS)}\n"
    f"#tags column:{TAGS + 1}\n#deck column:{DECK + 1}\n"
)
DEFAULTS = {
    "name": "Flashcards",
    "deck_root": "",
    "note_type": "Flashcards",
    "reverse_cards": False,
    "media_prefix": "",
    "port": 8040,
    "anki_connect_url": "http://localhost:8765",
    "duplicate_scope": "deck",
    "review_csv": "cards/review.csv",
    "approved_csv": "cards/approved.csv",
    "media_dir": "media",
    "tts": None,
}

SOUND_RE = re.compile(r"\[sound:([^\]]+)\]")
IMG_RE = re.compile(r"""<img\b[^>]*?\bsrc\s*=\s*["']([^"']+)["']""", re.I)


class Project:
    """A flashcards project rooted at the folder that holds flashcards.json."""

    def __init__(self, root: Path) -> None:
        self.root = root
        raw = json.loads((root / CONFIG_NAME).read_text(encoding="utf-8"))
        self.cfg = {**DEFAULTS, **raw}

    def __getitem__(self, key: str):
        return self.cfg[key]

    @property
    def review(self) -> Path:
        return self.root / self.cfg["review_csv"]

    @property
    def approved(self) -> Path:
        return self.root / self.cfg["approved_csv"]

    @property
    def media_dir(self) -> Path:
        return self.root / self.cfg["media_dir"]

    @property
    def css(self) -> Path:
        own = self.root / "card.css"
        return own if own.exists() else SKILL_DIR / "assets" / "card.css"

    def deck_path(self, deck: str) -> str:
        """'Greetings' -> '<root>::Greetings'; a path already under the root is kept."""
        root = self.cfg["deck_root"].strip()
        deck = deck.strip().strip(":")
        if not root or deck == root or deck.startswith(root + "::"):
            return deck
        return f"{root}::{deck}" if deck else root

    def short_deck(self, deck: str) -> str:
        """Deck path without the root, for badges and summaries."""
        root = self.cfg["deck_root"].strip()
        if root and deck.startswith(root + "::"):
            return deck[len(root) + 2:]
        return deck


def find_project(start: Path | None = None) -> Project:
    here = (start or Path.cwd()).resolve()
    for d in [here, *here.parents]:
        if (d / CONFIG_NAME).is_file():
            return Project(d)
    sys.exit(f"No {CONFIG_NAME} found in {here} or its parents. "
             "Run init.py in the project folder first.")


def load(path: Path) -> list[list[str]]:
    """Read card rows. Only the leading '#' header lines are skipped, and the rest is
    parsed as one CSV stream, so quoted fields may span lines (code blocks), contain
    blank lines, or have lines starting with '#'. Short rows are padded."""
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    while lines and lines[0].startswith("#"):
        lines.pop(0)
    rows = [r for r in csv.reader(lines) if any(f.strip() for f in r)]
    return [r + [""] * (NCOLS - len(r)) if len(r) < NCOLS else r for r in rows]


def raw_column_counts(path: Path) -> list[int]:
    """Column count of every row as written (before padding), for validation."""
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    while lines and lines[0].startswith("#"):
        lines.pop(0)
    return [len(r) for r in csv.reader(lines) if any(f.strip() for f in r)]


def save(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(HEADER)
        csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n").writerows(rows)


def parse_numbers(specs: list[str]) -> set[int]:
    """['1-8', '12', '#15', '3,4'] -> {1..8, 12, 15, 3, 4}"""
    out: set[int] = set()
    for s in specs:
        for part in s.replace("#", "").split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                out.update(range(int(a), int(b) + 1))
            else:
                out.add(int(part))
    return out


def pick(rows: list[list[str]], specs: list[str]) -> set[int]:
    """Card numbers chosen by specs (all cards when none given); exits on bad numbers."""
    picks = parse_numbers(specs) or set(range(1, len(rows) + 1))
    bad = sorted(n for n in picks if not 1 <= n <= len(rows))
    if bad:
        sys.exit(f"no such card numbers: {bad} (file has {len(rows)} cards)")
    return picks


def media_refs(field: str) -> list[str]:
    return SOUND_RE.findall(field) + IMG_RE.findall(field)
