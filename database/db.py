from __future__ import annotations

from typing import Iterable

from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from config.settings import DATABASE_URL
from models.job import Base, Job, JobSchema


engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create database tables if they do not exist."""

    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    return SessionLocal()


def list_jobs(session: Session | None = None) -> list[JobSchema]:
    """Load persisted jobs from the database as JobSchema objects."""

    owns_session = session is None
    db_session = session or get_session()

    try:
        rows = db_session.scalars(select(Job).order_by(Job.id.asc())).all()
        return [
            JobSchema(
                id=row.id,
                title=row.title,
                company=row.company,
                location=row.location,
                description=row.description,
                url=row.url,
                published=row.published,
                source=row.source,
            )
            for row in rows
        ]
    finally:
        if owns_session:
            db_session.close()


def save_jobs(jobs: Iterable[JobSchema], session: Session | None = None) -> int:
    """Persist validated jobs while skipping duplicates by URL."""

    parsed_jobs = list(jobs)
    if not parsed_jobs:
        return 0

    owns_session = session is None
    db_session = session or get_session()

    try:
        inserted_count = 0
        for job in parsed_jobs:
            job_url = str(job.url)
            existing = db_session.scalar(select(Job.id).where(Job.url == job_url))
            if existing is not None:
                continue

            db_session.add(
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
            inserted_count += 1

        try:
            db_session.commit()
        except IntegrityError:
            db_session.rollback()
            inserted_count = 0
            for job in parsed_jobs:
                job_url = str(job.url)
                existing = db_session.scalar(select(Job.id).where(Job.url == job_url))
                if existing is not None:
                    continue

                try:
                    db_session.add(
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
                    db_session.commit()
                    inserted_count += 1
                except IntegrityError:
                    db_session.rollback()
            return inserted_count

        return inserted_count
    except Exception:
        db_session.rollback()
        raise
    finally:
        if owns_session:
            db_session.close()
