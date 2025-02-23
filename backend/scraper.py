import scrapy
from scrapy.crawler import CrawlerProcess
from backend.db import articles_collection

class NewsSpider(scrapy.Spider):
    name = "news_spider"
    start_urls = ["https://www.bbc.com/news", "https://www.aljazeera.com/"]

    def parse(self, response):
        for article in response.css("article"):
            title = article.css("h3 a::text").get()
            link = response.urljoin(article.css("h3 a::attr(href)").get())

            if title and link:
                yield {"title": title, "url": link}

# Function to start Scrapy crawler
def run_scraper():
    process = CrawlerProcess(settings={"FEEDS": {"news.json": {"format": "json"}}})
    process.crawl(NewsSpider)
    process.start()
