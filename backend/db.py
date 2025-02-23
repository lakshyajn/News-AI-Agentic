import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME","newsDB")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
articles_collection = db["articles"]