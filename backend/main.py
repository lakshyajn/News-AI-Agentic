from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
from googletrans import Translator
import requests
import asyncio
from datetime import datetime
from backend.db import articles_collection
from backend.cleanup import delete_old_articles
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup

app = FastAPI()

# CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Summarization Model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Translator (English to Hindi)
translator = Translator()

# **🔹 Function: Scrape News from a Website**
def scrape_news(source_url, category="General"):
    try:
        response = requests.get(source_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        articles = []
        for news_item in soup.select("article"):  # Adjust selector as needed
            title = news_item.find("h2") or news_item.find("h3") or news_item.find("h1")
            link = news_item.find("a")["href"] if news_item.find("a") else None
            summary = news_item.find("p").text if news_item.find("p") else None

            if title and link:
                full_link = requests.compat.urljoin(source_url, link)
                articles.append({
                    "title": title.text.strip(),
                    "url": full_link,
                    "summary": summary.strip() if summary else "",
                    "category": category,
                    "timestamp": datetime.utcnow()
                })

        return articles

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

# **🔹 Function: Summarize an Article**
def summarize_article(article_text):
    summary = summarizer(article_text, max_length=200, min_length=50, do_sample=False)[0]["summary_text"]
    summary_hindi = translator.translate(summary, src="en", dest="hi").text
    return summary, summary_hindi

# **🔹 Function: Fetch & Summarize News Automatically**
def fetch_and_store_news():
    sources = [
        {"url": "https://www.bbc.com/news", "category": "World"},
        {"url": "https://www.aljazeera.com/", "category": "Politics"},
        {"url": "https://timesofindia.indiatimes.com/", "category": "India"},
    ]

    for source in sources:
        scraped_articles = scrape_news(source["url"], source["category"])
        for article in scraped_articles:
            existing = articles_collection.find_one({"title": article["title"]})
            if not existing:
                article["summary"], article["summary_hindi"] = summarize_article(article["summary"])
                article["image_url"] = generate_image(article["title"])  # Generate AI image
                articles_collection.insert_one(article)

# **🔹 Generate an AI Image**
def generate_image(prompt):
    response = requests.post("https://stablediffusionapi.com/generate", json={"prompt": prompt})
    return response.json().get("image_url", "https://default_image.com")

# **🔹 API Endpoint: Fetch News Automatically**
@app.get("/fetch-news/")
async def fetch_news():
    fetch_and_store_news()
    return {"message": "News fetched and stored!"}

# **🔹 API Endpoint: Get All Stored Articles**
@app.get("/articles/")
async def get_articles():
    delete_old_articles()  # Clean old articles
    articles = list(articles_collection.find({}, {"_id": 0}))

    if not articles:
        return {"message": "No articles found", "articles": []}
    
    return {"articles": articles}

# **🔹 Background Cleanup Task (Deletes Old Articles Every Hour)**
async def scheduled_cleanup():
    while True:
        await delete_old_articles()
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(scheduled_cleanup())