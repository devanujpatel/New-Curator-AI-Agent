# convert article_feedback.json file to tinydb
# one time run to convert existing data into tiny db

import json
from tinydb import TinyDB

# Load your current JSON
with open('article_feedback.json', 'r') as f:
    old_data = json.load(f)

# Convert dict-of-dicts → list of dicts with "key" field
records = []
for url, info in old_data.items():
    record = {"key": url}  # preserve original key
    record.update(info)    # merge title/url/feedback
    records.append(record)

# Save to TinyDB
db = TinyDB('article_feedback_tinydb.json')
db.insert_multiple(records)

print(f"Migrated {len(records)} records into TinyDB!")
