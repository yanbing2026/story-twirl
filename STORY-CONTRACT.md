# Story Twirl — story contract (v2)

Bedtime stories for ages 3–6, read aloud by a machine in a dark room.
Every word will be HEARD, never seen. Write for the ear.

## The one rule that matters
A parent reads this at 8pm to a child who is already half asleep. It must be
soothing, gentle, and safe, and it must end. Nothing scary, nothing sad that
doesn't resolve, no tension that hangs.

## Hard requirements (a checker will verify these)

1. **4–5 minutes** ≈ **22 to 32 paragraphs**. Each paragraph is 1–3 sentences.
2. **The last paragraph is exactly `THE END.`** — on its own paragraph.
3. **English only.** No Chinese, no emoji, no markdown, no asterisks, no headings.
4. **Plain British English.** Contractions are fine and encouraged ("didn't", "it's").
   No long words a 4-year-old can't picture.
5. **Placeholders are allowed but must be natural.** Use `{{name}}` for the child and
   `{{namePos}}` for the possessive (e.g. `{{namePos}} boots`). If the story works
   better with a fixed hero, don't use them at all. At most one story in three needs a name.
6. **A real fact.** `lesson.fact` must be a true, checkable, delightful fact about the
   real world. If you are not certain it is true, pick a different fact.
7. **A question, not a lesson.** `lesson.ask` is one question a parent can ask after
   the lights are off. It is about the child's own life, not about the story's facts.
   Never ask the child to perform or explain.

## Shape (this is what makes it work)

- **Open:** two or three short paragraphs of place and time. It is evening. Name the
  light, the air, the quiet. The listener needs to lie down inside the scene in ~20 seconds.
- **Turn 1:** the character wants something small and ordinary.
- **Turn 2 (the trouble):** one misunderstanding, one small failure, one thing that
  doesn't work. Keep it SMALL. Nobody is hurt. Nobody is in danger. A lost sock, a
  closed door, a too-loud voice. Never: a hospital, a funeral, a monster under the bed,
  a child lost in the dark, cruelty, or anything that would wake a sleeping child up.
- **Turn 3 (the change):** the character tries a different way, or notices something
  they hadn't seen. This is the whole point of the story — the small idea that lands
  quietly.
- **Landing:** two or three warm paragraphs that bring everyone back down. Slow the
  sentences down. Make the last real sentence sleepy.

## Voice

Look at the three existing stories (`stories.json` — the sheep, the puddle, the sock).
Match them. Some of their signatures:

- A person or animal states something plainly and a bit too seriously, and the reader
  is not told it is funny.
- Objects get a point of view only if the object has a real reason to want something
  (a puddle holding the sky, a sock that cannot be quiet).
- Sound words are written as words: SPLASH. squelch. click.
- The wise character is wrong, or nearly wrong, and the child is the one who figures it out.
- Around 5–8% of paragraphs are a single short sentence on its own: "Nothing happened."
  "So he jumped." Use this for rhythm. Not more than that.

## What to avoid

- Moralising. The child should notice the idea, not be told it.
- Any "and then they learned that…" paragraph.
- Rhyme throughout. A few rhyming pairs are fine; a full rhyming story is a
  different product.
- Complicated nouns in a row. Two is fine, three is a tongue-twister at 4.
- Sleepwords, baby talk, or a silly voice. The narration is a calm adult voice.
- Any character who dies, is ill, or is left alone in the dark.
- Meta-jokes about the app, the code, membership, or the internet.

## Output format

Return ONLY a JSON array, no prose, no code fence. Each object:

```json
{
  "id": "short-lowercase-kebab",
  "slug": "the-title-in-kebab-case",
  "title": "Title Case Title",
  "blurb": "One line, under 70 characters. Sets up the turn without spoiling it.",
  "minutes": 4,
  "cover": "img/cover-<id>.webp",
  "lesson": {
    "ask": "One question for afterwards, ending in a question mark.",
    "fact": "One true, specific, surprising fact. One or two sentences."
  },
  "body": ["Paragraph one.", "Paragraph two.", "THE END."]
}
```

- `minutes` is 4 or 5. It should match the paragraph count honestly.
- `id` must be unique and must be 2–5 words.
- `cover` is just the expected path. **You do not create the image** — the art is
  made separately. Just name it `img/cover-<id>.webp`.
- `blurb` examples that work: "A sheep gets the job backwards — and it works."
  "A new sock arrives. The sock has opinions."
