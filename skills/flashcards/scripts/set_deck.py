#!/usr/bin/env python3
"""Put cards into an Anki (sub)deck.

Usage (from inside the project):
    python3 -I set_deck.py "Greetings" 1-8 12        # -> <deck_root>::Greetings
    python3 -I set_deck.py "Unit 2::Verbs"           # all cards in the review CSV
    python3 -I set_deck.py "Verbs" 3 --csv cards/approved.csv

The deck is relative to deck_root in flashcards.json unless it already starts with it.
Numbers are card positions (#N in the preview); no numbers = every card in the file.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
from cardfile import DECK, find_project, load, pick, save


def main() -> None:
    proj = find_project()
    ap = argparse.ArgumentParser()
    ap.add_argument("deck", help='sub-deck under the root, e.g. "Unit 2::Verbs"')
    ap.add_argument("numbers", nargs="*", help="card numbers (#N); default all")
    ap.add_argument("--csv", help=f"card CSV (default: {proj['review_csv']})")
    a = ap.parse_args()
    path = Path(a.csv).resolve() if a.csv else proj.review
    rows = load(path)
    if not rows:
        sys.exit(f"{path.name} is empty")
    deck = proj.deck_path(a.deck)
    picks = pick(rows, a.numbers)
    for n in picks:
        rows[n - 1][DECK] = deck
    save(path, rows)
    print(f"{len(picks)} card(s) -> {deck}")


if __name__ == "__main__":
    main()
