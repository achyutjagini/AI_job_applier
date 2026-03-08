"""Lever job board scraper."""

import logging
import re
from typing import List, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from scraper.base_scraper import BaseScraper
from database.models import JobSchema

logger = logging.getLogger(__name__)


class LeverScraper(BaseScraper):
    """Scraper for Lever job boards."""

    def __init__(self):
        """Initialize Lever scraper."""
        super().__init__("Lever")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def close(self) -> None:
        """Close the session."""
        try:
            self.session.close()
            logger.info("Lever scraper session closed")
        except Exception as e:
            logger.error(f"Error closing session: {e}")

    def search_jobs(
        self,
        keywords: str = "AI Engineer",
        location: str = "",
        job_board_url: str = "",
        **kwargs,
    ) -> List[JobSchema]:
        """Search for jobs on a Lever job board.
        
        Args:
            keywords: Job search keywords (used for filtering)
            location: Job location (used for filtering)
            job_board_url: URL of the Lever job board
            **kwargs: Additional parameters
            
        Returns:
            List[JobSchema]: List of found jobs
        """
        if not job_board_url:
            logger.warning("No job_board_url provided for Lever scraper")
            return []

        jobs = []

        try:
            # Construct API URL for Lever
            api_url = f"{job_board_url.rstrip('/')}/api/v0/postings?mode=json"
            logger.info(f"Fetching from Lever API: {api_url}")

            # Fetch jobs via API
            response = self.session.get(api_url, timeout=10)
            response.raise_for_status()

            job_postings = response.json()

            for posting in job_postings:
                try:
                    job = self._parse_lever_posting(posting)
                    if job:
                        jobs.append(job)
                        self.jobs_found += 1
                except Exception as e:
                    logger.debug(f"Error parsing Lever posting: {e}")
                    continue

        except Exception as e:
            # Fallback to HTML scraping if API fails
            logger.warning(f"Lever API failed, falling back to HTML scraping: {e}")
            jobs = self._scrape_jobs_page(job_board_url)

        return jobs

    def _scrape_jobs_page(self, url: str) -> List[JobSchema]:
        """Scrape jobs from a Lever job board page.
        
        Args:
            url: Page URL
            
        Returns:
            List[JobSchema]: List of found jobs
        """
        jobs = []

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            job_elements = soup.select("[data-job-id], .posting, .opportunities li")

            for element in job_elements:
                try:
                    html = str(element)
                    job = self.parse_job_card(html)
                    if job:
                        jobs.append(job)
                        self.jobs_found += 1
                except Exception as e:
                    logger.debug(f"Error parsing job: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping Lever jobs page: {e}")

        return jobs

    def _parse_lever_posting(self, posting: dict) -> Optional[JobSchema]:
        """Parse a Lever posting from JSON API.
        
        Args:
            posting: Job posting dictionary from Lever API
            
        Returns:
            JobSchema: Parsed job data or None
        """
        try:
            title = posting.get("text", "")
            if not title:
                return None

            # Extract company from URL or posting
            posting_url = posting.get("hostedUrl") or posting.get("url", "")
            company = "Lever Partner"

            # Extract location
            location_parts = []
            if posting.get("categories"):
                location = posting["categories"].get("location", "")
                if location:
                    location_parts.append(location)

            location = ", ".join(location_parts) or ""

            # Extract description
            description = posting.get("description", "")
            if description:
                description = BeautifulSoup(description, "html.parser").get_text(strip=True)[:500]

            # Create JobSchema
            job = JobSchema(
                title=title,
                company=company,
                location=location,
                url=posting_url,
                description=description or None,
                source=self.source_name,
                scraped_at=datetime.utcnow(),
            )

            logger.debug(f"Parsed job: {title}")
            return job

        except Exception as e:
            logger.debug(f"Error parsing Lever posting: {e}")
            return None

    def parse_job_card(self, html: str) -> Optional[JobSchema]:
        """Parse a Lever job card from HTML.
        
        Args:
            html: HTML content of the job card
            
        Returns:
            JobSchema: Parsed job data or None
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Extract job title
            title_elem = soup.select_one("a.posting-title, h3, .job-title")
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)

            # Extract company
            company = "Lever Partner"

            # Extract location
            location_elem = soup.select_one(".location, [data-location]")
            location = location_elem.get_text(strip=True) if location_elem else ""

            # Extract job URL
            link_elem = soup.select_one("a.posting-title, a[href*='lever.co']")
            if not link_elem:
                return None

            job_url = link_elem.get("href", "")

            # Extract description
            desc_elem = soup.select_one(".description, [data-description]")
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
            logger.debug(f"Error parsing Lever job card: {e}")
            return None
