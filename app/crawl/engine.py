from sqlmodel import select
from ..core.models import Source, Item
from ..utils import sha256, canonicalize_url, to_utc_naive
from .fetch import Fetcher
from .strategies import parse_rss, parse_sitemap, parse_html_list
from .extract import extract_article
from .dedup import simhash_text, hamming

async def process_source(session, source: Source) -> int:
    cfg = source.strategy_config or {}
    strategies = cfg.get("strategies", [])
    if not strategies:
        return 0

    fetcher = Fetcher(user_agent=source.user_agent or "TheMikeDrop/1.0",
                      rate_limit_per_min=source.rate_limit_per_min or 20)
    new_count = 0

    for strat in strategies:
        stype = strat.get("type")
        url = strat.get("url")
        if not (stype and url):
            continue

        body = await fetcher.get_text(url)
        if not body:
            continue

        if stype == "rss":
            candidates = list(parse_rss(body))
        elif stype == "sitemap":
            candidates = list(parse_sitemap(body))
        elif stype == "html_list":
            candidates = list(parse_html_list(body, source.home_url, strat.get("list_selector","a"), strat.get("resolve_to","href")))
        else:
            candidates = []

        selectors = strat.get("article") if stype == "html_list" else {}

        for cand in candidates:
            url_c = canonicalize_url(cand["url"])
            url_hash = sha256(url_c)
            if session.exec(select(Item).where(Item.url_hash == url_hash)).first():
                continue

            html = await fetcher.get_text(url_c)
            article_fields = extract_article(html or "", selectors)

            title = article_fields.get("title") or cand.get("title")
            full_text = article_fields.get("full_text")
            pub = to_utc_naive(article_fields.get("published_at") or cand.get("published_at"))
            content_hash_hex = None
            if full_text:
                content_hash_hex = hex(simhash_text(full_text))

            is_dup = False
            dup_of = None
            if content_hash_hex:
                try_hash = int(content_hash_hex, 16)
                recent = session.exec(select(Item.id, Item.content_hash).order_by(Item.id.desc()).limit(500)).all()
                for iid, ch in recent:
                    if not ch:
                        continue
                    try:
                        other = int(ch, 16)
                        if hamming(try_hash, other) <= 3:
                            is_dup = True
                            dup_of = iid
                            break
                    except Exception:
                        continue

            row = Item(
                source_id=source.id,
                url=cand["url"],
                url_canonical=url_c,
                title=title,
                published_at=pub,
                summary=cand.get("summary"),
                full_text=full_text,
                content_hash=content_hash_hex,
                url_hash=url_hash,
                is_duplicate=is_dup,
                duplicate_of=dup_of,
            )
            session.add(row)
            try:
                session.commit()
                if not row.is_duplicate:
                    new_count += 1
            except Exception:
                session.rollback()

        if new_count or candidates:
            break

    return new_count
