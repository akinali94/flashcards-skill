# Writing good cards

The project's `FLASHCARDS.md` overrides anything here: it holds the rules this user agreed on.

## Every card

- **One idea per card.** If the back needs "and also…", split the card. A card the user
  fails is easy to fix, but a card with five facts is never really learned.
- **Front:** a question with one clear answer. **Back:** the short, direct answer.
  **Notes:** extra detail that helps the answer stick.
- **Ask why, how and what-if**, not only "what is". Ask "Why does X happen?", "What happens
  if…?", "X vs Y: when do you pick which?", "What's wrong with this code?". Keep plain
  definitions for the terms the rest builds on.
- **Lists:** don't ask for 7 items on one card. Make one card per item, or ask "Name 3 of…",
  or "Which of these is not…".
- **Your own words.** Rephrase the source; don't copy paragraphs. Short quotes are fine
  when the exact wording matters (a definition, a law, a famous line).
- **No invention.** Facts come from the source. You may add a fact you are confident about
  if it clearly helps, but mark that card `extra` in the chat report. If you are unsure,
  leave it out or ask. A missing card is better than a wrong one.

## The Notes field

Write 1-2 short sentences, like a good teacher's margin note. Pick what actually helps:

- Usage and context: when or where it applies, and with whom ("formal: strangers, work").
- A contrast with a look-alike ("`==` compares references; `equals` compares content").
- A memory hook: the literal meaning, a word breakdown, an origin, an analogy.
- A typical follow-up, reply, pitfall or interview trap.

An empty Notes field is better than a padded or generic one.

## Language-learning cards

- **Direction.** Front: the language the user knows. Back: the target language. For two-way
  practice, the project uses reversed cards (`reverse_cards: true` in flashcards.json).
  Never make a separate card for each direction.
- **Spelling.** Keep the course's spelling and forms exactly. Never "correct" them from
  memory. If a form looks wrong, ask, or check a dictionary and say so.
- **Register.** State formal vs informal on the front when it matters ("How are you?
  (informal)").
- **Split list cards.** Days, months, seasons, colours and numbers get one card per word.
  Then each card gets its own audio.
- **Grammar.** Make separate cards for grammar: conjugation tables, articles, word order,
  plural rules. Tag them `grammar no-audio`.
- **Hints.** Put a literal translation or hint on the back in `<small>…</small>`. Text-to-speech
  skips it.
- **Examples.** Dialog lines, example sentences and exercise sentences make good cards. Put
  the correct answer on the back.
- **Notes ideas:** gender and plural, irregular forms, pronunciation tips from the course,
  false friends.

## Tech and interview cards

- Phrase the front the way an interviewer would ask it.
- Keep code short (≤ 10 lines) and runnable in your head. "What does this print?" and
  "What's the bug?" cards work well.
- Show trade-offs ("When would you not use X?"), failure modes, and complexity.
- Use a diagram only when it carries the idea (architecture, flows). See media.md.

## HTML in fields

Fields are HTML, shown exactly like this in Anki and in the preview.

- Use `<b>` for the key term. Use `<br>` for line breaks, `<ul><li>` for short lists, and
  `<table>` for small paradigms.
- Inline code: `<code>…</code>`. Code blocks: `<pre><code>…</code></pre>`, with real
  newlines inside the quoted CSV field.
- Escape `<`, `>` and `&` inside code: `List&lt;String&gt;`, `a &amp;&amp; b`. If you don't,
  the browser eats `<String>` as an unknown tag. validate.py reports any unknown tag.
- Use `<small>` for hints and asides.

## CSV mechanics

The header (5 lines) must stay as is:

```
#separator:comma
#html:true
#columns:Front;Back;Notes;Media;Tags;Deck
#tags column:5
#deck column:6
```

- Quote every field. A `"` inside a field is written `""`.
- **Media:** empty unless the card has media (see media.md).
- **Tags:** lowercase and space-separated, with `::` for hierarchy (`verbs::irregular`,
  `jvm::gc`). Don't add source or priority tags unless the user wants them.
- **Deck:** one sub-deck per study unit (chapter section, article, topic), written as a short
  name (`Greetings`) or the full path. Avoid micro-decks with 3 cards.

## Examples

```
"Why can't a Java class extend two classes?","The <b>diamond problem</b>: if both parents define the same method, it's ambiguous which one the child inherits.","Interfaces allow it: two clashing <code>default</code> methods must be overridden, and <code>A.super.m()</code> picks one.","","java::oop","Core::OOP"
"What does this print?<pre><code>List&lt;Integer&gt; a = List.of(1, 2);
a.add(3);</code></pre>","Nothing: it throws <code>UnsupportedOperationException</code>, because <code>List.of</code> returns an immutable list.","Use <code>new ArrayList&lt;&gt;(List.of(1, 2))</code> when you need to add.","","java::collections","Core::Collections"
"Good morning","Guten Morgen<br><small>lit. good morning</small>","Used until about 11 a.m. Then <i>Guten Tag</i>.","","greetings","Unit 1::Greetings"
"to go (I go, you go [informal], he goes)","gehen: ich gehe, du gehst, er geht","Regular: stem <b>geh-</b> + -e, -st, -t.","","grammar no-audio verbs","Unit 2::Verbs"
```
