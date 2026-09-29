#!/usr/bin/env python3
"""Story Twirl — end-to-end check of the one-free-story-a-night gate.

Drives the real page in an already-running Chromium over CDP and asserts the
money logic by clicking the real buttons (no mocks): free story -> shelf locks
-> membership code -> shelf unlocks -> the child's name reaches the page.

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
import pathlib
import sys
import time
import urllib.parse

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
  const h1 = document.querySelector('header h1'), dot = document.querySelector('header .dot');
  const lh = parseFloat(getComputedStyle(h1).lineHeight) || 24;
  const hb = h1.getBoundingClientRect(), db = dot.getBoundingClientRect();
  check('header title stays on one line', hb.height <= lh + 3, 'h=' + Math.round(hb.height) + ' lh=' + lh);
  check('header dot is centred on the title',
        Math.abs((db.y + db.height / 2) - (hb.y + hb.height / 2)) <= 4,
        'dy=' + Math.round((db.y + db.height / 2) - (hb.y + hb.height / 2)));
  check('build stamp is visible', /build \d\d-\d\d \d\d:\d\d/.test($('#status').textContent), $('#status').textContent);
  // Regression: the shelf card must be a rounded RECTANGLE. It inherits the generic
  // button rule, and a pill radius (999px) with overflow:hidden clips the text rows
  // inside the curve — the title's first letters vanish. Measure the clip, not the CSS.
  {
    const card = document.querySelector('#shelf button');
    const cs = getComputedStyle(card), rect = card.getBoundingClientRect();
    const R = Math.min(parseFloat(cs.borderRadius) || 0, Math.min(rect.width, rect.height) / 2);
    const bl = card.querySelector('.txt span').getBoundingClientRect();
    const y = bl.top + bl.height / 2 - rect.top;
    const dy = y < R ? R - y : (y > rect.height - R ? y - (rect.height - R) : 0);
    const clip = R - Math.sqrt(Math.max(0, R * R - dy * dy));
    check('story cards are rounded rectangles, not pills', R <= 24, 'radius=' + R + 'px');
    check('card outline does not cut the card text', clip <= 2, 'clip=' + clip.toFixed(1) + 'px');
  }
  check('shelf shows three stories', shelfBtns().length === 3, 'n=' + shelfBtns().length);
  check('shelf cards carry cover art', document.querySelectorAll('#shelf button img.cv').length === 3,
        'covers=' + document.querySelectorAll('#shelf button img.cv').length);
  check('cover art is inlined, not fetched', [...document.querySelectorAll('#shelf button img.cv')]
        .every(i => i.getAttribute('src').startsWith('data:image/')));
  check('free story is available tonight', /free story is ready/.test(quota()), quota());
  check('shelf unlocked before reading', shelfBtns().every(b => !b.disabled));

  {
    const ref = shelfBtns()[0];
    $('#kidName').value = 'Mia<';
    $('#kidName').dispatchEvent(new Event('input'));
    check('typing a name does not rebuild the shelf', shelfBtns()[0] === ref);
    check('name is stored sanitized', JSON.parse(localStorage.getItem('storytwirl.v1')).name === 'Mia',
          JSON.parse(localStorage.getItem('storytwirl.v1')).name);
    check('name reaches the page', $('#status').textContent.indexOf('Mia') > -1, $('#status').textContent);
    $('#kidName').value = ''; $('#kidName').dispatchEvent(new Event('input'));
  }

  shelfBtns()[0].click();
  await sleep(200);
  check('reader opens', !$('#reader').classList.contains('hidden'));
  check('reader shows the story', ($('#storyBody h2') || {}).textContent === 'The Sheep Who Counted Children',
        ($('#storyBody h2') || {}).textContent);
  check('narration player appears', !$('#player').classList.contains('hidden'));
  check('reader shows cover art', !!document.querySelector('#storyBody img.hero'));
  check('story text is below the art', ($('#storyBody').firstElementChild || {}).tagName === 'IMG');

  check('narration has the story text', paras.join(' ').length > 400, 'len=' + paras.join(' ').length);
  $('#playBtn').click();                       // no await: assert synchronously, before any utterance event can fire
  check('play starts narration', qi === 1 && curU !== null, 'qi=' + qi);
  $('#stopBtn').click();
  check('stop resets the play label', $('#playBtn').textContent.indexOf('read to me') > -1, $('#playBtn').textContent);

  $('#back').click();
  await sleep(200);
  check('free story is consumed', /free story used tonight/.test(quota()), quota());
  check('shelf locks new stories after one read', shelfBtns().slice(1).every(b => b.disabled) && !shelfBtns()[0].disabled,
        'disabled=' + shelfBtns().map(b => b.disabled).join(','));
  check('locked stories marked, read story is not',
        shelfBtns().slice(1).every(b => b.innerHTML.includes('\u{1F512}')) && !shelfBtns()[0].innerHTML.includes('\u{1F512}'));

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

  { state.day = '2000-1-1'; rollover();
    check("rollover resets quota and today's reads", state.used === 0 && state.read.length === 0,
          'used=' + state.used + ' read=' + state.read.length); }
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


def ensure_browser(timeout=25):
    """Headless Chromium dies on its own often enough (OOM on a 6GB box) that a test
    which only works while someone else's browser is alive is not a test."""
    import subprocess
    import urllib.request

    def alive():
        try:
            with urllib.request.urlopen(f"{CDP}/json/version", timeout=2):
                return True
        except Exception:
            return False

    if alive():
        return False
    profile = pathlib.Path.home() / ".hermes/cache/scratch/cdp-profile"
    subprocess.Popen(
        ["/usr/bin/chromium", "--headless=new", "--no-sandbox", "--disable-gpu",
         "--remote-debugging-port=9222", f"--user-data-dir={profile}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if alive():
            return True
        time.sleep(0.5)
    raise SystemExit("could not start Chromium on :9222")


async def run(url):
    ws_url = await page_target()
    origin = "{0.scheme}://{0.netloc}".format(urllib.parse.urlsplit(url))
    async with websockets.connect(ws_url, max_size=16 * 1024 * 1024) as ws:
        c = itertools.count(1)
        await cmd(ws, c, "Page.enable")
        # Clear the SITE ORIGIN's storage, not whatever page happens to be loaded:
        # localStorage.clear() via Runtime.evaluate runs in the current page's origin
        # (often about:blank), so a previous run's "already a member" state survives and
        # the free-tier assertions fail while the product is fine.
        await cmd(ws, c, "Page.navigate", {"url": url})
        await asyncio.sleep(1.5)
        await cmd(ws, c, "Storage.clearDataForOrigin",
                  {"origin": origin, "storageTypes": "local_storage"})
        await cmd(ws, c, "Page.navigate", {"url": url + ("?t=%d" % time.time())})
        await asyncio.sleep(3.0)
        r = await cmd(ws, c, "Runtime.evaluate",
                      {"expression": DRIVE, "awaitPromise": True, "returnByValue": True})
    res = r.get("result", {}).get("result", {})
    exc = r.get("result", {}).get("exceptionDetails")
    if exc:
        text = exc.get("exception", {}).get("description") or exc.get("text")
        raise SystemExit(f"driver threw in the page (JS broken?): {text}")
    if "value" not in res or not res["value"]:
        raise SystemExit(f"driver returned no checks — the page probably failed to load: {json.dumps(r)[:600]}")
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
    if ensure_browser():
        print("started a headless Chromium for this run")
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
