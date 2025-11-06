from tinydb import TinyDB

# Open your TinyDB file
db = TinyDB('data_tinydb_archive_8-10.json')

# Fetch all records
all_records = db.all()

# Print them
for record in all_records:
    print(record["id"])
