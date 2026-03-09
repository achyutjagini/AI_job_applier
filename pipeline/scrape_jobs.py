from __future__ import annotations

import logging

from config.settings import DEFAULT_LIMIT, MAX_PAGES, SEARCH_LOCATIONS, TECH_JOB_QUERIES
from database.db import get_session, init_db, save_jobs
from models.job import JobSchema, parse_jobs
from scrapers.arbetsformedlingen import ArbetsformedlingenScraper

logger = logging.getLogger(__name__)


def run_scraper(
    queries: list[str] | None = None,
    locations: list[str] | None = None,
    limit: int = DEFAULT_LIMIT,
    max_pages: int = MAX_PAGES,
) -> list[JobSchema]:
    """Fetch Arbetsformedlingen jobs and persist them to the database."""

    init_db()
    query_list = queries or TECH_JOB_QUERIES
    location_list = locations or SEARCH_LOCATIONS

    all_raw_jobs: list[dict[str, object]] = []
    scraper = ArbetsformedlingenScraper()
    try:
        for query in query_list:
            for location in location_list:
                search_text = f"{query} {location}"
                logger.info("Searching query: %s in %s", query, location)
                raw_jobs = scraper.search_jobs(search_text, limit, max_pages)
                logger.info("Received %d jobs", len(raw_jobs))
                all_raw_jobs.extend(raw_jobs)
    finally:
        scraper.close()

    logger.info("Total jobs collected: %d", len(all_raw_jobs))
    parsed_jobs = parse_jobs(all_raw_jobs)

    session = get_session()
    try:
        saved_count = save_jobs(parsed_jobs, session)
    finally:
        session.close()

    duplicates_skipped = len(parsed_jobs) - saved_count
    logger.info("Parsed %d jobs", len(parsed_jobs))
    logger.info("Saved %d new jobs (%d duplicates skipped)", saved_count, duplicates_skipped)
    return parsed_jobs
