# Media: audio and images

## When to suggest what

| Topic | Good media | Usually skip |
|---|---|---|
| Language learning | Audio of the target-language side, on every speakable card. Pictures for concrete nouns (food, animals, objects). | Audio on grammar tables and English-only cards (tag them `no-audio`). |
| Programming, system design | Diagrams for architecture, request flows, data layouts, and trees and graphs. | Screenshots of code: put code in the card as HTML instead. |
| Medicine, biology, anatomy, chemistry | Labelled diagrams, structures, images of specimens. | Decorative pictures. |
| Geography | Maps, flags, landmark photos. | |
| History, art | Portraits, artworks, maps of events. | |
| Music, birdsong, accents | Short audio clips the user provides. | |
| Law, business, definitions | Usually nothing. | Stock images: they add noise. |

Media should carry information. If the card works the same without it, leave it out.

## Rules for all media files

- Keep files in `media/`, with bare names that start with the project's `media_prefix`
  (from flashcards.json). Anki keeps all media of all decks in one folder: a file called
  `diagram1.svg` from another deck would clash.
- Reference media from the Media field (`[sound:x.mp3]`, `<img src="x.svg">`). An image may
  also go inside Back.
- Keep files small: an SVG under about 50 KB, a photo under about 300 KB (resize it to 800 px
  with `sips -Z 800 file.jpg` on macOS, or ImageMagick `magick file.jpg -resize 800x800 file.jpg`).
  Use mp3 for audio.
- Never link to web URLs: cards must work offline and on the phone.
- validate.py reports missing files and names without the prefix.

## Audio with text-to-speech (tts.py)

`tts.py` voices one field of each card (default: Back) with the program set in the `tts` block
of flashcards.json, then adds `[sound:...]` to Media. It skips cards that already have audio,
cards tagged `no-audio` (configurable with `skip_tags`), `<small>` hints, multi-line backs
and very long texts. File names include a hash of the text and the command, so the same text
with the same voice is never made twice.

```json
"tts": {
  "command": ["say", "-v", "Anna", "-o", "{out}", "-f", "{text_file}"],
  "output_ext": "aiff",
  "field": "Back",
  "skip_tags": ["no-audio"],
  "max_chars": 200
}
```

In `command`: `{out}` = the file to write, `{text_file}` = a UTF-8 file holding the text,
`{text}` = the text itself. Prefer `{text_file}`: text that starts with `-` would otherwise be
read as an option. Set `"stdin": true` to pipe the text in instead. Output that isn't mp3 is
converted with **ffmpeg** (macOS: `brew install ffmpeg`, Windows: `winget install ffmpeg`,
Linux: the package manager). Without ffmpeg only mp3, wav, ogg and m4a output is accepted.

### Engines

Help the user pick one, then let them listen to 2-3 samples before you voice the whole deck.
Voice the field in the target language.

| Engine | Quality | Runs | Install | Note |
|---|---|---|---|---|
| macOS `say` | good | offline, macOS only | built in | List voices: `say -v '?' \| grep de_DE`. More voices: System Settings > Accessibility > Spoken Content. |
| Piper | good | offline, any OS | `python3 -m venv .venv-tts && .venv-tts/bin/pip install piper-tts`, plus a voice model | Voices are at huggingface.co/rhasspy/piper-voices (an `.onnx` file plus its `.onnx.json`). Check the license on each voice's model card. |
| edge-tts | very natural | online | `pip install edge-tts` | Sends the card text to Microsoft's online speech service, an unofficial use. Tell the user before choosing it. List voices: `edge-tts --list-voices`. |
| espeak-ng | robotic | offline, any OS | package manager | Good enough for checking pronunciation, not for listening practice. |

Command templates (adjust the voice and paths):

```json
"command": ["say", "-v", "Anna", "-o", "{out}", "-f", "{text_file}"], "output_ext": "aiff"
"command": [".venv-tts/bin/piper", "-m", "voices/de_DE-thorsten-medium.onnx", "-f", "{out}"], "stdin": true, "output_ext": "wav"
"command": ["edge-tts", "--voice", "de-DE-KatjaNeural", "-f", "{text_file}", "--write-media", "{out}"], "output_ext": "mp3"
"command": ["espeak-ng", "-v", "de", "-w", "{out}", "-f", "{text_file}"], "output_ext": "wav"
```

Piper's command-line flags differ between versions. Run `piper --help` and check its output
before you write the template. Put voice models in a folder such as `voices/`, and add the
`.venv-tts/` and `voices/` folders to `.gitignore`.

### What makes audio cards good

- Voice only the target-language utterance: one word, phrase or sentence per card.
- For `A / B` variants, voice the first form, or split them into two cards.
- Course notation such as optional letters (`de(n)`) or abbreviations should be spoken the
  way a native speaker says them. If needed, keep a cleaned spoken text in a project script.
- Tag grammar, rules, tables and English-only cards `no-audio`.

### Human recordings instead of TTS

Some languages have open pronunciation data: national dictionaries with open-data dumps, and
Wikimedia Commons or Lingua Libre (CC-licensed). Recordings of native speakers are better
than TTS when they exist. Check the license, use exact text matches only (never stitch
recorded words into a sentence), and fall back to TTS for the rest. This is project-specific:
write a small script in the project that downloads the matches into `media/` under prefixed
names and fills Media. Then run `tts.py` for the cards still without audio.

## Images and diagrams

### From the source
- Saved web pages: `extract_svgs.py` for inline SVG, or the `<page>_files/` folder (see sources.md).
- PDFs: ask the user to export the figure (a screenshot or the PDF app's export). Crop it to
  the figure only.

### Drawn by you (SVG)
Simple diagrams are often clearer than the source's: boxes and arrows, flows, timelines,
trees, layered stacks. Write them as SVG files in `media/`:

- Use `viewBox="0 0 W H"` with W ≤ 640, and no fixed width or height (the card scales it).
- Use `font-family="sans-serif"` and `font-size` ≥ 14. Use dark strokes and text on a
  transparent background: card.css adds a white backing, so it works in night mode too.
- Draw arrowheads with a `<marker>`. Keep each file under about 20 KB, with no embedded fonts
  or bitmaps.
- Label only what the card asks about. Every label in the picture should be readable on a phone.

After writing one, check it in the preview before the user reviews it.

### Label-the-picture cards
For "name the part" drills on one image, Anki's built-in **Image Occlusion** note type (Anki
23.10+) beats anything this CSV can do. Suggest it, and make those cards in Anki directly.
