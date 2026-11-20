# flashcards: an Anki card workflow for Claude Code

Give Claude Code your study material (a PDF chapter, a web article, your notes) and it turns
it into Anki flashcards with you, one section at a time. You see every card rendered as it
will look in Anki. You fix cards by number ("#3 shorter", "merge 4 and 5"). Only the cards
you approve go to Anki, in one command.

It works for any subject: language courses, interview prep, exams, hobbies. Language decks
can get spoken audio, and technical decks can get diagrams.

## How a session goes

1. You say what you're studying and where the material is. On the first run, Claude asks a
   few setup questions: deck name, Anki connection, and whether you want audio or images.
2. Claude reads one section and writes its cards to a staging file.
3. A live preview page shows the cards, numbered, looking like Anki. It has a quiz mode and
   a night mode, and it updates whenever a card changes.
4. You ask for changes in plain words, by number: `#3 shorter`, `delete 7`,
   `merge 4 and 5`, `move 6-8 to Verbs`, `add an example to #2`.
5. You say `ok` or `next`. The cards are approved, and the next section starts.
6. When you want: `add audio`, `import to Anki`, `sync`.

## Requirements

- [Claude Code](https://claude.com/claude-code)
- Python 3.9 or newer (macOS and most Linux systems have it; on Windows, install it from
  python.org). The scripts use only the standard library.
- **Recommended:** [Anki desktop](https://apps.ankiweb.net) with the **AnkiConnect** add-on
  (Tools > Add-ons > Get Add-ons…, code `2055492159`, then restart Anki). Without it you can
  still review cards in the preview, and import the CSV into Anki by hand.
- **Optional, for audio:** a text-to-speech program. macOS `say` is built in. Piper (offline,
  any OS) and edge-tts (online) also work. Claude helps you pick and set one up. Install
  `ffmpeg` too, to convert audio to mp3.

## Install

As a plugin (updates come with `/plugin marketplace update flashcards-skill`), inside Claude Code:

```
/plugin marketplace add akinali94/flashcards-skill
/plugin install flashcards@flashcards-skill
```

or from a terminal:

```
claude plugin marketplace add akinali94/flashcards-skill
claude plugin install flashcards@flashcards-skill
```

Or copy the skill by hand (no plugin system needed):

```
git clone https://github.com/akinali94/flashcards-skill
cp -r flashcards-skill/skills/flashcards ~/.claude/skills/flashcards
```

## Start a deck

```
mkdir german-a1 && cd german-a1
claude
> I want Anki cards for my German A1 course. The PDFs are in ~/Downloads/german.
```

Claude recognises flashcard requests by itself. You can also call the skill directly: type
`/flashcards:flashcards` with the plugin, or `/flashcards` with the manual copy.

## What a project folder looks like

```
german-a1/
  flashcards.json      settings: deck name, note type, media prefix, preview port, audio
  FLASHCARDS.md        project brief: your goal, sources and card rules (Claude keeps it current)
  card.css             card style, used by both the preview and Anki
  cards/review.csv     cards waiting for your OK
  cards/approved.csv   approved cards, ready for Anki
  media/               audio and images used by cards
  sources/             your PDFs, saved pages and notes (never changed by Claude)
  preview/             the generated preview pages
```

The CSVs are plain Anki import files, so your cards are never locked into this tool.

## Good to know

- **Nothing in Anki is ever deleted or overwritten.** The import adds new cards and skips
  ones already there. Media files with the same name are left alone.
- **Fixing a card after import:** edit it in Anki (Browse). Re-importing doesn't update it.
- **Phones:** cards reach AnkiDroid or AnkiMobile through AnkiWeb sync (`sync`, or the sync
  button in Anki).
- **Privacy:** your sources and cards stay on your machine. Online text-to-speech (edge-tts)
  sends card text to Microsoft. macOS `say`, Piper and espeak-ng run offline.
- **Copyright:** cards made from a paid course are for your own study. The project's
  `.gitignore` keeps `sources/` out of git. Think twice before publishing such a deck.
- **Windows:** if `python3` isn't found, Claude uses `python`.

## What's inside

```
.claude-plugin/          plugin and marketplace manifests
skills/flashcards/
  SKILL.md               the workflow Claude follows
  scripts/               init, validate, preview, approve, set_deck, anki_import, tts,
                         html_to_md, extract_svgs (plain Python, no dependencies)
  assets/card.css        default card style
  references/            card-writing guide, sources, media and Anki notes
```

You can run any script yourself, from inside a project folder:
`python3 -I <path-to-skill>/scripts/validate.py`. Each script explains its options with `--help`.
