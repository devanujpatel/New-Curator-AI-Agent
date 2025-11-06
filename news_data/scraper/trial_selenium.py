"""from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Open a browser
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get("https://www.cnbc.com/")
print(driver.title)
driver.quit()
"""
from news_data.scraper.content_fetcher import fetch_full_article_content

url = "https://www.cnbc.com/2025/08/06/tesla-training-improved-full-self-driving-fsd-model-could-release-next-month.html"
content = fetch_full_article_content(url, headless=True)

if content:
    print("Article snippet:\n", content[:500], "...")
else:
    print("No content found.")
