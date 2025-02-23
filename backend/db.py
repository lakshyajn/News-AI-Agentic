import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Use MongoDB Atlas Connection String (from Compass)
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://lakshyajain0740:2wu7gG8SW4WFT5qf@cluster0.3jlor.mongodb.net/?retryWrites=true&w=majority")
DB_NAME = os.getenv("DB_NAME", "newsDB")

# Connect to MongoDB Atlas
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000) 
db = client[DB_NAME]
articles_collection = db["articles"]

# Check connection
try:
    client.admin.command('ping')
    print("✅ Connected to MongoDB Atlas!")
except Exception as e:
    print(f"❌ MongoDB connection error: {e}")
