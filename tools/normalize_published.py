from sqlmodel import Session, select
from app.main import engine
from app.core.models import Item
from app.utils import to_utc_naive

with Session(engine) as s:
    rows = s.exec(select(Item).where(Item.published_at.is_not(None))).all()
    for it in rows:
        it.published_at = to_utc_naive(it.published_at)
        s.add(it)
    s.commit()
print("Normalized published_at to UTC-naive when tz-aware.")
