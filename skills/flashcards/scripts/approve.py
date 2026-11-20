#!/usr/bin/env python3
"""Move reviewed cards from the review CSV into the approved CSV.

Usage (from inside the project):
    python3 -I approve.py                 # all cards in cards/review.csv
    python3 -I approve.py 1 3-5 9         # only these (#N in the preview)
    python3 -I approve.py --to other.csv 2

Approved cards are appended to the target. Cards whose Front is already there are skipped
and stay in review. Cards without a Deck are refused (set one with set_deck.py first).
Card numbers in review.csv shift after this, so re-read the preview before the next edit.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
from cardfile import DECK, FRONT, NCOLS, find_project, load, pick, raw_column_counts, save


def main() -> None:
    proj = find_project()
    ap = argparse.ArgumentParser()
    ap.add_argument("numbers", nargs="*", help="card numbers (#N); default all")
    ap.add_argument("--to", help=f"target CSV (default: {proj['approved_csv']})")
    a = ap.parse_args()
    target = Path(a.to).resolve() if a.to else proj.approved

    review = load(proj.review)
    if not review:
        sys.exit(f"{proj['review_csv']} is empty")
    bad = [i for i, n in enumerate(raw_column_counts(proj.review), 1) if n != NCOLS]
    if bad:
        sys.exit(f"rows with the wrong column count: {bad}. Run validate.py first.")
    picks = pick(review, a.numbers)
    nodeck = sorted(n for n in picks if not review[n - 1][DECK].strip())
    if nodeck:
        sys.exit(f"cards without a Deck: {nodeck}. Run set_deck.py first.")

    deck = load(target)
    fronts = {r[FRONT] for r in deck}
    moved, dupes, keep = [], [], []
    for i, row in enumerate(review, 1):
        if i not in picks:
            keep.append(row)
        elif row[FRONT] in fronts:
            dupes.append(i)
            keep.append(row)
        else:
            row[DECK] = proj.deck_path(row[DECK])
            moved.append(row)
            fronts.add(row[FRONT])

    save(target, deck + moved)
    save(proj.review, keep)
    print(f"moved {len(moved)} -> {target.name} (now {len(deck) + len(moved)} cards); "
          f"{len(keep)} left in {proj.review.name}")
    if dupes:
        print(f"skipped, Front already in {target.name}: #{', #'.join(map(str, dupes))}")


if __name__ == "__main__":
    main()
