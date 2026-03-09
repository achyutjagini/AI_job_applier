from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl, ValidationError
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config.settings import SOURCE_NAME

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    company: Mapped[str | None] = mapped_column(String(256), nullable=True)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    published: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class JobSchema(BaseModel):
    id: int | None = None
    title: str
    company: str | None = None
    location: str | None = None
    description: str | None = None
    url: HttpUrl
    published: datetime | None = None
    source: str = Field(default=SOURCE_NAME)
    skills: list[str] = Field(default_factory=list)
    score: float = 0.0


def parse_jobs(raw_jobs: list[dict[str, Any]]) -> list[JobSchema]:
    """Validate raw Arbetsformedlingen API hits into JobSchema objects."""

    parsed_jobs: list[JobSchema] = []
    for raw_job in raw_jobs:
        try:
            parsed_jobs.append(
                JobSchema(
                    title=raw_job.get("headline") or "Untitled job",
                    company=_read_nested(raw_job, "employer", "name"),
                    location=_read_nested(raw_job, "workplace_address", "city"),
                    description=_read_nested(raw_job, "description", "text"),
                    url=raw_job["webpage_url"],
                    published=_parse_published(raw_job),
                )
            )
        except (KeyError, ValidationError) as exc:
            logger.warning("Skipping invalid Arbetsformedlingen job payload: %s", exc)
    return parsed_jobs


def _read_nested(payload: dict[str, Any], *keys: str) -> str | None:
    value: Any = payload
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value if isinstance(value, str) and value else None


def _parse_published(raw_job: dict[str, Any]) -> datetime | None:
    for key in ("publication_date", "published", "last_publication_date"):
        value = raw_job.get(key)
        if not isinstance(value, str) or not value:
            continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            logger.debug("Unrecognized published date format for key %s: %s", key, value)
    return None
