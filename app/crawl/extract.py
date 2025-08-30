from trafilatura import extract as extract_main
from bs4 import BeautifulSoup
from dateutil import parser as dtp
from typing import Optional, Dict

def extract_article(html: str, selectors: Optional[Dict] = None) -> Dict:
    out: Dict = {}
    if not html:
        return out

    try:
        txt = extract_main(html, include_comments=False, include_tables=False)
        if txt and len((txt or '').split()) > 50:
            out["full_text"] = txt
    except Exception:
        pass

    if selectors:
        soup = BeautifulSoup(html, "lxml")
        def pick(sel):
            return soup.select_one(sel) if sel else None

        tsel = selectors.get("title_selector") if isinstance(selectors, dict) else None
        psel = selectors.get("published_selector") if isinstance(selectors, dict) else None
        bsel = selectors.get("body_selector") if isinstance(selectors, dict) else None

        if tsel:
            n = pick(tsel)
            if n:
                out["title"] = n.get_text(strip=True)

        if bsel and not out.get("full_text"):
            n = pick(bsel)
            if n:
                out["full_text"] = n.get_text(" ", strip=True)

        if psel:
            n = pick(psel)
            if n:
                dt = n.get("datetime") or n.get_text(strip=True)
                try:
                    out["published_at"] = dtp.parse(dt)
                except Exception:
                    pass

    return out
