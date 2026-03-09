from __future__ import annotations

import logging

from config.settings import CV_PATH, DEFAULT_LIMIT, MAX_PAGES, SEARCH_LOCATIONS, TECH_JOB_QUERIES
from database.db import get_session, init_db, save_jobs
from models.job import parse_jobs
from processors.job_processor import process_jobs
from rankers.job_ranker import load_cv, rank_jobs
from scrapers.arbetsformedlingen import ArbetsformedlingenScraper


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    init_db()

    all_raw_jobs: list[dict[str, object]] = []
    scraper = ArbetsformedlingenScraper()
    try:
        for query in TECH_JOB_QUERIES:
            for location in SEARCH_LOCATIONS:
                search_text = f"{query} {location}"
                logger.info("Searching query: %s in %s", query, location)
                raw_jobs = scraper.search_jobs(search_text, DEFAULT_LIMIT, MAX_PAGES)
                logger.info("Received %d jobs", len(raw_jobs))
                all_raw_jobs.extend(raw_jobs)
    finally:
        scraper.close()

    logger.info("Total jobs collected: %d", len(all_raw_jobs))
    parsed_jobs = parse_jobs(all_raw_jobs)
    processed_jobs = process_jobs(parsed_jobs)
    try:
        cv_text = load_cv(CV_PATH)
    except FileNotFoundError:
        logger.warning("CV file not found at %s. Ranking skipped.", CV_PATH)
        ranked_jobs = processed_jobs
    else:
        ranked_jobs = rank_jobs(processed_jobs, cv_text)

    session = get_session()
    try:
        saved_count = save_jobs(ranked_jobs, session)
    finally:
        session.close()

    duplicates_skipped = len(ranked_jobs) - saved_count
    logger.info("Parsed %d jobs", len(parsed_jobs))
    logger.info("Saved %d new jobs (%d duplicates skipped)", saved_count, duplicates_skipped)

    for index, job in enumerate(ranked_jobs[:10], start=1):
        company = job.company or "Unknown company"
        print(f"{index}. {job.title} @ {company} [{job.score:.2f}] ({job.url})")


if __name__ == "__main__":
    main()
