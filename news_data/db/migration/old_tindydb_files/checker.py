from news_data.db.migration.old_tindydb_files.database import get_db
from tinydb import Query
import pprint

db = get_db()
article = Query()
my_article = db.get(article.url == "https://www.investors.com/news/technology/monday-earnings-mndy-stock-news-q22025/")

del my_article["embedding"]

pprint.pprint(my_article)

# for a in db.all():
#     if "cnbc.com/2025/08/11/automakers-trump-electric-vehicles" in a["url"]:
#         print(a["url"])



# update_notes("https://www.cnbc.com/2025/08/11/automakers-trump-electric-vehicles-ev-policies-ford-gm-tesla-rivian.html", "NOTE SAYS HI ~note")