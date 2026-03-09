from __future__ import annotations

import logging

from config.settings import DEFAULT_LIMIT, DEFAULT_QUERY
from database.db import get_session, init_db, save_jobs
from models.job import parse_jobs
from scrapers.arbetsformedlingen import ArbetsformedlingenScraper


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    init_db()

    scraper = ArbetsformedlingenScraper()
    try:
        raw_jobs = scraper.search_jobs(DEFAULT_QUERY, DEFAULT_LIMIT)
    finally:
        scraper.close()

    parsed_jobs = parse_jobs(raw_jobs)

    session = get_session()
    try:
        saved_count = save_jobs(parsed_jobs, session)
    finally:
        session.close()

    duplicates_skipped = len(parsed_jobs) - saved_count
    logger.info("Parsed %d jobs", len(parsed_jobs))
    logger.info("Saved %d new jobs (%d duplicates skipped)", saved_count, duplicates_skipped)

    for index, job in enumerate(parsed_jobs[:10], start=1):
        company = job.company or "Unknown company"
        print(f"{index}. {job.title} @ {company} ({job.url})")


if __name__ == "__main__":
    main()
