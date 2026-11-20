# Reading sources

Source files belong in the project's `sources/` folder. Read them, but never change or delete
them. `sources/README.md` is the folder's note to the user, not study material.
Work one study unit at a time: read a section, write its cards, review, approve, move on.

## Slides (PowerPoint, Keynote, Google Slides)

Ask the user to export the deck to PDF, then treat it like any PDF. Look at the slide images
as well as the text, because slides carry much of their meaning in diagrams and layout.
Speaker notes don't survive a normal export. If the notes matter, ask for an export that
includes them (PowerPoint: "Notes Pages" layout).

## PDF (course books, slides, study guides)

- Read the PDF with the Read tool, using `pages` (at most 20 pages per call). For a big book,
  first read the table of contents and agree on the order of units with the user.
- Look at the page images, not only the text. Tables, speech bubbles, diagrams and exercise
  boxes often hold content that text extraction misses or scrambles.
- Section headings make good sub-deck names (`3-2 Counting beyond 10`, `Chapter 4::Joins`).
- For exercises, write the card with the correct answer on the back. If the PDF has a
  solutions section, use it. If not, solve the exercise and mark uncertain answers in the report.

## Web page by URL

- Fetch the URL. Turn the page into cards in your own words: the interview-relevant or
  exam-relevant points, with code where it helps.
- If the fetch fails or the content is behind a login, ask the user to save the page into
  `sources/`. In a browser: File > Save Page As > "Webpage, Complete".

## Saved web page (.html)

1. Text: `S/html_to_md.py "sources/Page.html" sources/page.md`. Look at the end of the
   output. If comments, "related articles" or page controls got in, find the first block that
   isn't article text and rerun with `--stop "that exact text"` (repeatable). If the output is
   empty or starts too late, rerun with `--start none`.
2. Inline diagrams: `S/extract_svgs.py "sources/Page.html" media --prefix <media_prefix>`.
   Files are named after the caption under each diagram.
3. Diagrams saved as separate files: browsers put images in `sources/Page_files/`. Copy the
   ones a card needs into `media/` under a prefixed name (`<media_prefix>sharding.svg`).
   Skip icons and logos.

## Markdown, Notion or Obsidian exports, plain notes

- Read the files directly. Notion export names end in a hash
  (`Spring Security 397c0f….md`), and images sit in a folder with the same name.
- The user's own notes come first, because they show what the user found important. Ask
  before using AI-generated pages, roadmaps or study plans from the same export.
- Notes already in question-and-answer form: keep the user's wording where it works. Fix
  only the clarity and split multi-idea answers.

## Pasted text and "make cards about X"

- Pasted text: treat it like a source section.
- No source at all ("make cards about Kubernetes networking"): agree on a scope first and
  propose a list of units. Write from well-established knowledge only, and mark the batch as
  not from a source in the report. Suggest a source the user can check against.

## Copyright

Decks for personal study are fine. Rephrase; don't copy long passages. Warn the user before
they publish a deck or a repo made from a paid course or book. Keep `sources/` out of public
repos (`.gitignore`).
