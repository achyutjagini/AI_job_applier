"""Base scraper abstract class."""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

from database.models import JobSchema

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for job scrapers."""

    def __init__(self, source_name: str):
        """Initialize the scraper.
        
        Args:
            source_name: Name of the job source (e.g., 'LinkedIn', 'Greenhouse')
        """
        self.source_name = source_name
        self.jobs_found = 0
        self.jobs_saved = 0

    @abstractmethod
    def search_jobs(
        self,
        keywords: str,
        location: str = "",
        **kwargs,
    ) -> List[JobSchema]:
        """Search for jobs on the platform.
        
        Args:
            keywords: Job search keywords
            location: Job location (optional)
            **kwargs: Additional search parameters specific to the scraper
            
        Returns:
            List[JobSchema]: List of found jobs
        """
        pass

    @abstractmethod
    def parse_job_card(self, html: str) -> Optional[JobSchema]:
        """Parse a single job card from HTML.
        
        Args:
            html: HTML content of the job card
            
        Returns:
            JobSchema: Parsed job data or None if parsing fails
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the scraper (e.g., browser for Playwright-based scrapers)."""
        pass

    def save_job(self, job: JobSchema, db=None) -> bool:
        """Save a job to the database.
        
        Args:
            job: JobSchema instance
            db: Database session (optional)
            
        Returns:
            bool: True if job was saved, False if it already exists
        """
        from database.db import insert_job

        result = insert_job(job, db)
        if result:
            self.jobs_saved += 1
            return True
        return False

    def log_stats(self) -> None:
        """Log scraper statistics."""
        logger.info(
            f"{self.source_name} scraper - Found: {self.jobs_found}, "
            f"Saved: {self.jobs_saved}"
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
