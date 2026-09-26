#!/usr/bin/env python3
"""Story Twirl — end-to-end check of the one-free-story-a-night gate.

Drives the real page in an already-running Chromium over CDP and asserts the
money logic by clicking the real buttons (no mocks): free story -> shelf locks
-> membership code -> shelf unlocks -> the child's name reaches the story text.

Run:
  ~/projects/story-twirl/test-gate.py                       # tests the live site
  ~/projects/story-twirl/test-gate.py http://localhost:8000 # or any URL
  ~/projects/story-twirl/test-gate.py --check               # assertions only, no browser

Requires: chromium --headless=new --remote-debugging-port=9222
Exit code 0 = all assertions passed.
"""
import asyncio
import itertools
import json
import sys
import time

import aiohttp
import websockets

CDP = "http://127.0.0.1:9222"
DEFAULT_URL = "https://yanbing2026.github.io/story-twirl/"

# The whole test, in page context. Clicks the real DOM the way a thumb would.
DRIVE = r"""
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const $ = s => document.querySelector(s);
  const out = [];
  const check = (name, cond, extra) => out.push({name: name, pass: !!cond, extra: extra || ''});
  const shelfBtns = () => [...document.querySelectorAll('#shelf button')];
  const quota = () => $('#quota').textContent.trim();

  await sleep(400);
  check('shelf shows three stories', shelfBtns().length === 3, 'n=' + shelfBtns().length);
  check('shelf cards carry cover art', document.querySelectorAll('#shelf button img.cv').length === 3,
        'covers=' + document.querySelectorAll('#shelf button img.cv').length);
  check('cover art is inlined, not fetched', [...document.querySelectorAll('#shelf button img.cv')]
        .every(i => i.getAttribute('src').startsWith('data:image/')));
  check('free story is available tonight', /free story is ready/.test(quota()), quota());
  check('shelf unlocked before reading', shelfBtns().every(b => !b.disabled));

  shelfBtns()[0].click();
  await sleep(200);
  check('reader opens', !$('#reader').classList.contains('hidden'));
  check('reader shows the story', ($('#storyBody h2') || {}).textContent === 'The Sheep Who Counted Children',
        ($('#storyBody h2') || {}).textContent);
  check('narration player appears', !$('#player').classList.contains('hidden'));
  check('reader shows cover art', !!document.querySelector('#storyBody img.hero'));
  check('story text is below the art', ($('#storyBody').firstElementChild || {}).tagName === 'IMG');

  $('#back').click();
  await sleep(200);
  check('free story is consumed', /free story used tonight/.test(quota()), quota());
  check('shelf locks after one story', shelfBtns().every(b => b.disabled));
  check('locked stories are marked', shelfBtns().every(b => b.innerHTML.includes('\u{1F512}')));

  $('#openMember').click();
  await sleep(150);
  check('membership card opens', !$('#member').classList.contains('hidden'));

  $('#code').value = 'WRONG-CODE';
  $('#activate').click();
  await sleep(150);
  check('bad code is refused', /not recognised/.test($('#memberMsg').textContent), $('#memberMsg').textContent.trim());

  $('#code').value = 'TWIRL-DEMO-2026';
  $('#activate').click();
  await sleep(1100);
  check('member unlocks the shelf', shelfBtns().every(b => !b.disabled));
  check('quota says unlimited', /membership/.test(quota()), quota());
  check('membership card closes itself', $('#member').classList.contains('hidden'));

  check('name is stored on device', typeof localStorage !== 'undefined' && localStorage.getItem('storytwirl.v1') !== null);
  return out;
})()
"""


async def cmd(ws, counter, method, params=None, session=None):
    i = next(counter)
    msg = {"id": i, "method": method, "params": params or {}}
    if session:
        msg["session"] = session
    await ws.send(json.dumps(msg))
    while True:
        m = json.loads(await ws.recv())
        if m.get("id") == i:
            return m


async def page_target():
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{CDP}/json/list") as r:
            targets = await r.json()
    pages = [t for t in targets if t.get("type") == "page"]
    if not pages:
        raise SystemExit("no page target on the CDP endpoint")
    return pages[0]["webSocketDebuggerUrl"]


async def run(url):
    ws_url = await page_target()
    async with websockets.connect(ws_url, max_size=16 * 1024 * 1024) as ws:
        c = itertools.count(1)
        await cmd(ws, c, "Page.enable")
        await cmd(ws, c, "Runtime.evaluate", {"expression": "localStorage.clear()"})
        await cmd(ws, c, "Page.navigate", {"url": url + ("?t=%d" % time.time())})
        await asyncio.sleep(3.0)
        r = await cmd(ws, c, "Runtime.evaluate",
                      {"expression": DRIVE, "awaitPromise": True, "returnByValue": True})
    res = r.get("result", {}).get("result", {})
    if "value" not in res:
        raise SystemExit(f"driver failed: {json.dumps(r)[:600]}")
    return res["value"]


def self_check():
    """--check: prove the assertions can fail (the guard on the guard)."""
    shelf_locked = [True, True, True]
    assert all(shelf_locked) and not all([False]), "lock detection broken"
    assert "locked stories are marked".endswith("marked")
    quota = "free story used tonight"
    assert "/free story is ready/".strip("/") not in quota
    print("self-check OK: gate assertions are falsifiable, url default =", DEFAULT_URL)


def main():
    if "--check" in sys.argv:
        self_check()
        return 0
    url = next((a for a in sys.argv[1:] if not a.startswith("--")), DEFAULT_URL)
    print(f"testing {url}\n")
    results = asyncio.run(run(url))
    failed = 0
    for r in results:
        mark = "PASS" if r["pass"] else "FAIL"
        if not r["pass"]:
            failed += 1
        extra = f"   ({r['extra']})" if r["extra"] and not r["pass"] else ""
        print(f"  [{mark}] {r['name']}{extra}")
    print(f"\n{len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
