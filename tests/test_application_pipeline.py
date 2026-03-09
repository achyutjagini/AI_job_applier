from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import db
from generators import resume_generator
from models.job import Base
from pipeline.generate_applications import run_application_generation
from pipeline.process_jobs import run_processor
from pipeline.rank_jobs import run_ranker
from pipeline.scrape_jobs import run_scraper
from rankers import job_ranker


def test_pipeline_end_to_end(monkeypatch) -> None:
    db_path = Path.cwd() / "test_pipeline.db"
    applications_dir = Path.cwd() / "test_pipeline_applications"
    resume_path = Path.cwd() / "test_pipeline_resume.txt"

    engine = create_engine(f"sqlite:///{db_path.name}", future=True)
    session_local = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    class FakeScraper:
        def search_jobs(self, query: str, limit: int, max_pages: int):
            return [
                {
                    "headline": "Python Developer",
                    "employer": {"name": "Spotify"},
                    "workplace_address": {"city": "Stockholm"},
                    "description": {"text": "Python backend development with AWS"},
                    "webpage_url": "https://example.com/job/1",
                }
            ]

        def close(self) -> None:
            return None

    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", session_local)
    monkeypatch.setattr("pipeline.scrape_jobs.ArbetsformedlingenScraper", FakeScraper)
    monkeypatch.setattr(job_ranker, "embed_text", lambda text: [1.0, 0.0] if "python" in text.lower() else [0.0, 1.0])
    monkeypatch.setattr(resume_generator, "APPLICATIONS_DIR", str(applications_dir))
    monkeypatch.setattr("pipeline.generate_applications.APPLICATIONS_DIR", str(applications_dir))

    resume_path.write_text("Python backend engineer with AWS experience", encoding="utf-8")

    try:
        Base.metadata.create_all(bind=engine)

        jobs = run_scraper(
            queries=["python developer"],
            locations=["Stockholm"],
            limit=1,
            max_pages=1,
        )
        processed = run_processor()
        ranked = run_ranker(processed, cv_path=str(resume_path))
        generated = run_application_generation(ranked, resume_path=str(resume_path), top_n=1)

        assert jobs
        assert processed
        assert ranked
        assert generated

        job_directory = generated[0]["directory"]
        resume_file = generated[0]["resume_path"]
        cover_letter_file = generated[0]["cover_letter_path"]
        job_json_file = generated[0]["job_json_path"]

        assert job_directory.exists()
        assert resume_file.exists()
        assert cover_letter_file.exists()
        assert job_json_file.exists()

        job_payload = json.loads(job_json_file.read_text(encoding="utf-8"))
        assert job_payload["id"] == ranked[0].id
        assert "Python Developer" in resume_file.read_text(encoding="utf-8")
        assert "Dear Hiring Manager," in cover_letter_file.read_text(encoding="utf-8")
    finally:
        engine.dispose()
        if resume_path.exists():
            resume_path.unlink()
        if db_path.exists():
            db_path.unlink()
        if applications_dir.exists():
            for path in applications_dir.rglob("*"):
                if path.is_file():
                    path.unlink(missing_ok=True)
            for path in sorted(applications_dir.rglob("*"), reverse=True):
                if path.is_dir():
                    path.rmdir()
            applications_dir.rmdir()
