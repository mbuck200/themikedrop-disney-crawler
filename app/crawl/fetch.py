import asyncio, aiohttp
from typing import Optional

class Fetcher:
    def __init__(self, user_agent: str, rate_limit_per_min: int = 20):
        self.sem = asyncio.Semaphore(max(1, rate_limit_per_min // 2))
        self.headers = {"User-Agent": user_agent}

    async def get_text(self, url: str, timeout: int = 25) -> Optional[str]:
        async with self.sem:
            async with aiohttp.ClientSession(headers=self.headers) as s:
                try:
                    async with s.get(url, timeout=timeout) as r:
                        if r.status == 200:
                            ctype = r.headers.get("Content-Type", "")
                            if "text" in ctype or "xml" in ctype or "json" in ctype:
                                return await r.text()
                except Exception:
                    return None
        return None
