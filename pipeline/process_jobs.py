from __future__ import annotations

import logging
from typing import Iterable

from database.db import list_jobs
from models.job import JobSchema
from processors.job_processor import process_jobs

logger = logging.getLogger(__name__)


def run_processor(jobs: Iterable[JobSchema] | None = None) -> list[JobSchema]:
    """Load scraped jobs and normalize/enrich them."""

    source_jobs = list(jobs) if jobs is not None else list_jobs()
    processed_jobs = process_jobs(source_jobs)
    logger.info("Processor returned %d jobs", len(processed_jobs))
    return processed_jobs
