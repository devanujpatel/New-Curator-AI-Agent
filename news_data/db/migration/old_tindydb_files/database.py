from tinydb import TinyDB

DB_PATH = r"C:\DEV\coding\MSN\news_data\db\migration\old_tindydb_files\data_tinydb.json"

# Singleton DB connection
db = TinyDB(DB_PATH)

def get_db():
    return db
