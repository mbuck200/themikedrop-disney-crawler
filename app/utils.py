import hashlib
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from datetime import datetime, timedelta
from dateutil import tz

def canonicalize_url(url: str) -> str:
    parts = urlsplit(url)
    q = [(k, v) for k, v in parse_qsl(parts.query) if not k.lower().startswith("utm_")]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), ""))

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def to_utc_naive(dt):
    """Convert timezone-aware dt to UTC and strip tz; leave naive as-is (assume already UTC)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(tz.UTC).replace(tzinfo=None)

def ny_day_bounds(kind: str):
    """Return (start_utc_naive, end_utc_naive) for NY calendar buckets."""
    ny = tz.gettz("America/New_York")
    now_utc = datetime.utcnow().replace(tzinfo=tz.UTC)
    now_ny = now_utc.astimezone(ny)

    today_start_ny = now_ny.replace(hour=0, minute=0, second=0, microsecond=0)

    if kind == "today":
        start_ny, end_ny = today_start_ny, now_ny
    elif kind == "yesterday":
        start_ny = today_start_ny - timedelta(days=1)
        end_ny = today_start_ny
    elif kind == "7d":
        start_ny = now_ny - timedelta(days=7)
        end_ny = now_ny
    elif kind == "30d":
        start_ny = now_ny - timedelta(days=30)
        end_ny = now_ny
    else:
        return (None, None)

    start_utc = start_ny.astimezone(tz.UTC).replace(tzinfo=None)
    end_utc = end_ny.astimezone(tz.UTC).replace(tzinfo=None)
    return (start_utc, end_utc)
