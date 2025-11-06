import os
import json
import hashlib
from newspaper import Article
from selenium_scraper import scrape_article_with_selenium
from playwright_scraper import scrape_article_with_playwright

CACHE_FILE = "article_content_cache.json"


def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def _get_cache_key(url):
    return hashlib.md5(url.encode()).hexdigest()


def _clean_text(text):
    """Clean up scraped text by removing empty lines and trimming whitespace."""
    if not text:
        return None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def fetch_full_article_content(url, force_refresh=False, headless=True):
    """
    Fetches and caches the full article content for a given URL.
    1. Checks cache
    2. Tries Newspaper3k
    3. Falls back to Selenium scraper if needed
    4. Fallbs back to Playwright scraper if needed

    Args:
        url (str): Article URL
        force_refresh (bool): Ignore cache and re-scrape
        headless (bool): Run Selenium in headless mode

    Returns:
        str or None: Full article text
    """
    cache = _load_cache()
    cache_key = _get_cache_key(url)

    # Step 1: Cache check
    if not force_refresh and cache_key in cache:
        return cache[cache_key]

    content = None

    # Step 2: Try Newspaper3k first
    try:
        article = Article(url)
        article.download()
        article.parse()
        content = _clean_text(article.text)
    except Exception as e:
        print(f"[WARN] Newspaper3k failed for {url}: {e}")

    # Step 3: Fall back to Selenium if content is missing/too short
    if not content or len(content.split()) < 50:
        selenium_content = scrape_article_with_selenium(url, headless=headless)
        selenium_content = _clean_text(selenium_content)
        if selenium_content and len(selenium_content.split()) > (len(content.split()) if content else 0):
            content = selenium_content

    if not content or len(content.split()) < 50:
        playwright_content = scrape_article_with_playwright(url, headless=headless)
        playwright_content = _clean_text(playwright_content)
        if playwright_content and len(playwright_content.split()) > (len(content.split()) if content else 0):
            content = playwright_content
    
    # Step 4: Cache if content found
    if content:
        cache[cache_key] = content
        _save_cache(cache)
    else:
        print(f"[WARN] No content fetched for {url}")

    return content
