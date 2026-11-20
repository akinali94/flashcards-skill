#!/usr/bin/env python3
"""Talk to Anki through the AnkiConnect add-on (Anki desktop must be open).

Usage (from inside the project):
    python3 -I anki_import.py --check            # is AnkiConnect reachable? note type, decks
    python3 -I anki_import.py --dry-run          # what an import of cards/approved.csv would do
    python3 -I anki_import.py                    # import cards/approved.csv
    python3 -I anki_import.py other.csv          # import another card CSV
    python3 -I anki_import.py --sync             # only sync Anki with AnkiWeb
    python3 -I anki_import.py --update-style     # push card.css to the existing note type

Import steps: create the note type if missing (fields Front, Back, Notes, Media; CSS from
card.css; a reversed card too when reverse_cards is true), create missing decks, upload media
files that Anki doesn't have yet, then add the notes, skipping duplicates (same Front in the
same deck, or in the whole collection when duplicate_scope is "collection").
It never deletes or changes existing notes, and never overwrites existing media files.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
from cardfile import DECK, MEDIA, TAGS, Project, find_project, load, media_refs

FIELDS = ["Front", "Back", "Notes", "Media"]
EXTRAS = ('{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}\n'
          '{{#Media}}<div class="media">{{Media}}</div>{{/Media}}')
TEMPLATES = [{
    "Name": "Card 1",
    "Front": '<div class="front">{{Front}}</div>',
    "Back": '<div class="front">{{Front}}</div>\n<hr id="answer">\n<div class="back">{{Back}}</div>\n' + EXTRAS,
}]
REVERSE = {
    "Name": "Card 2 (reversed)",
    "Front": '<div class="front">{{Back}}</div>',
    "Back": '<div class="front">{{Back}}</div>\n<hr id="answer">\n<div class="back">{{Front}}</div>\n' + EXTRAS,
}
SETUP_HELP = """AnkiConnect is not reachable at {url}.
To connect:
  1. Install Anki desktop from https://apps.ankiweb.net and open it.
  2. In Anki: Tools > Add-ons > Get Add-ons..., paste the code 2055492159, click OK.
  3. Restart Anki and keep it open while importing.
AnkiConnect only works with Anki desktop (not AnkiWeb or the phone apps). Cards reach your
phone when you sync. Without AnkiConnect you can import cards/approved.csv by hand
(File > Import); the skill's references/anki.md explains how."""


class Anki:
    def __init__(self, url: str) -> None:
        self.url = url

    def __call__(self, action: str, **params):
        body = json.dumps({"action": action, "version": 6, "params": params}).encode()
        try:
            with urllib.request.urlopen(urllib.request.Request(self.url, body), timeout=60) as r:
                resp = json.load(r)
        except OSError:
            sys.exit(SETUP_HELP.format(url=self.url))
        if resp.get("error"):
            raise RuntimeError(f"{action}: {resp['error']}")
        return resp["result"]


def check(anki: Anki, proj: Project) -> None:
    print(f"AnkiConnect: reachable (API version {anki('version')}) at {proj['anki_connect_url']}")
    model = proj["note_type"]
    if model in anki("modelNames"):
        fields = anki("modelFieldNames", modelName=model)
        ok = all(f in fields for f in FIELDS)
        print(f"note type {model!r}: exists, fields {fields}" + ("" if ok else "  <- missing some of " + str(FIELDS)))
    else:
        print(f"note type {model!r}: not there yet (the first import creates it)")
    root = proj["deck_root"]
    decks = [d for d in anki("deckNames") if not root or d == root or d.startswith(root + "::")]
    if decks:
        n = len(anki("findNotes", query=f'"deck:{root}"')) if root else None
        print(f"decks under {root!r}: {len(decks)}" + (f", {n} notes" if n is not None else ""))
    else:
        print(f"deck {root!r}: not there yet (the first import creates it)")


def import_cards(anki: Anki, proj: Project, csv_path: Path, dry: bool) -> None:
    rows = load(csv_path)
    tag = "[dry-run] " if dry else ""
    print(f"{tag}{len(rows)} cards from {csv_path.name}")
    if not rows:
        return
    if nodeck := [i for i, r in enumerate(rows, 1) if not r[DECK].strip()]:
        sys.exit(f"cards without a Deck: {nodeck}")

    # 1. note type
    model = proj["note_type"]
    model_exists = model in anki("modelNames")
    if model_exists:
        fields = anki("modelFieldNames", modelName=model)
        if missing := [f for f in FIELDS if f not in fields]:
            sys.exit(f"note type {model!r} exists but lacks fields {missing}. "
                     "Use another note_type name in flashcards.json.")
        print(f"note type {model!r}: exists (left unchanged)")
    else:
        templates = TEMPLATES + ([REVERSE] if proj["reverse_cards"] else [])
        print(f"note type {model!r}: create ({len(templates)} card type(s))")
        if not dry:
            anki("createModel", modelName=model, inOrderFields=FIELDS,
                 css=proj.css.read_text(encoding="utf-8"), cardTemplates=templates)

    # 2. decks
    existing = set(anki("deckNames"))
    wanted = sorted({r[DECK].strip() for r in rows})
    new_decks = [d for d in wanted if d not in existing]
    for d in new_decks:
        print(f"deck: create {d}")
        if not dry:
            anki("createDeck", deck=d)

    # 3. media (never overwrite: storeMediaFile replaces a same-named file by default)
    names = sorted({n for r in rows for col in r[:MEDIA + 1] for n in media_refs(col)})
    if names:
        have = set(anki("getMediaFilesNames", pattern=(proj["media_prefix"] or "") + "*"))
        up = 0
        for n in names:
            src = proj.media_dir / n
            if n in have:
                continue
            if not src.exists():
                sys.exit(f"missing media file {src}. Run validate.py.")
            up += 1
            if not dry:
                anki("storeMediaFile", filename=n, path=str(src.resolve()))
        print(f"media: {up} to upload, {len(names) - up} already in Anki (not overwritten)")

    # 4. notes
    notes = [{
        "deckName": r[DECK].strip(), "modelName": model,
        "fields": dict(zip(FIELDS, r[:4])),
        "tags": r[TAGS].split(),
        "options": {"allowDuplicate": False, "duplicateScope": proj["duplicate_scope"]},
    } for r in rows]
    if not model_exists:
        checks = [{"canAdd": True}] * len(notes)          # nothing can clash with a new note type
    else:
        try:
            checks = anki("canAddNotesWithErrorDetail", notes=notes)
        except RuntimeError:                               # older AnkiConnect
            checks = [{"canAdd": ok, "error": None if ok else "duplicate"}
                      for ok in anki("canAddNotes", notes=notes)]
    if dry:  # in a dry run the new decks don't exist yet; that's not a real problem
        checks = [{"canAdd": True} if not c["canAdd"] and n["deckName"] in new_decks else c
                  for n, c in zip(notes, checks)]
    todo = [n for n, c in zip(notes, checks) if c["canAdd"]]
    skipped = [(i, c.get("error")) for i, c in enumerate(checks, 1) if not c["canAdd"]]
    for i, why in skipped[:30]:
        print(f"skip #{i}: {why}")
    if len(skipped) > 30:
        print(f"... and {len(skipped) - 30} more skipped")
    print(f"{tag}notes: {len(todo)} to add, {len(skipped)} skipped (already in Anki)")
    if dry or not todo:
        return
    ids = anki("addNotes", notes=todo)
    failed = sum(1 for x in ids if x is None)
    print(f"added {len(ids) - failed} notes" + (f", {failed} failed" if failed else ""))


def main() -> None:
    proj = find_project()
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?", help=f"card CSV (default: {proj['approved_csv']})")
    ap.add_argument("--check", action="store_true", help="only test the connection")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen")
    ap.add_argument("--sync", action="store_true", help="only sync Anki with AnkiWeb")
    ap.add_argument("--update-style", action="store_true", help="push card.css to the note type")
    a = ap.parse_args()
    anki = Anki(proj["anki_connect_url"])

    if a.check:
        check(anki, proj)
    elif a.sync:
        anki("sync")
        print("synced with AnkiWeb")
    elif a.update_style:
        if proj["note_type"] not in anki("modelNames"):
            sys.exit(f"note type {proj['note_type']!r} doesn't exist yet")
        if not a.dry_run:
            anki("updateModelStyling", model={"name": proj["note_type"],
                                              "css": proj.css.read_text(encoding="utf-8")})
        print(f"{'[dry-run] ' if a.dry_run else ''}styling of {proj['note_type']!r} <- {proj.css.name}")
    else:
        path = Path(a.csv).resolve() if a.csv else proj.approved
        import_cards(anki, proj, path, a.dry_run)


if __name__ == "__main__":
    main()
