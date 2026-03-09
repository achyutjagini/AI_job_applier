from __future__ import annotations

import logging
import re
from typing import Any, Iterable, Mapping

from config.settings import SOURCE_NAME
from models.job import JobSchema

logger = logging.getLogger(__name__)

TECH_SKILLS: list[str] = [
    "python",
    "java",
    "sql",
    "docker",
    "kubernetes",
    "aws",
    "machine learning",
    "data engineering",
    "tensorflow",
    "pytorch",
]


def normalize_job(job: JobSchema | Mapping[str, Any]) -> dict[str, Any]:
    """Normalize job fields into a cleaned dictionary."""

    raw_job = job.model_dump() if isinstance(job, JobSchema) else dict(job)
    return {
        "title": _clean_text(raw_job.get("title")) or "",
        "company": _clean_text(raw_job.get("company")),
        "location": _clean_text(raw_job.get("location")),
        "description": _clean_text(raw_job.get("description")),
        "url": str(raw_job.get("url") or "").strip(),
        "published": raw_job.get("published"),
        "source": raw_job.get("source") or SOURCE_NAME,
        "skills": list(raw_job.get("skills") or []),
    }


def extract_skills(description: str) -> list[str]:
    """Detect configured tech skills from a job description."""

    normalized_description = description.casefold()
    matched_skills: list[tuple[int, str]] = []
    for skill in TECH_SKILLS:
        pattern = rf"(?<!\w){re.escape(skill.casefold())}(?!\w)"
        match = re.search(pattern, normalized_description)
        if match:
            matched_skills.append((match.start(), skill))
    matched_skills.sort(key=lambda item: item[0])
    return [skill for _, skill in matched_skills]


def filter_jobs(jobs: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop invalid jobs with empty descriptions or very short titles."""

    filtered_jobs: list[dict[str, Any]] = []
    for job in jobs:
        title = str(job.get("title") or "").strip()
        description = str(job.get("description") or "").strip()
        if len(title) < 3:
            continue
        if not description:
            continue
        filtered_jobs.append(job)
    return filtered_jobs


def process_jobs(jobs: Iterable[JobSchema | Mapping[str, Any]]) -> list[JobSchema]:
    """Normalize, enrich, and filter parsed jobs."""

    parsed_jobs = list(jobs)
    logger.info("Processing %d jobs", len(parsed_jobs))

    normalized_jobs = [normalize_job(job) for job in parsed_jobs]
    filtered_jobs = filter_jobs(normalized_jobs)
    filtered_count = len(normalized_jobs) - len(filtered_jobs)

    processed_jobs: list[JobSchema] = []
    for job in filtered_jobs:
        job["skills"] = extract_skills(job["description"])
        processed_jobs.append(JobSchema(**job))

    logger.info("Extracted skills for %d jobs", len(processed_jobs))
    logger.info("Filtered %d invalid jobs", filtered_count)
    return processed_jobs


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    collapsed = " ".join(str(value).split())
    return collapsed or None
