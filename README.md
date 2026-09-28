# Story Twirl

A story a night, read aloud by the device itself.

- **One free story every night.** Want more in one night? That is what membership is for.
- **Narration is offline.** In the browser it uses the device's `speechSynthesis` voices;
  inside the Android app it uses the platform's offline `TextToSpeech` engine. No API keys,
  no server, no accounts.
- **One file.** `index.html` is the entire product — the website you are looking at and the
  exact asset that gets bundled into the APK. It is **generated** from `stories.json` by
  `scripts/build-site.py` (which also writes `/stories/<slug>/`, `sitemap.xml`, `robots.txt`) —
  edit the data or the generator, never the generated file. See `AGENTS.md`.

## Layout

```
index.html                 landing page: what this is, for whom, the story wall
app/index.html             the reader app (the whole web app, in one file)
404.html                   a not-found page that offers a way back
```

`/` is what a parent lands on and what a search engine or a chat preview reads.
`/app/` is the app itself, which needs JavaScript. They are generated from the
same `stories.json`, so the two can never disagree about what exists.

The Android shell lives in `~/projects/StoryTwirl` and pulls this file in as its asset:

```bash
bash ~/projects/StoryTwirl/scripts/sync-web-asset.sh ~/projects/story-twirl/app/index.html
```

That script is the only thing keeping the site and the app in sync — run it before every APK
build so the two can never drift apart.

## The bridge contract (site ↔ app)

The HTML narrates through one function and falls back cleanly:

```js
const Bridge = (typeof AndroidBridge !== 'undefined' && AndroidBridge && AndroidBridge.isNative)
  ? AndroidBridge : null;
```

- inside the APK: `AndroidBridge.speak(text, lang)`, `AndroidBridge.stop()` → native offline TTS
- in any browser: `speechSynthesis` (no bridge, no error)

Nothing else in `app/index.html` needs to change for the app.

## How the gate works (and its honest ceiling)

`localStorage` holds `{member, day, used, name}`. A member reads anything; everyone else gets
**one story per calendar day**, and the shelf locks until midnight. The name a parent types
stays on the device and is only substituted into the story text.

A local gate is bypassable by anyone who clears site data. It exists to be fair, not to be
DRM. Real enforcement means checking a purchased code server-side once and storing a signed
licence — that arrives with the payment provider, not with the prototype.

## Privacy

One optional first name. No accounts, no analytics, no cookies, no network calls. The Android
build ships **without the INTERNET permission**, so it literally cannot phone home.

## What is still missing before this sells

1. Payment + licence issuance (provider decision: Stripe / Gumroad / Paddle for the web,
   Play Billing if it ever goes to the Play Store).
2. A story pipeline: drafts generated, a human-grade read-aloud pass, then publish — the
   shelf is three stories; a nightly habit needs dozens.
3. Artwork for the store listing (optional: the product is voice + text, so this is
   packaging, not core).
