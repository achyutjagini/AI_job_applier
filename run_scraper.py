from __future__ import annotations

import logging

from pipeline.generate_applications import run_application_generation
from pipeline.process_jobs import run_processor
from pipeline.rank_jobs import run_ranker
from pipeline.scrape_jobs import run_scraper as run_scrape_stage


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    scraped_jobs = run_scrape_stage()
    logger.info("Scrape stage returned %d jobs", len(scraped_jobs))
    processed_jobs = run_processor()
    ranked_jobs = run_ranker(processed_jobs)
    generated_applications = run_application_generation(ranked_jobs)
    logger.info("Generated %d application bundles", len(generated_applications))

    for index, job in enumerate(ranked_jobs[:10], start=1):
        company = job.company or "Unknown company"
        print(f"{index}. {job.title} @ {company} [{job.score:.2f}] ({job.url})")


if __name__ == "__main__":
    main()
