"""Stealth web scraper for retail product/pricing data.

Despite the filename (kept so existing imports don't break), this now uses
`nodriver` rather than plain Selenium. nodriver drives a real Chrome over CDP
with no chromedriver to version-match, and is stealthy enough to get past the
Akamai/DataDome bot walls that hard-block plain Selenium (Levi's returned a
341-byte "Access Denied" to Selenium; nodriver + headful + consent-dismiss +
human scrolling pulls the real 3.7MB page from a residential IP).

It handles BOTH detection layers:
  Layer 1 (the door): real Chrome fingerprint via nodriver, run headful.
  Layer 2 (in-session): dismiss cookie/consent popups, human-like scrolling.

The public API is unchanged: scrape_category(url, brand, category) returns a
list of product dicts, and save_to_json / load_from_json stage them for the
"Save to Database" button. The async nodriver work is wrapped in a private
event loop so callers (FastAPI sync endpoints, the scheduler) stay synchronous.
"""
import asyncio
import json
import os
import random
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import nodriver as uc
from dotenv import load_dotenv

# This module also runs as a standalone subprocess (see __main__), which does NOT
# inherit the server's loaded env - load it here so the LLM key is available.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# JSON staging file - Scrape writes here; "Save to Database" reads it.
SCRAPED_JSON_PATH = Path(__file__).resolve().parent / "scraped_products.json"

# Lazily-created Ollama cloud client (same model the chatbot uses) for the
# LLM-guided selector step. False = no API key, so the step is skipped.
_llm_client = None


def _get_llm():
    global _llm_client
    if _llm_client is None:
        key = os.getenv("OLAMA_API_KEY")
        if not key:
            _llm_client = False
        else:
            from ollama import Client
            _llm_client = Client(host="https://ollama.com", headers={"Authorization": "Bearer " + key})
    return _llm_client or None

# CURATED per-site CSS selectors, for best-quality extraction on known sites.
# Any site NOT listed here uses the GENERIC extractor (_GENERIC_EXTRACT_JS),
# which auto-detects products via JSON-LD structured data + a price heuristic -
# so the scraper works on many sites without hand-tuning selectors.
# name_attr: when set, the product name is read from that attribute instead of
# the element's text (books.toscrape truncates the visible text but keeps the
# full title in the <a title="..."> attribute).
SITE_SELECTORS = {
    "books.toscrape.com": {
        "card": "article.product_pod",
        "name": "h3 a", "name_attr": "title",
        "price": ".price_color",
        "image": "img",
        "link": "h3 a",
    },
    "levi.com": {
        "card": ".product-cell",
        "name": ".product-name", "name_attr": None,
        "price": ".product-price",
        "image": ".product-image img",
        "link": ".product-link",
    },
}


def _selectors_for(url: str):
    """Curated selectors for a known domain, or None to use the generic extractor."""
    host = urlparse(url).netloc.lower()
    for domain, sel in SITE_SELECTORS.items():
        if domain in host:
            return sel
    return None


def _extract_js(sel: dict) -> str:
    """Build a JS snippet that returns [{name, price, image_url, url}, ...] by
    running the site's selectors in the page itself - more reliable across sites
    than driving each element from Python."""
    if sel["name_attr"]:
        name_expr = f"c.querySelector({json.dumps(sel['name'])}) && c.querySelector({json.dumps(sel['name'])}).getAttribute({json.dumps(sel['name_attr'])})"
    else:
        name_expr = f"c.querySelector({json.dumps(sel['name'])}) && c.querySelector({json.dumps(sel['name'])}).innerText"
    # Return a JSON *string* (not a JS array): nodriver hands primitives back as
    # plain Python values, so json.loads gives us a real list of dicts. Returning
    # the array object directly yields an opaque RemoteObject instead.
    return f"""
    (() => JSON.stringify(Array.from(document.querySelectorAll({json.dumps(sel['card'])})).map(c => {{
      const nameRaw = {name_expr};
      const priceEl = c.querySelector({json.dumps(sel['price'])});
      const imgEl   = c.querySelector({json.dumps(sel['image'])});
      const linkEl  = c.querySelector({json.dumps(sel['link'])});
      return {{
        name: nameRaw ? String(nameRaw).trim() : null,
        price: priceEl ? priceEl.innerText.trim() : null,
        image_url: imgEl ? imgEl.src : null,
        url: linkEl ? linkEl.href : null,
      }};
    }})))()
    """


# Generic, site-agnostic product extractor. Runs in the page and returns a JSON
# string of [{name, price, image_url, url}, ...]. Strategy:
#   1) JSON-LD structured data (schema.org Product / ItemList) - most e-commerce
#      sites embed this for SEO/Google Shopping; it's the most reliable source.
#   2) Heuristic fallback - find small leaf elements that contain a currency-like
#      price, climb to the nearest ancestor holding an image, and read the name
#      from a heading / link title / image alt within that card.
# It won't rescue sites that keep no product data in the DOM at all (e.g. Zara's
# virtualized grid), but it works on the majority of normal product pages.
_GENERIC_EXTRACT_JS = r"""
(() => {
  const out = [], seen = new Set();
  const clean = s => (s == null ? '' : String(s)).replace(/\s+/g, ' ').trim();
  const firstImg = v => Array.isArray(v) ? firstImg(v[0]) : (v && (v.url || v)) || null;
  // generic UI labels that must NOT be treated as a product name
  const junkRe = /^(quick\s*view|quick\s*add|quick\s*shop|add to (bag|cart|wish\s?list)|view( product| details)?|shop( now)?|select( options)?|choose( options)?|notify me|wish\s?list|new|sale|more colou?rs?|see details|buy now|details|compare)$/i;
  // resolve a real image URL even when the site lazy-loads (data-src / srcset)
  const imgSrc = img => {
    if (!img) return null;
    const cands = [];
    const ss = img.getAttribute('srcset') || img.getAttribute('data-srcset');
    if (ss) { const p = ss.split(',').map(s => s.trim().split(/\s+/)[0]).filter(Boolean); if (p.length) cands.push(p[p.length - 1]); }
    cands.push(img.getAttribute('data-src'), img.getAttribute('data-original'), img.getAttribute('data-lazy'), img.currentSrc, img.getAttribute('src'));
    for (const u of cands) if (u && !u.startsWith('data:') && !/blank|placeholder|spacer|transparent|1x1/i.test(u)) return u;
    return null;
  };
  function push(name, price, image_url, url) {
    name = clean(name).slice(0, 140);
    if (!name) return;
    const key = name + '|' + (url || '');
    if (seen.has(key)) return;
    seen.add(key);
    out.push({ name, price: price != null && price !== '' ? clean(price) : null,
               image_url: image_url || null, url: url || null });
  }

  // 1) JSON-LD structured data
  document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
    let data; try { data = JSON.parse(s.textContent); } catch (e) { return; }
    const nodes = [];
    (function collect(d) {
      if (!d || typeof d !== 'object') return;
      if (Array.isArray(d)) { d.forEach(collect); return; }
      nodes.push(d);
      collect(d['@graph']); collect(d.itemListElement); collect(d.item);
    })(data);
    nodes.forEach(d => {
      const type = d['@type'];
      const isProduct = type === 'Product' || (Array.isArray(type) && type.includes('Product')) || (d.name && d.offers);
      if (!isProduct) return;
      let price = null;
      const off = d.offers ? (Array.isArray(d.offers) ? d.offers[0] : d.offers) : null;
      if (off) price = off.price || off.lowPrice || (off.priceSpecification && off.priceSpecification.price);
      push(d.name, price, firstImg(d.image), d.url);
    });
  });
  if (out.length >= 3) return JSON.stringify(out);

  // 2) price-heuristic fallback
  const priceRe = /(?:[$£€₹]|USD|EUR|GBP|PKR|Rs\.?|AED|SAR)\s?\d[\d.,]*/i;
  Array.from(document.querySelectorAll('body *')).forEach(pe => {
    if (pe.children.length) return;
    const t = (pe.textContent || '').trim();
    if (!t || t.length > 24 || !priceRe.test(t)) return;
    if (/\d\s*[-–—]\s*\D*\d/.test(t)) return;  // skip price ranges like "$0 - $25" (filter facets)
    let card = pe;
    for (let i = 0; i < 7 && card.parentElement; i++) {
      card = card.parentElement;
      if (card.querySelector && card.querySelector('img')) break;
    }
    if (!card || !card.querySelector) return;
    const img = card.querySelector('img'), link = card.querySelector('a[href]');
    // Build name candidates in priority order, then pick the first that isn't
    // itself price-like (avoids grabbing the price <h4> as the name).
    const cand = [];
    const titleEl = card.querySelector('a[class*="title" i], [class*="title" i], [class*="name" i]');
    if (titleEl) cand.push(titleEl.getAttribute('title') || titleEl.textContent);
    if (link) cand.push(link.getAttribute('title') || link.textContent);
    card.querySelectorAll('h1,h2,h3,h4,h5').forEach(h => { if (h !== pe) cand.push(h.textContent); });
    if (img) cand.push(img.getAttribute('alt'));
    let name = '';
    for (const c of cand) {
      const cc = clean(c);
      if (cc && !priceRe.test(cc) && !junkRe.test(cc)) { name = cc; break; }
    }
    push(name, t, imgSrc(img), link ? link.href : null);
  });
  return JSON.stringify(out);
})()
"""


def _rows_from_raw(raw, brand, category, url):
    """Parse the JSON string a page extractor returned into tagged product rows,
    dropping entries with no name."""
    data = json.loads(raw) if isinstance(raw, str) else (raw or [])
    rows = []
    for r in data:
        if not r or not r.get("name"):
            continue
        rows.append({
            "brand": brand, "category": category,
            "name": r.get("name"), "price": r.get("price"),
            "image_url": r.get("image_url"), "url": r.get("url") or url,
        })
    return rows


# Grabs the outer HTML of ~2 representative product cards (found by climbing from
# a price to a container with an image + link) to feed the LLM selector step.
_SAMPLE_CARDS_JS = r"""
(() => {
  const priceRe = /(?:[$£€₹]|USD|EUR|GBP|PKR|Rs\.?)\s?\d/;
  const seen = new Set(), cards = [];
  for (const el of document.querySelectorAll('body *')) {
    if (el.children.length) continue;
    const t = (el.textContent || '').trim();
    if (!t || t.length > 24 || !priceRe.test(t)) continue;
    let card = el;
    for (let i = 0; i < 8 && card.parentElement; i++) {
      card = card.parentElement;
      if (card.querySelector && card.querySelector('img') && card.querySelector('a[href]')) break;
    }
    if (!card) continue;
    const sig = card.tagName + '|' + String(card.className || '').slice(0, 60);
    if (seen.has(sig)) continue;
    seen.add(sig);
    cards.push(card.outerHTML.slice(0, 2500));
    if (cards.length >= 2) break;
  }
  return JSON.stringify(cards);
})()
"""

_LLM_SELECTOR_SYSTEM = (
    "You are given the HTML of ONE product card from an e-commerce listing page. "
    "Respond with ONLY a JSON object (no markdown, no explanation):\n"
    '{"card": "...", "name": "...", "name_attr": null, "price": "...", "image": "...", "link": "..."}\n'
    "- card: a CSS selector matching EVERY product card on the page - use the card "
    "element's own tag plus a stable class from the HTML.\n"
    "- name, price, image, link: CSS selectors RELATIVE to a card for the product "
    "name, the price, the <img>, and the product <a> link.\n"
    "- name_attr: if the name lives only in an attribute (e.g. an <img> alt or an "
    "<a> title), give that attribute name; otherwise null.\n"
    "IMPORTANT: the name must be the real PRODUCT TITLE. Never select an action "
    "button like 'Quick View', 'Quick Add', 'Add to Bag', or 'Wishlist'. If the "
    "title isn't a text node, read it from the product <img> alt (name_attr='alt').\n"
    "Prefer stable class names over deep/positional selectors. Return valid CSS."
)


def _llm_selectors(sample_json):
    """LLM-guided step: derive CSS selectors from a sample card's HTML. Returns a
    selector dict compatible with _extract_js, or None on any failure (caller then
    falls back to the generic extractor)."""
    client = _get_llm()
    if not client or not sample_json:
        return None
    try:
        samples = json.loads(sample_json)
    except Exception:
        return None
    if not samples:
        return None
    html = ("\n\n=== next card ===\n\n".join(samples))[:6000]
    try:
        resp = client.chat(model="gpt-oss:120b-cloud", messages=[
            {"role": "system", "content": _LLM_SELECTOR_SYSTEM},
            {"role": "user", "content": "Card HTML:\n" + html},
        ])
        txt = resp.message.content.strip()
    except Exception:
        return None
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    try:
        sel = json.loads(m.group(0))
    except Exception:
        return None
    if not (isinstance(sel, dict) and sel.get("card") and sel.get("name") and sel.get("price")):
        return None
    sel.setdefault("name_attr", None)
    sel["image"] = sel.get("image") or "img"
    sel["link"] = sel.get("link") or "a"
    return sel


_DISMISS_JS = """
(() => {
  // known consent-accept selectors first (OneTrust is used by Levi's, Zara, ...)
  const sels = ['#onetrust-accept-btn-handler', 'button[id*="accept" i]',
                'button[aria-label*="accept" i]', 'button[data-testid*="accept" i]'];
  for (const s of sels) { const el = document.querySelector(s); if (el) { el.click(); return true; } }
  // fallback: a button/link whose text looks like an accept action
  const el = Array.from(document.querySelectorAll('button, a'))
    .find(b => /accept all|accept|agree|allow all/i.test((b.textContent || '').trim()));
  if (el) { el.click(); return true; }
  return false;
})()
"""


async def _dismiss_popups(tab):
    """Layer 2: click the cookie/consent 'accept' button via in-page JS. We use
    evaluate rather than tab.find because tab.find does a full-text DOM scan that
    HANGS on very large DOMs (e.g. Zara); running JS in the page is instant."""
    try:
        await tab.evaluate(_DISMISS_JS)
        await asyncio.sleep(random.uniform(0.5, 1.0))
    except Exception:
        pass


async def _human_scroll(tab):
    """Layer 2: variable scrolling that mimics a human and triggers lazy-loaded
    prices/images."""
    for _ in range(6):
        try:
            await tab.scroll_down(random.randint(300, 600))
        except Exception:
            break
        await asyncio.sleep(random.uniform(0.3, 1.0))


async def _extract_products(tab, sel, brand, category, url):
    await _human_scroll(tab)  # scroll to trigger lazy-loaded cards/prices
    # 1) selectors (curated per-site OR LLM-derived) when we have them
    if sel:
        try:
            try:
                await tab.select(sel["card"], timeout=10)
            except Exception:
                pass
            rows = _rows_from_raw(await tab.evaluate(_extract_js(sel)), brand, category, url)
            if rows:
                return rows
        except Exception:
            pass  # invalid/wrong selectors -> fall through to generic
    # 2) generic extractor (JSON-LD + price heuristic) - works on many sites
    return _rows_from_raw(await tab.evaluate(_GENERIC_EXTRACT_JS), brand, category, url)


async def _scrape_async(url: str, brand: str, category: str, headless: bool = False) -> list:
    sel = _selectors_for(url)
    browser = await uc.start(
        headless=headless,  # headful (default) is far less detectable
        browser_args=["--window-size=1440,1000", "--lang=en-US"],
    )
    products = []
    try:
        tab = await browser.get(url)
        await asyncio.sleep(random.uniform(3, 5))  # let the page settle
        await _dismiss_popups(tab)                  # cookie/consent, once
        await _human_scroll(tab)                    # load some cards before sampling

        # LLM-guided pipeline: for a site we haven't curated, show the LLM a
        # sample product card and let it derive the CSS selectors, instead of
        # relying on the generic heuristic. Runs in a thread so the blocking LLM
        # HTTP call doesn't stall nodriver's event loop. Falls back to generic.
        if not sel:
            try:
                sample = await tab.evaluate(_SAMPLE_CARDS_JS)
                sel = await asyncio.to_thread(_llm_selectors, sample)
                if sel:
                    print(f"[scraper] LLM selectors: {sel}", flush=True)
            except Exception as exc:
                print(f"[scraper] LLM selector step failed: {exc}", flush=True)
                sel = None

        # Try up to twice. Between tries we DON'T reload (a reload on a heavy SPA
        # like Zara is brutally slow and blows the timeout); instead we wait a
        # beat and let _extract_products scroll further, which loads more of the
        # lazy content and re-extracts.
        for _ in range(2):
            products = await _extract_products(tab, sel, brand, category, url)
            if products:
                break
            await asyncio.sleep(random.uniform(1.5, 3))
    finally:
        try:
            browser.stop()
        except Exception:
            pass
    return products


def _kill_process_tree(pid: int) -> None:
    """Kill a child process and all its descendants. nodriver spawns Chrome as a
    grandchild that outlives a plain terminate; on Windows `taskkill /T` walks the
    whole tree so no orphaned Chrome is left behind after a timeout."""
    try:
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def scrape_category(url: str, brand: str, category: str, headless: bool = False):
    """Scrape one category page and return a list of product dicts
    (brand, category, name, price, image_url, url).

    Runs the actual nodriver scrape in a FRESH SUBPROCESS (this module executed
    as a script - see the __main__ block). In-process nodriver is unreliable
    under uvicorn's Windows event-loop policy: a SelectorEventLoop can't spawn
    Chrome (instant NotImplementedError), and forcing a Proactor loop in a side
    thread hangs instead. A clean subprocess gets nodriver the default Proactor
    loop and a process to itself - exactly the conditions it works under
    standalone - fully isolated from the server's loop. Results come back via a
    temp JSON file.
    """
    fd, out_path = tempfile.mkstemp(suffix=".json", prefix="scrape_")
    os.close(fd)
    lfd, log_path = tempfile.mkstemp(suffix=".log", prefix="scrape_")
    os.close(lfd)
    cmd = [sys.executable, str(Path(__file__).resolve()),
           url, brand, category, "1" if headless else "0", out_path]
    try:
        # Redirect the child's output to a FILE, not a PIPE. The child launches
        # Chrome, which inherits the handles; with a PIPE, subprocess would block
        # draining it until Chrome exits - so a slow/heavy site (e.g. Zara) whose
        # Chrome doesn't die promptly would hang the request forever. A file has
        # nothing to drain, so we return as soon as the child process exits, and
        # on timeout we kill the whole process tree (Chrome included).
        with open(log_path, "w", encoding="utf-8", errors="replace") as logf:
            proc = subprocess.Popen(cmd, stdout=logf, stderr=logf)
            try:
                proc.wait(timeout=150)
            except subprocess.TimeoutExpired:
                _kill_process_tree(proc.pid)
                raise RuntimeError(
                    "Scrape timed out - the site was too slow or kept blocking. "
                    "Very heavy/dynamic sites (e.g. Zara) may not scrape reliably."
                )
        try:
            return json.loads(Path(out_path).read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            tail = Path(log_path).read_text(encoding="utf-8", errors="replace")[-600:]
            raise RuntimeError(f"Scraper produced no valid output ({exc}). Log tail: {tail}") from exc
    finally:
        for p in (out_path, log_path):
            try:
                os.remove(p)
            except OSError:
                pass


# --- JSON staging (unchanged) ---------------------------------------------

def save_to_json(products: list) -> None:
    SCRAPED_JSON_PATH.write_text(json.dumps(products, indent=2), encoding="utf-8")


def load_from_json() -> list:
    if not SCRAPED_JSON_PATH.exists():
        return []
    return json.loads(SCRAPED_JSON_PATH.read_text(encoding="utf-8"))


# --- Subprocess entrypoint -------------------------------------------------
# Invoked by scrape_category() as:  python selenium_scraper.py URL BRAND CATEGORY
# HEADLESS(0/1) OUTPUT_JSON_PATH. Runs the scrape on nodriver's own loop in this
# clean process and writes the product list to OUTPUT_JSON_PATH.
if __name__ == "__main__":
    _url, _brand, _category, _headless, _out = sys.argv[1:6]
    _products = uc.loop().run_until_complete(
        _scrape_async(_url, _brand, _category, headless=(_headless == "1")))
    Path(_out).write_text(json.dumps(_products, ensure_ascii=False), encoding="utf-8")
    # force-exit: a lingering Chrome/nodriver thread would otherwise hang exit
    os._exit(0)
