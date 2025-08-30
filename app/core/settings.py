import os
from pydantic import BaseModel
from typing import Optional

class Settings(BaseModel):
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "8080"))
    db_url: str = os.getenv("DB_URL", "sqlite:///./data/crawler.db")
    user_agent: str = os.getenv("USER_AGENT", "TheMikeDrop/1.0")
    slack_webhook: Optional[str] = os.getenv("SLACK_WEBHOOK_URL") or None
    crawl_default_interval_min: int = int(os.getenv("CRAWL_INTERVAL_MINUTES", "5"))
    rate_limit_per_min: int = int(os.getenv("RATE_LIMIT_PER_MIN", "20"))
