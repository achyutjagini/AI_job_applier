import logging

from scraper.linkedin_scraper import LinkedInScraper
from scraper.greenhouse_scraper import GreenhouseScraper


logging.basicConfig(level=logging.INFO)


def main():
    print("Starting job scraping...\n")

    jobs = []

    try:
        print("Running LinkedIn scraper...")
        linkedin = LinkedInScraper()
        linkedin_jobs = linkedin.search_jobs("AI Engineer", "Stockholm")
        print(f"LinkedIn jobs found: {len(linkedin_jobs)}")

        jobs.extend(linkedin_jobs)

    except Exception as e:
        print("LinkedIn scraper error:", e)

    try:
        print("\nRunning Greenhouse scraper...")
        greenhouse = GreenhouseScraper()
        greenhouse_jobs = greenhouse.search_jobs()

        print(f"Greenhouse jobs found: {len(greenhouse_jobs)}")
        jobs.extend(greenhouse_jobs)

    except Exception as e:
        print("Greenhouse scraper error:", e)

    print("\nJobs collected:", len(jobs))

    for job in jobs[:10]:
        print(job)


if __name__ == "__main__":
    main()
