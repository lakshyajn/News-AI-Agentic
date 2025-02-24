from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
from googletrans import Translator
import requests
import asyncio
import torch
from diffusers import StableDiffusionPipeline
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
        image_prompt = article['title'].split()[:5]  # Use first 5 words of title
        image_url = generate_image_from_text(article['title'])    
        article["image_url"] = image_url
       
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



STABILITY_API_KEY = "sk-aqmyHE3qY1eKl7CMbuosSE5K7tgxyAVl81cEYso8eAeAdZMS"  # Replace with your actual API key
STABILITY_API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

def generate_image_from_text(text):
    """
    Generate an image using Stability AI
    """
    print(f"Generating image for text: {text}")  # Debug log
    
    try:
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {STABILITY_API_KEY}"
        }
        
        payload = {
            "text_prompts": [
                {
                    "text": f"professional photojournalistic photograph of {text}, high quality, realistic, 4k, news style",
                    "weight": 1
                }
            ],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }
        
        print("Sending request to Stability AI...")  # Debug log
        response = requests.post(STABILITY_API_URL, headers=headers, json=payload)
        print(f"Stability AI Response Status: {response.status_code}")  # Debug log
        
        if response.status_code == 200:
            data = response.json()
            
            if 'artifacts' in data and len(data['artifacts']) > 0:
                # Get the base64 image and convert to a data URL
                image_base64 = data['artifacts'][0]['base64']
                image_url = f"data:image/png;base64,{image_base64}"
                print("Successfully generated image")  # Debug log
                return image_url
            
        print(f"API Response: {response.text}")  # Debug log
        
        # Fallback to Unsplash if Stability AI fails
        print("Falling back to Unsplash...")  # Debug log
        return f"https://source.unsplash.com/1200x800/?{text.replace(' ', ',')}"
        
    except Exception as e:
        print(f"Error in image generation: {str(e)}")  # Debug log
        return "https://via.placeholder.com/1200x800?text=News+Image"

# Test endpoint
@app.get("/test-image-generation/{text}")
async def test_image_generation(text: str):
    """
    Test endpoint to verify image generation
    """
    try:
        image_url = generate_image_from_text(text)
        return {
            "status": "success",
            "input_text": text,
            "generated_url": image_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
