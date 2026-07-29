# added: background scheduler that periodically re-scrapes the configured
# retail category pages and saves the results straight into PostgreSQL. This is
# the automated path (runs unattended every 6 hours); the Scraper tab in the UI
# is the manual path (scrape -> review JSON -> click Save). Both end up in the
# same scraped_products table via save_products().
from apscheduler.schedulers.background import BackgroundScheduler

from .selenium_scraper import scrape_category
from database import save_products

# Add one dict per category page you want scraped automatically. Selectors in
# selenium_scraper.py currently target books.toscrape.com (a scraping sandbox);
# a different site needs its own selectors before you add it here.
TARGETS = [
    {"url": "http://books.toscrape.com/catalogue/category/books/fiction_10/index.html",
     "brand": "Books to Scrape", "category": "Fiction"},
]

# Module-level singleton so uvicorn's --reload (which can import this module
# more than once) doesn't start two schedulers hammering the same sites.
_scheduler = None


def run_all_targets():
    """Scrape every configured target and save its rows to the database. Each
    target is isolated in its own try/except so one failing site doesn't stop
    the others."""
    for target in TARGETS:
        try:
            products = scrape_category(target["url"], target["brand"], target["category"])
            save_products(products)
            print(f"[scheduler] {target['brand']} / {target['category']}: saved {len(products)} rows.")
        except Exception as exc:
            print(f"[scheduler] failed for {target.get('url')}: {exc}")


def start_scheduler():
    """Start the 6-hourly background scrape. Safe to call more than once - the
    guard below keeps a single scheduler instance for the process."""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(run_all_targets, "interval", hours=6, id="scrape_targets")
    _scheduler.start()
    print("[scheduler] started - scraping targets every 6 hours.")
