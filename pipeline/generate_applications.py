from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Iterable

from config.settings import APPLICATIONS_DIR, RESUME_PATH, TOP_JOBS_TO_GENERATE
from generators.resume_generator import (
    generate_cover_letter,
    generate_resume,
    load_resume,
    save_application,
)
from models.job import JobSchema

from pipeline.rank_jobs import run_ranker

logger = logging.getLogger(__name__)


def run_application_generation(
    ranked_jobs: Iterable[JobSchema] | None = None,
    resume_path: str = RESUME_PATH,
    top_n: int = TOP_JOBS_TO_GENERATE,
) -> list[dict[str, object]]:
    """Generate tailored resume and cover letter files for top ranked jobs."""

    jobs = list(ranked_jobs) if ranked_jobs is not None else run_ranker(cv_path=resume_path)
    if not jobs:
        return []

    try:
        resume_text = load_resume(resume_path)
    except FileNotFoundError:
        logger.warning("Resume file not found at %s. Application generation skipped.", resume_path)
        return []

    top_jobs = jobs[:top_n]
    logger.info("Generating applications for top %d jobs", len(top_jobs))

    generated_applications: list[dict[str, object]] = []
    for index, job in enumerate(top_jobs, start=1):
        job_id = _job_identifier(job, fallback_index=index)
        tailored_resume = generate_resume(job, resume_text)
        cover_letter = generate_cover_letter(job, resume_text)
        resume_file, cover_letter_file = save_application(job_id, tailored_resume, cover_letter)

        job_directory = Path(APPLICATIONS_DIR) / f"job_{job_id}"
        job_json_path = job_directory / "job.json"
        job_json_path.write_text(
            json.dumps(job.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        company = job.company or "Unknown company"
        logger.info("Generated application for %s %s", company, job.title)
        generated_applications.append(
            {
                "job": job,
                "job_id": job_id,
                "directory": job_directory,
                "resume_path": resume_file,
                "cover_letter_path": cover_letter_file,
                "job_json_path": job_json_path,
            }
        )

    return generated_applications


def _job_identifier(job: JobSchema, fallback_index: int) -> str:
    if job.id is not None:
        return str(job.id)
    return hashlib.sha1(f"{job.url}-{fallback_index}".encode("utf-8")).hexdigest()[:12]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    results = run_application_generation()

    print(f"\nGenerated {len(results)} applications\n")

    for app in results:
        job = app["job"]
        print(f"{job.title} @ {job.company}")
        print(" ->", app["directory"])