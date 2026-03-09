from __future__ import annotations

from datetime import datetime
from typing import Iterable

from sqlalchemy import DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from config.settings import DATABASE_URL
from models.job import JobSchema


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


engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create database tables if they do not exist."""

    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()


def save_jobs(jobs: Iterable[JobSchema], session: Session | None = None) -> int:
    """Persist validated jobs while skipping duplicates by URL."""

    parsed_jobs = list(jobs)
    if not parsed_jobs:
        return 0

    owns_session = session is None
    db_session = session or get_session()

    try:
        urls = [str(job.url) for job in parsed_jobs]
        existing_urls = set(
            db_session.scalars(select(Job.url).where(Job.url.in_(urls))).all()
        )
        seen_urls = set(existing_urls)

        new_records: list[Job] = []
        for job in parsed_jobs:
            job_url = str(job.url)
            if job_url in seen_urls:
                continue

            new_records.append(
                Job(
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    description=job.description,
                    url=job_url,
                    published=job.published,
                    source=job.source,
                )
            )
            seen_urls.add(job_url)

        db_session.add_all(new_records)
        db_session.commit()
        return len(new_records)
    except Exception:
        db_session.rollback()
        raise
    finally:
        if owns_session:
            db_session.close()
