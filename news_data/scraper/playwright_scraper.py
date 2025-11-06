from playwright.sync_api import sync_playwright
import time

def scrape_article_with_playwright(url, headless=True, wait_time=3):
    """
    Scrapes the textual content from a webpage using Playwright (no stealth).

    Args:
        url (str): URL of the page to scrape
        headless (bool): Whether to run browser in headless mode (no UI)
        wait_time (int): Seconds to wait for page to load

    Returns:
        str: Extracted text content (paragraphs joined)
    """
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(url, timeout=60000)  # wait up to 60s
            time.sleep(wait_time)  # wait for JS content to load

            # Extract all <p> tag text
            paragraphs = page.query_selector_all("p")
            page_text = "\n".join([
                p.inner_text().strip() for p in paragraphs if p.inner_text().strip()
            ])

            return page_text.strip() if page_text else None

        except Exception as e:
            print(f"[WARN] Playwright scraping failed for {url}: {e}")
            return None

        finally:
            browser.close()