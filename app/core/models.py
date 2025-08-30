from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, UniqueConstraint

class Source(SQLModel, table=True):
    __tablename__ = "sources"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    slug: str = Field(index=True, unique=True)
    home_url: str
    enabled: bool = True
    crawl_interval_minutes: int = 10
    rate_limit_per_min: int = 20
    user_agent: Optional[str] = None
    strategy_config: dict = Field(sa_column=Column(JSON))
    items: list["Item"] = Relationship(back_populates="source")

class Item(SQLModel, table=True):
    __tablename__ = "items"
    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="sources.id", index=True)
    url: str
    url_canonical: str
    title: Optional[str] = None
    authors: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    published_at: Optional[datetime] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    summary: Optional[str] = None
    full_text: Optional[str] = None
    tags: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    lang: Optional[str] = None
    content_hash: Optional[str] = Field(default=None, index=True)
    url_hash: str = Field(index=True)
    is_duplicate: bool = False
    duplicate_of: Optional[int] = None
    read_at: Optional[datetime] = None
    source: "Source" = Relationship(back_populates="items")
    __table_args__ = (UniqueConstraint("url_hash", name="uq_items_url_hash"), )
