from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
from googletrans import Translator
import requests
import asyncio
from datetime import datetime
from backend.db import articles_collection
from backend.cleanup import delete_old_articles
from bs4 import BeautifulSoup

app = FastAPI()

# ✅ Allow Frontend Access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow frontend to access API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ AI Summarization Model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# ✅ Translator (English to Hindi)
translator = Translator()

# ✅ Sources for Scraping
SOURCES = [
    {"url": "https://www.bbc.com/news", "category": "World"},
    {"url": "https://www.aljazeera.com/", "category": "Politics"},
    {"url": "https://timesofindia.indiatimes.com/", "category": "India"},
]

# ✅ Scrape News from a Website
def scrape_news(source_url, category="General"):
    try:
        response = requests.get(source_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        articles = []
        for news_item in soup.find_all("article"):  # Adjust selector as needed
            title_tag = news_item.find("h2") or news_item.find("h3") or news_item.find("h1")
            link_tag = news_item.find("a")
            summary_tag = news_item.find("p")

            if title_tag and link_tag:
                title = title_tag.text.strip()
                url = requests.compat.urljoin(source_url, link_tag["href"])
                summary = summary_tag.text.strip() if summary_tag else ""

                articles.append({
                    "title": title,
                    "url": url,
                    "summary": summary,
                    "category": category,
                    "timestamp": datetime.utcnow(),
                })

        return articles

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

# ✅ AI Summarization & Translation
def process_article(article):
    try:
        summary = summarizer(article["summary"], max_length=200, min_length=50, do_sample=False)[0]["summary_text"]
        summary_hindi = translator.translate(summary, src="en", dest="hi").text
        article["summary"] = summary
        article["summary_hindi"] = summary_hindi
        article["image_url"] = generate_image(article["title"])  # AI Image
        return article
    except Exception as e:
        return None  # Skip article if processing fails

# ✅ Fetch, Process & Store News
def fetch_and_store_news():
    for source in SOURCES:
        articles = scrape_news(source["url"], source["category"])
        for article in articles:
            existing = articles_collection.find_one({"title": article["title"]})
            if not existing:
                processed_article = process_article(article)
                if processed_article:
                    articles_collection.insert_one(processed_article)

# ✅ Generate AI Image
def generate_image(prompt):
    try:
        response = requests.post("https://stablediffusionapi.com/generate", json={"prompt": prompt})
        data = response.json()
        image_url = data.get("image_url")  # ✅ Extract image URL properly

        # ✅ Ensure the image URL is valid
        if image_url and image_url.startswith("http"):
            return image_url
        return "https://via.placeholder.com/400"  # ✅ Placeholder image if API fails
    except:
        return "https://via.placeholder.com/400"  # ✅ Default fallback image


# ✅ API: Fetch News & Store in DB
@app.get("/fetch-news/")
async def fetch_news():
    try:
        fetch_and_store_news()
        return {"message": "News fetched and stored successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

# ✅ API: Get All Stored Articles
@app.get("/articles/")
async def get_articles():
    try:
        delete_old_articles()
        articles = list(articles_collection.find({}, {"_id": 0}))
        return {"articles": articles} if articles else {"message": "No articles found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching articles: {str(e)}")

# ✅ Health Check API
@app.get("/health/")
async def health_check():
    try:
        articles_collection.count_documents({})
        return {"status": "✅ Server & MongoDB are running!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB Connection Error: {str(e)}")

# ✅ Background Task: Auto-Clean Old Articles
async def scheduled_cleanup():
    while True:
        await asyncio.sleep(3600)
        delete_old_articles()

async def scheduled_news_fetch():
    while True:
        print("📰 Fetching and storing news automatically...")
        fetch_and_store_news()
        await asyncio.sleep(1800)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(scheduled_news_fetch())
    asyncio.create_task(scheduled_cleanup())


# ✅ Root API
@app.get("/")
async def root():
    return {"message": "Welcome to AI News Scraper! Use /articles/ to get news."}

@app.get("/favicon.ico")
async def favicon():
    return {"message": "No favicon available"}
