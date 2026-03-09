from __future__ import annotations

import logging
from typing import Iterable

from config.settings import CV_PATH
from models.job import JobSchema
from rankers.job_ranker import load_cv, rank_jobs

from pipeline.process_jobs import run_processor

logger = logging.getLogger(__name__)


def run_ranker(
    processed_jobs: Iterable[JobSchema] | None = None,
    cv_path: str = CV_PATH,
) -> list[JobSchema]:
    """Rank processed jobs against the user CV text."""

    jobs = list(processed_jobs) if processed_jobs is not None else run_processor()
    try:
        cv_text = load_cv(cv_path)
    except FileNotFoundError:
        logger.warning("CV file not found at %s. Ranking skipped.", cv_path)
        return jobs

    return rank_jobs(jobs, cv_text)
