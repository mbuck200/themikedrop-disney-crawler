import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dtp
from typing import Iterable, Dict
from ..utils import canonicalize_url

def parse_rss(xml: str) -> Iterable[Dict]:
    feed = feedparser.parse(xml)
    for e in feed.entries:
        pub = e.get("published") or e.get("updated")
        yield {
            "url": canonicalize_url(e.link),
            "title": e.get("title"),
            "published_at": dtp.parse(pub) if pub else None,
            "summary": e.get("summary"),
        }

def parse_sitemap(xml: str) -> Iterable[Dict]:
    soup = BeautifulSoup(xml, "xml")
    for loc in soup.find_all("loc"):
        url = loc.text.strip()
        if url:
            yield {"url": canonicalize_url(url)}

def parse_html_list(html: str, base_url: str, list_selector: str, resolve_to: str = "href") -> Iterable[Dict]:
    soup = BeautifulSoup(html, "lxml")
    for a in soup.select(list_selector):
        href = a.get(resolve_to)
        if not href:
            continue
        if href.startswith("http"):
            yield {"url": canonicalize_url(href)}
        else:
            yield {"url": canonicalize_url(base_url.rstrip('/') + '/' + href.lstrip('/'))}
