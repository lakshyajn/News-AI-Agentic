from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
from googletrans import Translator
import requests
import asyncio
from datetime import datetime, timedelta
from backend.db import articles_collection
from bs4 import BeautifulSoup
from time import sleep
from ratelimit import limits, sleep_and_retry

app = FastAPI()

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_ARTICLES = 24 

@sleep_and_retry
@limits(calls=1, period=2)  # 1 call every 2 seconds
def rate_limited_request(url, headers):
    return requests.get(url, headers=headers, timeout=10)

# ✅ AI Summarization Model
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# ✅ Translator (English to Hindi)
translator = Translator()

# ✅ News Sources
SOURCES = [
    {
        "url": "https://www.bbc.com/news",
        "category": "World",
        "article_selector": "article.gs-c-promo"  # Add specific CSS selector
    },
    {
        "url": "https://www.aljazeera.com/",
        "category": "Politics",
        "article_selector": "article.gc"
    },
    {
        "url": "https://timesofindia.indiatimes.com/",
        "category": "India",
        "article_selector": "div.main-content article"
    }
]

# ✅ Stability AI API Key & URL
STABILITY_API_KEY = "sk-FVO06A2V2ImPVDvP0TOZmZ6yB5vfQdOu1Dc4ATbVZrj4QLSC"  
STABILITY_API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

# ✅ Clear previous data (Run only once)
def clear_database():
    articles_collection.delete_many({})
    print("🗑️ Old data cleared!")

clear_database()  # ❗ Run once to reset the database

# ✅ Scrape News
def scrape_news(source_url, category="General"):
    try:
        print(f"🔍 Attempting to scrape: {source_url}")  # Debug print
        
        response = requests.get(source_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }, timeout=10)
        
        # Check response status
        if response.status_code != 200:
            print(f"⚠️ Failed to fetch {source_url}: Status code {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        articles = []
        article_elements = soup.find_all("article")
        print(f"📑 Found {len(article_elements)} article elements")  # Debug print
        
        for news_item in article_elements:
            try:
                title_tag = news_item.find(["h1", "h2", "h3"])
                link_tag = news_item.find("a")
                summary_tag = news_item.find("p")

                if title_tag and link_tag:
                    title = title_tag.text.strip()
                    url = requests.compat.urljoin(source_url, link_tag["href"])
                    summary = summary_tag.text.strip() if summary_tag else "No summary available."

                    articles.append({
                        "title": title,
                        "url": url,
                        "summary": summary,
                        "category": category,
                        "timestamp": datetime.utcnow(),
                    })
            except Exception as item_error:
                print(f"⚠️ Error processing individual article: {str(item_error)}")
                continue

        print(f"✅ Successfully scraped {len(articles)} articles from {source_url}")
        return articles
        
    except requests.exceptions.Timeout:
        print(f"🚨 Timeout while scraping {source_url}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"🚨 Request failed for {source_url}: {str(e)}")
        return []
    except Exception as e:
        print(f"🚨 Unexpected error scraping {source_url}: {str(e)}")
        return []

# ✅ Summarization, Translation & Image Generation
def process_article(article):
    try:
        # ✅ Fetch full article text
        response = requests.get(article["url"])
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        full_text = " ".join([p.text for p in paragraphs if len(p.text) > 50])

        # ✅ If article is **too short**, don't summarize (prevents 'Index out of range')
        if not full_text or len(full_text.split()) < 50:
            print(f"⚠️ {article['title']} is too short, using original summary.")
            summary = article["summary"]
        else:
            try:
                summary = summarizer(full_text, max_length=200, min_length=50, do_sample=False)[0]["summary_text"]
            except Exception as e:
                print(f"⚠️ Summarization failed for {article['title']} - {str(e)}")
                summary = full_text[:200] + "..."  # ✅ Use first 200 characters as fallback summary

        summary_hindi = translator.translate(summary, src="en", dest="hi").text

        # ✅ Generate unique AI image (only retries once)
        image_url = generate_image_from_text(article["title"])

        article["summary"] = summary
        article["summary_hindi"] = summary_hindi
        article["image_url"] = image_url

        return article
    except Exception as e:
        print(f"🚨 Error processing article: {str(e)}")
        return None  # Skip article if processing fails

# ✅ Fetch & Store News (Newest First)
def fetch_and_store_news():
    try:
        # Get current count
        current_count = articles_collection.count_documents({})
        
        # If we have too many articles, remove oldest ones
        if current_count >= MAX_ARTICLES:
            pipeline = [
                {"$sort": {"timestamp": 1}},  # Sort oldest first
                {"$limit": current_count - MAX_ARTICLES + 5}  # Number to remove
            ]
            
            old_articles = articles_collection.aggregate(
                pipeline,
                allowDiskUse=True
            )
            
            # Delete the old articles
            for article in old_articles:
                articles_collection.delete_one({"_id": article["_id"]})
                
            print(f"🗑️ Removed oldest articles to maintain limit of {MAX_ARTICLES}")

        new_articles = []
        for source in SOURCES:
            if articles_collection.count_documents({}) >= MAX_ARTICLES:
                print("📊 Reached maximum article limit")
                return new_articles
                
            scraped_articles = scrape_news(source["url"], source["category"])
            for article in scraped_articles:
                existing = articles_collection.find_one({"title": article["title"]})
                if not existing and articles_collection.count_documents({}) < MAX_ARTICLES:
                    processed_article = process_article(article)
                    if processed_article:
                        articles_collection.insert_one(processed_article)
                        new_articles.insert(0, processed_article)
        
        return new_articles
    except Exception as e:
        print(f"🚨 Error in fetch_and_store_news: {str(e)}")
        return []


# ✅ Generate Unique AI Images (Retries once if fails)
def generate_image_from_text(text):
    try:
        print(f"🎨 Attempting to generate image for: {text}")
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",  # Added content-type header
            "Authorization": f"Bearer {STABILITY_API_KEY}"
        }
        
        payload = {
            "text_prompts": [{"text": f"High-quality journalistic photo of {text}", "weight": 1}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }

        response = requests.post(
            STABILITY_API_URL, 
            headers=headers, 
            json=payload,
            timeout=30  # Added timeout
        )
        
        print(f"📡 Stability API Response Status: {response.status_code}")
        print(f"📡 Response Headers: {response.headers}")
        
        if response.status_code != 200:
            print(f"⚠️ API Error: {response.text}")
            raise Exception(f"API returned status code {response.status_code}")

        data = response.json()
        
        if "artifacts" in data and len(data["artifacts"]) > 0:
            return f"data:image/png;base64,{data['artifacts'][0]['base64']}"
        else:
            print("⚠️ No artifacts found in response")
            raise Exception("No image generated")

    except requests.exceptions.RequestException as e:
        print(f"🚨 Request failed: {str(e)}")
        return f"https://source.unsplash.com/1200x800/?{text.replace(' ', ',')}"
    except Exception as e:
        print(f"🚨 Error generating image: {str(e)}")
        return f"https://source.unsplash.com/1200x800/?{text.replace(' ', ',')}"

# ✅ API: Fetch News Every 2 Minutes
@app.get("/fetch-news/")
async def fetch_news():
    try:
        new_articles = fetch_and_store_news()
        return {"message": "New articles added", "new_articles": new_articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")

# ✅ API: Get All Stored Articles (Newest First)
@app.get("/articles/")
async def get_articles():
    try:
        # Create index on timestamp if it doesn't exist
        articles_collection.create_index([("timestamp", -1)])
        
        # Use a more efficient query approach
        pipeline = [
            {"$sort": {"timestamp": -1}},
            {"$limit": MAX_ARTICLES},
            {"$project": {"_id": 0}}
        ]
        
        articles = list(articles_collection.aggregate(
            pipeline,
            allowDiskUse=True  # Enable disk use in aggregation
        ))
        
        return {"articles": articles} if articles else {"message": "No articles found"}
    except Exception as e:
        print(f"🚨 Detailed error in get_articles: {str(e)}")  # Detailed error logging
        raise HTTPException(status_code=500, detail=f"Error fetching articles: {str(e)}")

# ✅ Delete Articles Older Than 24 Hours
async def delete_old_articles():
    expiry_time = datetime.utcnow() - timedelta(hours=24)
    articles_collection.delete_many({"timestamp": {"$lt": expiry_time}})
    print("🗑️ Old articles deleted!")

# ✅ Schedule Auto Fetch & Cleanup
async def scheduled_tasks():
    while True:
        print("🔄 Fetching new news...")
        fetch_and_store_news()
        await asyncio.sleep(120)  # 2 minutes = 120 seconds
        await delete_old_articles()  # ✅ Delete old news every 24 hours

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(scheduled_tasks())
