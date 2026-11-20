# Anki: AnkiConnect, note type, manual import, sync

## Why AnkiConnect (recommend it)

AnkiConnect is a free Anki add-on that lets programs talk to Anki desktop. With it,
`anki_import.py` does a whole import in one command: it creates the note type and decks,
uploads media, adds the new cards, skips the ones already there, and can sync to AnkiWeb.
Without it, the user imports the CSV by hand and copies media files themselves.

### Setup (once)
1. Install Anki desktop: https://apps.ankiweb.net.
2. In Anki: **Tools > Add-ons > Get Add-ons…**, enter `2055492159`, click OK, restart Anki.
3. Keep Anki open while importing. Check the connection with `S/anki_import.py --check`.

AnkiConnect listens on `http://localhost:8765` and only works with Anki desktop, not AnkiWeb
or the phone apps. Cards reach the phone through sync, which needs a free AnkiWeb account.

### Troubleshooting
- **"not reachable":** Anki is closed, the add-on is not installed, or Anki wasn't restarted
  after installing it. If the port was changed in the add-on's config, update
  `anki_connect_url` in flashcards.json.
- **Slow or hanging on macOS while Anki is in the background (App Nap).** Run these once,
  then restart Anki:
  ```
  defaults write net.ankiweb.dtop NSAppSleepDisabled -bool true
  defaults write net.ichi2.anki NSAppSleepDisabled -bool true
  defaults write org.qt-project.Qt.QtWebEngineCore NSAppSleepDisabled -bool true
  ```
- **"note type … lacks fields":** a note type with that name exists with different fields.
  Set another `note_type` in flashcards.json. Don't change the existing one.
- **Cards skipped as duplicates:** a note with the same Front is already in that deck. Set
  `"duplicate_scope": "collection"` to check the whole collection instead.

## What the import creates

- **Note type** (`note_type` in flashcards.json): fields `Front`, `Back`, `Notes`, `Media`,
  with the project's `card.css` as styling. It has one card type, plus a reversed one when
  `reverse_cards` is true at the first import (changing that flag later doesn't touch an
  existing note type).
  - Front template: `<div class="front">{{Front}}</div>`
  - Back template: front, `<hr id="answer">`, `<div class="back">{{Back}}</div>`, then
    Notes and Media blocks when they aren't empty.
- **Decks:** every deck named in the Deck column, created if missing.
- **Media:** files referenced by the cards that Anki doesn't have yet. Same-named files
  already in Anki are left alone.
- **Notes:** the cards of `cards/approved.csv`, with their tags.

The import never deletes or modifies notes. Re-running it is safe: existing cards are
skipped. To fix a card that is already in Anki, edit it in Anki (Browse). Re-importing
doesn't update it.

**Style changes:** edit `card.css` (the preview shows the result immediately), then run
`S/anki_import.py --update-style`. This restyles every card of that note type.

## Manual import (without AnkiConnect)

Anki 2.1.55 and later reads the CSV's header lines (separator, HTML, columns, tags column,
deck column).

1. Make the note type once: **Tools > Manage Note Types > Add > Add: Basic**, and give it
   the `note_type` name. Under **Fields**, keep Front and Back and add `Notes` and `Media`.
   Under **Cards**, paste the templates above and the contents of `card.css` as Styling.
2. **File > Import…** > `cards/approved.csv`. Choose that note type. Deck: *from the file*
   (the Deck column). Check that the field mapping is Front, Back, Notes, Media, then Tags.
   Import.
3. Copy the files from `media/` into Anki's media folder. Never overwrite files already there.
   Ask the user before copying.
   - macOS: `~/Library/Application Support/Anki2/<profile>/collection.media/`
   - Windows: `%APPDATA%\Anki2\<profile>\collection.media\`
   - Linux: `~/.local/share/Anki2/<profile>/collection.media/`
4. Run **Tools > Check Media** in Anki to confirm nothing is missing.

To import only new cards next time, import a CSV that holds only them. Anki also flags
duplicates during import.

## Sync

`S/anki_import.py --sync` syncs Anki desktop with AnkiWeb. Pressing **Y** or the sync button
in Anki does the same. Then sync the phone app.
