from pydantic import BaseModel
from typing import List
from datetime import datetime

class Article(BaseModel):
    title: str
    summary: str
    summary_hindi: str
    keywords: List[str]
    image_url: str
    timestamp: datetime
