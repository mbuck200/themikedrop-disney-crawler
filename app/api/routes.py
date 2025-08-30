from fastapi import APIRouter, HTTPException
from sqlmodel import select, delete
from ..core.models import Source, Item
from ..core.db import get_session
from ..crawl.engine import process_source
from sqlalchemy import asc, desc, or_
from ..utils import ny_day_bounds
from datetime import datetime

router = APIRouter()

@router.get("/sites")
def list_sites():
    from ..main import engine
    with get_session(engine) as s:
        return s.exec(select(Source)).all()

@router.post("/sites")
def create_site(site: Source):
    from ..main import engine
    with get_session(engine) as s:
        s.add(site); s.commit(); s.refresh(site)
        return site

@router.patch("/sites/{site_id}")
def update_site(site_id: int, patch: dict):
    from ..main import engine
    with get_session(engine) as s:
        src = s.get(Source, site_id)
        if not src: raise HTTPException(404, "not found")
        for k, v in patch.items():
            setattr(src, k, v)
        s.add(src); s.commit(); s.refresh(src)
        return src

@router.delete("/sites/{site_id}")
def delete_site(site_id: int):
    from ..main import engine
    with get_session(engine) as s:
        src = s.get(Source, site_id)
        if not src: raise HTTPException(404, "not found")
        s.exec(delete(Item).where(Item.source_id == site_id))
        s.commit()
        s.delete(src); s.commit()
        return {"ok": True, "deleted_site_id": site_id}

@router.post("/sites/{site_id}/run")
async def run_site_now(site_id: int):
    from ..main import engine
    with get_session(engine) as s:
        src = s.get(Source, site_id)
        if not src: raise HTTPException(404, "not found")
        count = await process_source(s, src)
        return {"new_items": count}

@router.post("/sites/run_all")
async def run_all_sites():
    from ..main import engine
    new_total = 0
    with get_session(engine) as s:
        sources = s.exec(select(Source).where(Source.enabled == True)).all()
        for src in sources:
            try:
                cnt = await process_source(s, src)
                new_total += (cnt or 0)
            except Exception:
                continue
    return {"new_items": new_total}

@router.get("/items")
def list_items(
    site: str | None = None,
    q: str | None = None,
    sort: str = "fetched",
    dir: str = "desc",
    date_range: str = "all",
    read: str = "all",
    limit: int = 100
):
    from ..main import engine
    with get_session(engine) as s:
        base = select(Item, Source).where(Source.id == Item.source_id)
        if site:
            base = base.where(Source.slug == site)
        if q:
            like = f"%{q}%"
            base = base.where(or_(Item.title.ilike(like), Item.summary.ilike(like), Item.full_text.ilike(like)))

        start, end = ny_day_bounds((date_range or "all").lower())
        if start:
            base = base.where(Item.published_at >= start)
        if end:
            base = base.where(Item.published_at < end)

        r = (read or "all").lower()
        if r == "read":
            base = base.where(Item.read_at.is_not(None))
        elif r == "unread":
            base = base.where(Item.read_at.is_(None))

        key = (sort or "fetched").lower()
        direction = (dir or "desc").lower()
        if key == "published":
            col = Item.published_at
        elif key == "source":
            col = Source.slug
        elif key == "title":
            col = Item.title
        else:
            col = Item.fetched_at
        order = desc(col) if direction == "desc" else asc(col)

        rows = s.exec(base.order_by(order).limit(limit)).all()
        return [
            {
                "id": it.id,
                "source_id": it.source_id,
                "source_slug": src.slug,
                "title": it.title,
                "url": it.url,
                "published_at": it.published_at.isoformat() if it.published_at else None,
                "fetched_at": it.fetched_at.isoformat() if it.fetched_at else None,
                "summary": it.summary,
                "is_duplicate": it.is_duplicate,
                "read": bool(it.read_at),
            }
            for it, src in rows
        ]

@router.patch("/items/{item_id}/read")
def mark_read(item_id: int, body: dict):
    from ..main import engine
    want = bool(body.get("read", True))
    with get_session(engine) as s:
        it = s.get(Item, item_id)
        if not it: raise HTTPException(404, "not found")
        from datetime import datetime
        it.read_at = datetime.utcnow() if want else None
        s.add(it); s.commit(); s.refresh(it)
        return {"id": it.id, "read": bool(it.read_at)}
