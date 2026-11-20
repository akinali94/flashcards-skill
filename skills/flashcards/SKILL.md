---
name: flashcards
description: Turn study material (PDFs, web pages, URLs, notes, pasted text) into Anki flashcards through a review loop. Cards are drafted into a staging CSV, shown in a live Anki-like HTML preview, changed by card number, approved, and imported into Anki with AnkiConnect. Optional audio (text-to-speech, e.g. for language learning) and images or diagrams. Use when the user wants to make, review, edit, approve or import flashcards or Anki cards, study a topic with spaced repetition, or keeps working in a folder that has a flashcards.json.
allowed-tools: Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/init.py *), Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/validate.py *), Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/preview.py *), Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/approve.py *), Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/set_deck.py *), Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/anki_import.py *), Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/html_to_md.py *), Bash(python3 -I ${CLAUDE_SKILL_DIR}/scripts/extract_svgs.py *), Bash(python -I ${CLAUDE_SKILL_DIR}/scripts/init.py *), Bash(python -I ${CLAUDE_SKILL_DIR}/scripts/validate.py *), Bash(python -I ${CLAUDE_SKILL_DIR}/scripts/preview.py *), Bash(python -I ${CLAUDE_SKILL_DIR}/scripts/approve.py *), Bash(python -I ${CLAUDE_SKILL_DIR}/scripts/set_deck.py *), Bash(python -I ${CLAUDE_SKILL_DIR}/scripts/anki_import.py *), Bash(python -I ${CLAUDE_SKILL_DIR}/scripts/html_to_md.py *), Bash(python -I ${CLAUDE_SKILL_DIR}/scripts/extract_svgs.py *)
---

# Flashcards

You turn the user's study material into Anki cards, one study unit at a time. Nothing reaches
the deck until the user has seen the card rendered and said OK. The loop:

1. Read one unit of the source (a chapter section, an article, a topic).
2. Write its cards to `cards/review.csv`.
3. Run `validate.py`. The live preview updates by itself.
4. Give a short `# | topic` table in chat. The user asks for changes by card number.
5. On "ok" / "next", run `approve.py`. The cards move to `cards/approved.csv`.
6. When the user asks: add media, then import into Anki with `anki_import.py`.

Talk to the user in their language. Write cards in the language agreed at setup.

## Scripts

All scripts are in `${CLAUDE_SKILL_DIR}/scripts/`. They need only Python 3.9+ (standard
library). Run them from the project folder (the one with `flashcards.json`; subfolders also
work) as `python3 -I ${CLAUDE_SKILL_DIR}/scripts/<script>.py ...`. If `python3` is not found
(Windows), use `python`. Below, `S` stands for `python3 -I ${CLAUDE_SKILL_DIR}/scripts`.

| Command | What it does |
|---|---|
| `S/init.py --name "German A1" --deck-root "German::A1" [--reverse]` | New project. Creates only missing files. |
| `S/validate.py [csv]` | Columns, empty fields, duplicates, deck, raw `<` in code, media files. Prints cards per deck. |
| `S/preview.py --serve` | Live preview of `cards/review.csv` (run in the background). `S/preview.py cards/approved.csv` builds one page. |
| `S/approve.py [#N ...]` | Move cards (all, or the given numbers) from review to approved. Skips duplicates. |
| `S/set_deck.py "Unit 2::Verbs" [#N ...]` | Set the sub-deck under the root (default: every card in review). |
| `S/anki_import.py --check` / `--dry-run` / (no flag) / `--sync` / `--update-style` | AnkiConnect: test, plan, import approved, sync, push card.css. |
| `S/tts.py --dry-run` / `S/tts.py` | Text-to-speech audio into Media. Needs a `tts` block in flashcards.json. |
| `S/html_to_md.py page.html out.md --stop "TEXT"` | Article text of a saved web page as Markdown. |
| `S/extract_svgs.py page.html media --prefix <media_prefix>` | Diagram SVGs embedded in a saved web page. |

Card numbers accept ranges: `1-5 8 12`. Numbers are positions in the file, so they shift after
a delete, merge or approve. The preview always shows the current numbers.

## At the start of every session

- If `flashcards.json` exists here or in a parent folder: read `FLASHCARDS.md` (the project
  brief), run `validate.py`, and look at what is waiting in `cards/review.csv`. Start the
  preview server (see the review loop) and continue where the user left off.
- If there is no `flashcards.json`, run **Setup** first, even when the user already gave a
  source. Setup is short, and it decides how every card is written.

## Setup (new project)

Gather these in as few questions as possible. Use AskUserQuestion for the choices. Skip any
question the user has already answered.

1. **Topic, goal and sources.** What they study and why (exam, job interview, language
   level, hobby), and the material (files, links, notes). Ask them to put files in
   `sources/` after init.
2. **Deck name.** Suggest a root deck such as `German::A1` or `Interview::System Design`.
   Each study unit becomes a sub-deck under it.
3. **Anki connection.** Recommend AnkiConnect, because it lets you import with one command,
   upload media, create decks, skip duplicates and sync. Setup takes 2 minutes:
   - Install Anki desktop (https://apps.ankiweb.net).
   - In Anki: Tools > Add-ons > Get Add-ons, enter code `2055492159`, then restart Anki.
   Then run `anki_import.py --check` to confirm it works. The alternatives are manual CSV
   import (`references/anki.md`) or no Anki yet, using the preview's quiz mode. Users can
   switch later.
4. **Media.** Ask whether they want media, and tailor the suggestion to their topic:

   | Topic | Suggest |
   |---|---|
   | Language learning | Audio of the target-language side (text-to-speech, offline or online). Optionally pictures for concrete nouns. Ask about two-way cards (`--reverse`). |
   | Programming, system design, tech interviews | Usually no media: code goes in the card as HTML. Diagrams (SVG) for architecture, flows and data structures, taken from the source or drawn by you. |
   | Medicine, biology, anatomy, chemistry | Labelled diagrams and images. Anki's own Image Occlusion suits "label the picture" cards. |
   | Geography, history, art | Maps, flags, pictures of places and artworks. |
   | Music, birdsong, accents | Audio clips the user provides. |
   | Law, business, definitions, exam facts | No media. |

   If they choose audio, set up the `tts` block (`references/media.md`). Let them hear 2-3
   samples, and agree on a voice before generating in bulk.
5. Run `init.py` with the name and deck root (`--reverse` for two-way cards). Then fill in
   `FLASHCARDS.md` with what you learned: goal, sources in priority order, card rules, deck
   structure, media, and Anki connection.
6. Offer to add `"Edit(cards/**)"` and `"Write(cards/**)"` to `permissions.allow` in
   `.claude/settings.local.json`, so card edits don't prompt each time. Do it only if the
   user says yes. Keep their existing settings when you do.

## Writing cards

- Before the first batch of a session, read `references/card-writing.md` and the project's
  `FLASHCARDS.md`. Read `references/sources.md` when a source type is new to you.
- Do one study unit per batch, usually 10-30 cards. Cover what matters in the unit. Don't
  pad it.
- Write cards **only** into `cards/review.csv`, with the Write or Edit tools. Never paste
  card tables into chat. Never write cards through heredocs or inline Python, because the
  user would have to approve each command.
- The CSV format is exact: keep the 5 header lines, quote every field, and write a `"` inside
  a field as `""`. The columns are `Front;Back;Notes;Media;Tags;Deck`. The Deck column can
  hold the sub-deck alone (`Verbs`); approve puts it under the root.
- Run `validate.py` and fix every error before you report.

## The review loop

1. Run `validate.py` after every change to `cards/review.csv`.
2. **Preview.** Start `preview.py --serve` once with `run_in_background`, read its `Serving:`
   line, and give the user the URL. In VS Code they can open it with Cmd/Ctrl+Shift+P >
   "Simple Browser: Show". The page reloads by itself when the CSV or card.css changes.
   Restart the server only if `preview.py` itself changed. Don't start a second server while
   one is running. Stop it only by its own task, never with `pkill`, because other projects
   may run a script with the same name.
3. **Report in chat** with a short table: `# | topic` (add the deck when the batch spans
   several). Below it, list cards with facts not from the source (tag them `extra`) and
   anything you are unsure of. Don't repeat the card text, since the preview shows it.
4. **Changes by number.** The user writes things like "#3 shorter", "merge 4 and 5",
   "delete 2", "move 6-8 to Verbs", "split 9". Edit `cards/review.csv` (use `set_deck.py`
   for deck moves), validate, and say in 1-3 lines what changed.
5. **Approve.** On "ok", "good", "next" or "approve", run `approve.py`, with numbers if they
   approved only some. Don't ask for confirmation. Then start the next unit's batch.
6. **Record decisions.** When the user sets a lasting rule ("no source tags", "always add an
   example sentence"), add it with today's date to the Decisions log in `FLASHCARDS.md`, and
   follow it from then on.

## Media

- Files live in `media/` with bare names starting with the project's `media_prefix`. Anki
  keeps all media of all decks in one folder, so the prefix prevents name clashes. Put
  `[sound:<file>]` or `<img src="<file>">` in the Media field. An image may also sit in the
  Back. Never link to images on the web: Anki works offline.
- Images can come from the source (`extract_svgs.py`, or the `<page>_files/` folder saved
  with the page), from the user, or from you: write a simple SVG diagram yourself. See
  `references/media.md`.
- Audio comes after approval and before import. Run `tts.py --dry-run`, show the counts,
  then run `tts.py`. Cards tagged `no-audio` are skipped. If the user wants to hear cards
  before approving them, use `tts.py --csv cards/review.csv`. `tts.py` runs the program set
  in `flashcards.json`, so it is deliberately left out of this skill's pre-approved tools,
  and Claude Code may ask the user to approve each run.

## Importing into Anki

Import only when the user asks. Run `anki_import.py --check`, then `--dry-run`, and report
the plan: new note type or decks, media uploads, notes to add and skip. Then run
`anki_import.py`. Afterwards, offer `anki_import.py --sync`, which syncs AnkiWeb so the
cards reach the user's phone.

- The script never deletes or changes existing notes, and never overwrites media. Never
  work around this through other AnkiConnect calls.
- Notes already in Anki are skipped (same Front in the same deck). A card fixed after import
  must be edited in Anki's Browse window: re-importing does not update it.
- If `note_type` exists in Anki with other fields, choose a new `note_type` name in
  `flashcards.json`. Never modify the user's existing note types.
- To change the look of the cards: edit the project's `card.css` (the preview shows the
  result), then run `anki_import.py --update-style` after asking. It restyles every card of
  that note type.
- If AnkiConnect is unreachable, the script prints the setup steps; pass them on. For manual
  import, follow `references/anki.md`.

## Rules

- Never change or delete files in `sources/`. They are the user's material.
- Put things in your own words. Don't copy long passages from sources.
- Never invent facts, word forms or APIs. If you are unsure, say so in the report, or leave
  it out.
- Keep `flashcards.json` valid JSON, since every script reads it.

## Reference files

- `references/card-writing.md`: how to write good cards (general, language, tech), CSV and
  HTML details, examples.
- `references/sources.md`: PDFs, URLs, saved web pages, Markdown and Notion exports.
- `references/media.md`: when to suggest media, TTS engines and their config, images and
  diagrams.
- `references/anki.md`: AnkiConnect setup and troubleshooting, the note type, manual import,
  syncing.
