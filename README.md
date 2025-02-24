# Automated AI News Generator

## Overview  
[![YouTube Video Demo](https://github.com/user-attachments/assets/e6f2a97c-8214-47cd-9510-5e58295c4f3a)](https://youtu.be/D0AkONTA-Qw)  

**[Demo Link](https://youtu.be/D0AkONTA-Qw)**

The **Automated AI News Generator** is an autonomous AI agent designed to search, summarize, optimize, and publish news articles across various topics, including current events, crime, sports, politics, and more. The system operates at both global and local levels, ensuring comprehensive coverage and accurate news delivery.

## Features

### 1. **Automated Web Crawling & Data Extraction**

### 2. **Summarization & Content Generation**

### 4. **Automated Publishing**

## Additional Features (Bonus Points Implemented)

✅ **Use of Open-Source LLMs** - Self-hosted open-source AI models used instead of proprietary APIs.

✅ **Image Generation** - AI-generated infographics and visuals enhance blog posts using another open source LLM 

✅ **Multilingual Support** - Articles published in multiple languages (e.g., Hindi and English).

✅ **User Engagement Metrics** - vercel analytics and tools used 

## Tech Stack

### **Backend**
- **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python 3.7+.
- **Uvicorn**: ASGI server to run the FastAPI application.

### **AI/ML**
- **Transformers (Hugging Face)**: Used for text summarization with the `facebook/bart-large-cnn` model.
- **Google Translate API**: Used for translating English summaries into Hindi.

### **Image Generation**
- **Stability AI API**: Used for generating images from text prompts.
- **Unsplash**: Fallback for image generation if Stability AI fails.

### **Web Scraping**
- **BeautifulSoup**: Used for parsing HTML and scraping news articles from websites.
- **Requests**: Used for making HTTP requests to fetch web pages.

### **Database**
- **MongoDB**: NoSQL database used for storing processed news articles.
- **PyMongo**: Python driver for interacting with MongoDB.

### **Background Tasks**
- **Asyncio**: Used for running asynchronous background tasks (e.g., periodic news fetching and cleanup).

### **Logging**
- **Python Logging**: Used for logging application events and errors.


## Installation & Setup
```sh
# Clone the Repository
git clone https://github.com/your-repo/ai-news-generator.git
cd backend

# Install Dependencies
pip install -r requirements.txt 

# Set Up Environment Variables
set your stability api key a
set the mongo connection string

#Run the backend
uvicorn backend.main:app --reload

#Go to the frontend directory
cd ..
cd frontend
npm i
npm run dev

```
## Workflow explanation 

This FastAPI application is designed to scrape news articles from various sources, process them (summarize, translate, and generate images), and store them in a MongoDB database. It also provides endpoints to fetch the processed articles and includes background tasks for periodic news fetching and cleanup.

---

## **Workflow Overview**

1. **Initialization**:
   - The FastAPI app is initialized with CORS middleware to allow requests from `http://localhost:3000`.
   - A summarization pipeline (`facebook/bart-large-cnn`) and a Google Translate translator are initialized.
   - A list of news sources (`SOURCES`) is defined, each containing a URL and a category.

2. **Image Generation**:
   - The `generate_image_from_text` function uses the Stability AI API to generate an image based on the article's title.
   - If the API fails, it falls back to using Unsplash or a placeholder image.

3. **News Scraping**:
   - The `scrape_news` function scrapes news articles from a given URL using `BeautifulSoup`.
   - It extracts the title, URL, summary, and category of each article and stores them in a list.

4. **Article Processing**:
   - The `process_article` function processes each scraped article:
     - Generates a summary using the summarization pipeline.
     - Translates the summary into Hindi using the Google Translate API.
     - Generates an image using the `generate_image_from_text` function.
     - Returns the processed article with the new fields.

5. **Fetching and Storing News**:
   - The `fetch_and_store_news` function:
     - Iterates through the `SOURCES` list and scrapes articles.
     - Checks if the article already exists in the MongoDB collection.
     - Processes and stores new articles in the database.

6. **API Endpoints**:
   - `/fetch-news/`: Triggers the `fetch_and_store_news` function to fetch and store new articles.
   - `/articles/`: Retrieves all stored articles from the MongoDB collection.
   - `/health/`: Health check endpoint to verify the server and MongoDB connection.
   - `/`: Root endpoint with a welcome message.

7. **Background Tasks**:
   - `scheduled_news_fetch`: Fetches and stores news articles every 30 minutes.
   - `scheduled_cleanup`: Cleans up old articles from the database every hour.
   - These tasks are started automatically when the application starts.

---


## Team

- **Lakshya Jain**  
  [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/lakshya-jain-655bb8244/)  
  [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/lakshyajn)  

- **Kairvee Vaswani**  
  [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/kairveee/)  
  [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/kairveeehh)  

