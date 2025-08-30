from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import select
from ..core.models import Source
from ..core.db import get_session
from ..crawl.engine import process_source
from ..services.notify import notify_slack

def start_scheduler(app):
    from ..main import engine, settings
    sched = AsyncIOScheduler(timezone="UTC")

    async def run_once():
        from ..main import engine
        with get_session(engine) as s:
            sources = s.exec(select(Source).where(Source.enabled == True)).all()
            for src in sources:
                try:
                    new_count = await process_source(s, src)
                    if new_count:
                        notify_slack(f"🆕 {new_count} new items from {src.slug}")
                except Exception as e:
                    print(f"[{src.slug}] run error:", e)

    sched.add_job(lambda: app.loop.create_task(run_once()), "interval", minutes=settings.crawl_default_interval_min, id="crawl_loop")
    sched.start()
    return sched
