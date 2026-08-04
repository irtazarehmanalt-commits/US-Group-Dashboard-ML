"""Batch scrape of the configured jeans-brand targets (Arket, The Frankie
Shop, Zara, Diesel, Levi's, H&M): scrapes each brand's Women's and Men's
jeans category page, tags every product with a Fit Category / Fit
Sub-Category via fit_taxonomy.classify_fit(), then saves the results both
into Postgres (scraped_products, same table the manual single-URL scrape and
the scheduler already use) and as one JSON file per brand in
backend/scraper_data/.

Manual trigger only (see POST /market-data/scrape-brands in main.py) - not
wired into the 6-hourly scheduler (scraper/scheduler.py), which stays on its
own separate placeholder target for now.
"""
import json
from pathlib import Path

from .selenium_scraper import scrape_category
from .fit_taxonomy import classify_fit
from database import save_products

SCRAPER_DATA_DIR = Path(__file__).resolve().parent.parent / "scraper_data"

# One entry per brand per section (its Women's / Men's jeans category page).
# Found by hand via web search, not by scraping - these retailers block plain
# browsing behind Akamai/DataDome (see selenium_scraper.py's own notes on
# that), so locating the URLs and actually scraping them are separate steps.
BRAND_TARGETS = [
    {"brand": "Arket", "section": "women", "url": "https://www.arket.com/en-ww/women/clothing/jeans/"},
    {"brand": "Arket", "section": "men", "url": "https://www.arket.com/en-ww/men/clothing/jeans/"},
    {"brand": "The Frankie Shop", "section": "women", "url": "https://thefrankieshop.com/collections/womens-denim-clothing"},
    {"brand": "The Frankie Shop", "section": "men", "url": "https://thefrankieshop.com/collections/mens-denim-clothing"},
    {"brand": "Zara", "section": "women", "url": "https://www.zara.com/us/en/woman-jeans-l1119.html"},
    {"brand": "Zara", "section": "men", "url": "https://www.zara.com/us/en/man-jeans-l659.html"},
    {"brand": "Diesel", "section": "women", "url": "https://diesel.com/en-us/woman/denim/viewall/"},
    {"brand": "Diesel", "section": "men", "url": "https://diesel.com/en-us/man/denim/viewall/"},
    {"brand": "Levi's", "section": "women", "url": "https://www.levi.com/US/en_US/clothing/women/jeans/c/levi_clothing_women_jeans"},
    {"brand": "Levi's", "section": "men", "url": "https://www.levi.com/US/en_US/clothing/men/jeans/c/levi_clothing_men_jeans"},
    {"brand": "H&M", "section": "women", "url": "https://www2.hm.com/en_us/women/products/jeans.html"},
    {"brand": "H&M", "section": "men", "url": "https://www2.hm.com/en_us/men/products/jeans.html"},
]


def _brand_slug(brand: str) -> str:
    return brand.lower().replace("'", "").replace("&", "and").replace(" ", "_")


def scrape_all_configured_brands(save_to_db: bool = True) -> dict:
    """Scrape every BRAND_TARGETS entry, tag each product with its fit
    category/sub-category, write one JSON file per brand into
    backend/scraper_data/, and (unless save_to_db=False) insert everything
    into scraped_products too. Each target is isolated in its own try/except
    so one blocked or broken site doesn't stop the rest.

    Returns a per-brand summary: {brand: {scraped, classified, errors, json_file}}.
    """
    SCRAPER_DATA_DIR.mkdir(exist_ok=True)
    by_brand: dict[str, list] = {}
    summary: dict[str, dict] = {}

    for target in BRAND_TARGETS:
        brand, section, url = target["brand"], target["section"], target["url"]
        category = f"{section.capitalize()}'s Jeans"
        entry = summary.setdefault(brand, {"scraped": 0, "classified": 0, "errors": [], "json_file": None})
        try:
            products = scrape_category(url, brand, category)
        except Exception as exc:
            entry["errors"].append(f"{section}: {exc}")
            print(f"[batch_scrape] {brand} ({section}) failed: {exc}")
            continue

        for p in products:
            fit_category, fit_sub_category = classify_fit(p.get("name") or "", section)
            p["fit_category"] = fit_category
            p["fit_sub_category"] = fit_sub_category
            p["section"] = section
            if fit_category:
                entry["classified"] += 1

        entry["scraped"] += len(products)
        by_brand.setdefault(brand, []).extend(products)
        print(f"[batch_scrape] {brand} ({section}): {len(products)} products.")

    for brand, products in by_brand.items():
        out_path = SCRAPER_DATA_DIR / f"{_brand_slug(brand)}.json"
        out_path.write_text(json.dumps(products, indent=2, ensure_ascii=False), encoding="utf-8")
        summary[brand]["json_file"] = out_path.name

    if save_to_db:
        all_products = [p for products in by_brand.values() for p in products]
        inserted = save_products(all_products)
        print(f"[batch_scrape] saved {inserted} rows to scraped_products.")

    return summary
