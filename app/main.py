import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import select, Session
from .core.settings import Settings
from .core.db import get_engine, init_db
from .core.models import Source
from .api.routes import router as api_router
from .ui.pages import router as pages_router
from .services.scheduler import start_scheduler

settings = Settings()
engine = get_engine(settings)
init_db(engine)

def migrate():
    if settings.db_url.startswith("sqlite"):
        with engine.connect() as conn:
            cols = [row[1] for row in conn.exec_driver_sql("PRAGMA table_info(items);").fetchall()]
            if "read_at" not in cols:
                conn.exec_driver_sql("ALTER TABLE items ADD COLUMN read_at TIMESTAMP NULL;")
                conn.commit()

def seed_sources():
    with Session(engine) as s:
        exists = s.exec(select(Source)).first()
        if exists:
            return
        defaults = [
            {
                "name": "WDW News Today",
                "slug": "wdwnt",
                "home_url": "https://wdwnt.com",
                "strategy_config": {
                    "strategies": [
                        {"type": "rss", "url": "https://wdwnt.com/feed/"},
                        {"type": "sitemap", "url": "https://wdwnt.com/wp-sitemap.xml"},
                        {"type": "html_list", "url": "https://wdwnt.com/",
                         "list_selector": ".td-module-title a",
                         "article": {"title_selector":"h1.entry-title","published_selector":"time[datetime]","body_selector":"div.td-post-content"}
                        }
                    ]
                },
                "crawl_interval_minutes": 10,
                "rate_limit_per_min": 20,
            },
            {
                "name": "BlogMickey",
                "slug": "blogmickey",
                "home_url": "https://blogmickey.com",
                "strategy_config": {
                    "strategies": [
                        {"type": "rss", "url": "https://blogmickey.com/feed/"},
                        {"type": "sitemap", "url": "https://blogmickey.com/wp-sitemap.xml"},
                        {"type": "html_list", "url": "https://blogmickey.com/",
                         "list_selector": ".td-module-title a, .td-ss-main-content .entry-title a",
                         "article": {"title_selector":"h1.entry-title","published_selector":"time[datetime]","body_selector":"div.td-post-content, article .entry-content"}
                        }
                    ]
                },
                "crawl_interval_minutes": 10,
                "rate_limit_per_min": 20,
            },
            {
                "name": "Laughing Place",
                "slug": "laughingplace",
                "home_url": "https://www.laughingplace.com",
                "strategy_config": {
                    "strategies": [
                        {"type": "rss", "url": "https://www.laughingplace.com/feed/"},
                        {"type": "sitemap", "url": "https://www.laughingplace.com/sitemap_index.xml"},
                        {"type": "html_list", "url": "https://www.laughingplace.com/",
                         "list_selector": "article h2 a, article h3 a, .post h2 a",
                         "article": {"title_selector":"article h1, .single-post h1","published_selector":"time[datetime]","body_selector":"article .entry-content, article .content, .post .entry-content"}
                        }
                    ]
                },
                "crawl_interval_minutes": 10,
                "rate_limit_per_min": 20,
            },
            {
                "name": "Appear (Insights)",
                "slug": "appear",
                "home_url": "https://www.allears.net",
                "strategy_config": {
                    "strategies": [
                        {"type": "sitemap", "url": "https://www.allears.net/sitemap.xml"},
                        {"type": "html_list", "url": "https://www.allears.net/insights/",
                         "list_selector": "a[href*='/insight/'], article a[href]",
                         "article": {"title_selector":"article h1","published_selector":"time[datetime]","body_selector":"article, .entry-content"}
                        }
                    ]
                },
                "crawl_interval_minutes": 30,
                "rate_limit_per_min": 10,
            },
        ]
        for d in defaults:
            s.add(Source(**d))
        s.commit()

migrate()
seed_sources()

app = FastAPI(title="TheMikeDrop")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages_router)
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def _start_sched():
    start_scheduler(app)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)
