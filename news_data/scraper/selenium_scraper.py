from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time


def scrape_article_with_selenium(url, headless=True, wait_time=3):
    """
    Scrapes the textual content from a webpage using Selenium.

    Args:
        url (str): URL of the page to scrape
        headless (bool): Whether to run browser in headless mode (no UI)
        wait_time (int): Seconds to wait for page to load

    Returns:
        str: Extracted text content (paragraphs joined)
    """
    # Setup Chrome options
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")  # modern headless
        chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--log-level=3")  # reduce logs

    # Initialize driver
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )

    try:
        driver.get(url)
        time.sleep(wait_time)  # Let the page load JS content

        # Extract text from all <p> tags
        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        page_text = "\n".join([p.text for p in paragraphs if p.text.strip()])

        return page_text.strip() if page_text else None

    except Exception as e:
        print(f"[WARN] Selenium scraping failed for {url}: {e}")
        return None

    finally:
        driver.quit()
