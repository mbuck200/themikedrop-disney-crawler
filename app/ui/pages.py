from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select
from ..core.models import Source, Item
from ..core.db import get_session
from pathlib import Path
from sqlalchemy import asc, desc, or_
from ..utils import ny_day_bounds
from typing import Optional
import json


router = APIRouter()
TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

@router.get("/")
def home(request: Request):
    return RedirectResponse("/sites")

@router.get("/sites")
def sites(request: Request):
    from ..main import engine
    with get_session(engine) as s:
        rows = s.exec(select(Source)).all()
    return templates.TemplateResponse("sites.html", {"request": request, "sites": rows})

@router.get("/sites/new")
def site_new(request: Request):
    return templates.TemplateResponse("site_form.html", {"request": request, "site": None})

@router.post("/sites/save")
def site_save(request: Request,
              name: str = Form(...),
              slug: str = Form(...),
              home_url: str = Form(...),
              enabled: str = Form("on"),
              crawl_interval_minutes: int = Form(10),
              rate_limit_per_min: int = Form(20),
              user_agent: str = Form(""),
              strategy_config: str = Form(...)):
    from ..main import engine
    import json
    enabled_bool = enabled == "on"
    conf = json.loads(strategy_config)
    src = Source(name=name, slug=slug, home_url=home_url, enabled=enabled_bool,
                 crawl_interval_minutes=crawl_interval_minutes, rate_limit_per_min=rate_limit_per_min,
                 user_agent=(user_agent or None), strategy_config=conf)
    with get_session(engine) as s:
        s.add(src); s.commit()
    return RedirectResponse("/sites", status_code=303)

@router.get("/sites/{site_id}/edit")
def site_edit(request: Request, site_id: int):
    from ..main import engine
    with get_session(engine) as s:
        src = s.get(Source, site_id)
        if not src:
            return RedirectResponse("/sites", status_code=303)
        # Prettify JSON for the textarea
        strategy_json = json.dumps(src.strategy_config or {"strategies": []}, indent=2)
    return templates.TemplateResponse(
        "site_form.html",
        {"request": request, "site": src, "strategy_json": strategy_json}
    )

@router.post("/sites/{site_id}/update")
def site_update(
    request: Request,
    site_id: int,
    name: str = Form(...),
    slug: str = Form(...),
    home_url: str = Form(...),
    enabled: Optional[str] = Form(None),
    crawl_interval_minutes: int = Form(10),
    rate_limit_per_min: int = Form(20),
    user_agent: str = Form(""),
    strategy_config: str = Form(...)
):
    from ..main import engine
    enabled_bool = (enabled == "on")
    conf = json.loads(strategy_config)
    with get_session(engine) as s:
        src = s.get(Source, site_id)
        if not src:
            return RedirectResponse("/sites", status_code=303)
        src.name = name
        src.slug = slug
        src.home_url = home_url
        src.enabled = enabled_bool
        src.crawl_interval_minutes = crawl_interval_minutes
        src.rate_limit_per_min = rate_limit_per_min
        src.user_agent = (user_agent or None)
        src.strategy_config = conf
        s.add(src)
        s.commit()
    return RedirectResponse("/sites", status_code=303)

@router.get("/articles")
def articles(request: Request,
          site: str | None = None,
          q: str | None = None,
          sort: str = "fetched",
          dir: str = "desc",
          date_range: str = "all",
          read: str = "all",
          limit: int = 100):
    from ..main import engine
    with get_session(engine) as s:
        sites = s.exec(select(Source).order_by(Source.slug.asc())).all()
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

    return templates.TemplateResponse("articles.html", {
        "request": request,
        "rows": rows,
        "site": site,
        "q": q or "",
        "sites": sites,
        "sort": key,
        "dir": direction,
        "date_range": (date_range or "all").lower(),
        "read": (read or "all").lower(),
    })
