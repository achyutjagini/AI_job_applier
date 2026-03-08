"""Greenhouse job board scraper."""

import logging
import re
from typing import List, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from scraper.base_scraper import BaseScraper
from database.models import JobSchema

logger = logging.getLogger(__name__)


class GreenhouseScraper(BaseScraper):
    """Scraper for Greenhouse job boards."""

    def __init__(self):
        """Initialize Greenhouse scraper."""
        super().__init__("Greenhouse")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def close(self) -> None:
        """Close the session."""
        try:
            self.session.close()
            logger.info("Greenhouse scraper session closed")
        except Exception as e:
            logger.error(f"Error closing session: {e}")

    def search_jobs(
        self,
        keywords: str = "AI Engineer",
        location: str = "",
        job_board_url: str = "",
        **kwargs,
    ) -> List[JobSchema]:
        """Search for jobs on a Greenhouse job board.
        
        Args:
            keywords: Job search keywords (used for filtering)
            location: Job location (used for filtering)
            job_board_url: URL of the Greenhouse job board
            **kwargs: Additional parameters
            
        Returns:
            List[JobSchema]: List of found jobs
        """
        if not job_board_url:
            logger.warning("No job_board_url provided for Greenhouse scraper")
            return []

        jobs = []

        try:
            # Construct API URL
            api_url = f"{job_board_url.rstrip('/')}/api/v1/boards/{self._extract_board_name(job_board_url)}/departments"
            logger.info(f"Fetching from Greenhouse API: {api_url}")

            # Fetch departments
            response = self.session.get(api_url, timeout=10)
            response.raise_for_status()

            departments = response.json()

            # Scrape job listings
            for department in departments:
                dept_name = department.get("name", "")
                jobs_url = department.get("jobs_url", "")

                if jobs_url:
                    dept_jobs = self._scrape_jobs_page(jobs_url, keywords, location)
                    jobs.extend(dept_jobs)
                    self.jobs_found += len(dept_jobs)

        except Exception as e:
            logger.error(f"Error searching Greenhouse jobs: {e}")

        return jobs

    def _extract_board_name(self, url: str) -> str:
        """Extract board name from Greenhouse URL.
        
        Args:
            url: Greenhouse job board URL
            
        Returns:
            str: Board name
        """
        match = re.search(r"boards/([^/]+)", url)
        if match:
            return match.group(1)
        return "jobs"

    def _scrape_jobs_page(
        self,
        url: str,
        keywords: str,
        location: str,
    ) -> List[JobSchema]:
        """Scrape jobs from a Greenhouse job board page.
        
        Args:
            url: Page URL
            keywords: Keywords to filter
            location: Location to filter
            
        Returns:
            List[JobSchema]: List of found jobs
        """
        jobs = []

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            job_elements = soup.select("[data-job-id], .job-posting")

            for element in job_elements:
                try:
                    html = str(element)
                    job = self.parse_job_card(html)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.debug(f"Error parsing job: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping jobs page: {e}")

        return jobs

    def parse_job_card(self, html: str) -> Optional[JobSchema]:
        """Parse a Greenhouse job card.
        
        Args:
            html: HTML content of the job card
            
        Returns:
            JobSchema: Parsed job data or None
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Extract job title
            title_elem = soup.select_one("a.opening-link, h3.job-title, [data-job-title]")
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)

            # Extract company (if available in HTML)
            company = "Greenhouse Partner"

            # Extract location
            location_elem = soup.select_one("[data-job-location], .location")
            location = location_elem.get_text(strip=True) if location_elem else ""

            # Extract job URL
            link_elem = soup.select_one("a.opening-link, a[href*='boards']")
            if not link_elem:
                return None

            job_url = link_elem.get("href", "")
            if not job_url.startswith("http"):
                job_url = f"{job_url}"

            # Extract description
            desc_elem = soup.select_one(".description, [data-job-description]")
            description = desc_elem.get_text(strip=True)[:500] if desc_elem else None

            # Create JobSchema
            job = JobSchema(
                title=title,
                company=company,
                location=location,
                url=job_url,
                description=description,
                source=self.source_name,
                scraped_at=datetime.utcnow(),
            )

            logger.debug(f"Parsed job: {title}")
            return job

        except Exception as e:
            logger.debug(f"Error parsing Greenhouse job card: {e}")
            return None
