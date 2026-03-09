from __future__ import annotations

import unittest

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from database.db import save_jobs
from models.job import Base, Job, JobSchema


class DatabaseDuplicateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:", future=True)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        Base.metadata.create_all(self.engine)
        self.session: Session = self.session_factory()

    def tearDown(self) -> None:
        self.session.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_save_jobs_skips_duplicate_urls(self) -> None:
        duplicate_job = JobSchema(
            title="Backend Engineer",
            company="Acme",
            location="Stockholm",
            description="Build APIs",
            url="https://example.com/jobs/duplicate",
        )

        first_inserted = save_jobs([duplicate_job], self.session)
        second_inserted = save_jobs([duplicate_job], self.session)
        stored_count = self.session.scalar(select(func.count()).select_from(Job))

        self.assertEqual(first_inserted, 1)
        self.assertEqual(second_inserted, 0)
        self.assertEqual(stored_count, 1)


if __name__ == "__main__":
    unittest.main()
