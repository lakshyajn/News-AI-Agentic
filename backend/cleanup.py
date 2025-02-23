from datetime import datetime, timedelta
from backend.db import articles_collection

def delete_old_articles():
    expiry_date = datetime.utcnow() - timedelta(days=7)  # Delete articles older than 7 days
    articles_collection.delete_many({"timestamp": {"$lt": expiry_date}})
