"""LinkedIn job scraper using Playwright."""

import os
os.environ["PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS"] = "true"

import logging
from typing import List, Optional
from datetime import datetime
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright, Page, Browser
from bs4 import BeautifulSoup

from scraper.base_scraper import BaseScraper
from database.models import JobSchema
from utils.config import LINKEDIN_JOBS_URL, SCRAPER_TIMEOUT

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job postings."""

    def __init__(self):
        super().__init__("LinkedIn")
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None

    def _init_browser(self) -> None:
        """Initialize Playwright browser."""
        try:
            self._playwright = sync_playwright().start()

            self.browser = self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--disable-extensions",
                ],
            )

            self.page = self.browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
            )

            logger.info("Browser initialized for LinkedIn scraper")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise

    def close(self) -> None:
        """Close browser."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self._playwright:
                self._playwright.stop()

            logger.info("LinkedIn scraper closed")

        except Exception as e:
            logger.error(f"Error closing browser: {e}")

    def search_jobs(
        self,
        keywords: str = "AI Engineer",
        location: str = "",
        **kwargs,
    ) -> List[JobSchema]:

        if not self.browser:
            self._init_browser()

        jobs: List[JobSchema] = []

        try:

            params = {"keywords": keywords}
            if location:
                params["location"] = location

            search_url = f"{LINKEDIN_JOBS_URL}?{urlencode(params)}"
            logger.info(f"Searching LinkedIn: {search_url}")

            self.page.goto(search_url, timeout=SCRAPER_TIMEOUT)

            # wait for job cards
            self.page.wait_for_selector("li.jobs-search-results__list-item", timeout=10000)

            self._scroll_and_load(self.page)

            job_elements = self.page.query_selector_all("li.jobs-search-results__list-item")

            logger.info(f"Found {len(job_elements)} job listings")

            for element in job_elements:

                try:
                    html = element.inner_html()
                    job = self.parse_job_card(html)

                    if job:
                        jobs.append(job)
                        self.jobs_found += 1

                except Exception as e:
                    logger.debug(f"Error parsing job card: {e}")

        except Exception as e:
            logger.error(f"Error searching LinkedIn: {e}")

        return jobs

    def _scroll_and_load(self, page: Page, scrolls: int = 3) -> None:
        """Scroll page to load more results."""

        for _ in range(scrolls):
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            page.wait_for_timeout(1500)

    def parse_job_card(self, html: str) -> Optional[JobSchema]:
        """Parse job card HTML."""

        try:

            soup = BeautifulSoup(html, "html.parser")

            title_elem = soup.select_one("h3")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)

            company_elem = soup.select_one("h4")
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"

            location_elem = soup.select_one(".job-search-card__location")
            location = location_elem.get_text(strip=True) if location_elem else ""

            link_elem = soup.select_one("a")
            if not link_elem:
                return None

            job_url = link_elem.get("href", "")

            if job_url and not job_url.startswith("http"):
                job_url = f"https://www.linkedin.com{job_url}"

            job = JobSchema(
                title=title,
                company=company,
                location=location,
                url=job_url,
                description=None,
                source=self.source_name,
                scraped_at=datetime.utcnow(),
            )

            return job

        except Exception as e:
            logger.debug(f"Error parsing job card: {e}")
            return None