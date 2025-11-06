import requests
from news_data.fetcher import blacklist
from urllib.parse import urlparse
from datetime import datetime

API_KEY = "8edc4ac0af97446ca93446a5d872169f"
today = datetime.today().strftime('%Y-%m-%d')


def get_base_domain(url: str) -> str:
    """
    Extracts the base domain (e.g. 'cnbc.com') from a full URL.
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    # Remove 'www.' if present
    return hostname.replace("www.", "") if hostname else None


def fetch_newsapi_articles(inputs):
    today_all_articles = []

    for category in inputs["categories"]:
        print(f"[INFO] Fetching new articles for category {category} from NewsAPI...")

        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "country": inputs["country"],
            "category": category,
            "pageSize": inputs["page_size"],
            "apiKey": API_KEY
        }
        response = requests.get(url, params=params).json()

        if response.get("status") == "ok":
            print(f"[INFO] Fetched {len(response['articles'])} articles from NewsAPI")
            if len(response['articles']) < inputs["page_size"]:
                print(
                    f"[INFO] Multiple page response. Fetched only page 1. Total articles available: {response['totalResults']}")

            for article in response["articles"]:
                if get_base_domain(article["url"]) not in blacklist.blacklist:
                    article_dict = {
                        "date": today,
                        "title": article["title"].rsplit(' - ', 1)[0],
                        "url": article["url"],
                        "category": category,
                        "description": article["description"]
                    }
                    today_all_articles.append(article_dict)

    return today_all_articles


# inputs = {
#     "country": "us",
#     "categories": ["business", ],
#     "page_size": 50
# }
# fetch_newsapi_articles(inputs)
