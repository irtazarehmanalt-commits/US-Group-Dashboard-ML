"""Live textile-industry news for the Blog page (GNews API).

Fetch-fresh only: nothing here is cached or written to the database. Every
page load calls GNews directly, so the page always reflects current headlines
and there is no table to keep in sync.
"""

import os

import requests
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

GNEWS_SEARCH_URL = "https://gnews.io/api/v4/search"
# Quoted phrases keep the multi-word terms together, otherwise GNews matches
# "garment" and "industry" separately and the results drift off-sector.
GNEWS_QUERY = 'textile OR denim OR "garment industry" OR "textile export"'
# GNews caps a single response at GNEWS_MAX_ARTICLES no matter what "max" asks
# for, so more headlines means more calls: GNEWS_PAGES requests are spent on
# every page load, and there is no cache to soften that. Raise it only if the
# daily quota on your GNews plan can absorb it.
GNEWS_MAX_ARTICLES = 10
GNEWS_PAGES = 2
GNEWS_TIMEOUT_SECONDS = 15


def _upstream_error_detail(response: requests.Response) -> str:
    """GNews reports problems as {"errors": ["..."]} - surface that text when
    it's there, so a bad request says why instead of just showing a status."""
    try:
        errors = response.json().get("errors")
    except ValueError:
        return ""
    if isinstance(errors, list) and errors:
        return " ".join(str(e) for e in errors)
    if isinstance(errors, str):
        return errors
    return ""


def _clean_article(article: dict) -> dict:
    """Flatten one GNews article into the shape the frontend expects.

    GNews returns the publisher nested under "source", and uses an empty
    string (not null) for a missing image - normalising that to None here is
    what lets the card component decide between an <img> and its placeholder.
    """
    source = article.get("source") or {}
    return {
        "title": article.get("title") or "Untitled article",
        "description": article.get("description") or "",
        "url": article.get("url") or "",
        "image": article.get("image") or None,
        "source": source.get("name") or "Unknown source",
        "published_at": article.get("publishedAt") or None,
    }


def _request_page(api_key: str, page: int) -> list[dict]:
    """One GNews call. Returns its raw article dicts, or raises an
    HTTPException carrying a message worth showing to the user."""
    try:
        response = requests.get(
            GNEWS_SEARCH_URL,
            params={
                "q": GNEWS_QUERY,
                "lang": "en",
                "max": GNEWS_MAX_ARTICLES,
                "page": page,
                "apikey": api_key,
            },
            timeout=GNEWS_TIMEOUT_SECONDS,
        )
    except requests.Timeout as exc:
        raise HTTPException(
            status_code=504, detail="The news service took too long to respond. Try again in a moment."
        ) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach the news service: {exc}") from exc

    if response.status_code == 429:
        raise HTTPException(
            status_code=429,
            detail="News API rate limit reached (GNews free tier allows a limited number of requests per day). Try again later.",
        )
    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=502,
            detail="The news service rejected the API key. Check GNEWS_API_KEY in backend/.env.",
        )
    if response.status_code != 200:
        extra = _upstream_error_detail(response)
        raise HTTPException(
            status_code=502,
            detail=f"News service returned an error ({response.status_code}){f': {extra}' if extra else ''}.",
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise HTTPException(status_code=502, detail="News service returned a malformed response.") from exc

    articles = payload.get("articles")
    if not isinstance(articles, list):
        raise HTTPException(status_code=502, detail="News service returned an unexpected response shape.")

    return [a for a in articles if isinstance(a, dict)]


def fetch_textile_news() -> list[dict]:
    """Return cleaned articles across GNEWS_PAGES sequential GNews calls.

    Every failure path raises an HTTPException with a message worth showing to
    the user - the Blog page renders `detail` directly as its error state.
    """
    api_key = os.getenv("GNEWS_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GNEWS_API_KEY is not set. Add it to backend/.env and restart the server.",
        )

    articles: list[dict] = []
    seen_urls: set[str] = set()

    for page in range(1, GNEWS_PAGES + 1):
        try:
            raw_articles = _request_page(api_key, page)
        except HTTPException:
            # Losing the first page leaves nothing to show, so surface the
            # error. Losing a later one shouldn't discard the headlines already
            # in hand - a rate limit is the likely cause, and it becomes likely
            # precisely because each load spends GNEWS_PAGES requests. Stop
            # paginating and serve the shorter list instead of an error page.
            if page == 1:
                raise
            break

        for article in raw_articles:
            # The feed shifts between the two calls, so the same story can come
            # back on both pages - keep the first copy, drop the repeat.
            url = article.get("url")
            if url:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
            articles.append(_clean_article(article))

    return articles
