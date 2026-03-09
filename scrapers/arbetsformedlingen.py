from __future__ import annotations

import logging
from typing import Any

import requests

from config.settings import (
    API_BASE_URL,
    DEFAULT_LIMIT,
    DEFAULT_QUERY,
    MAX_PAGES,
    REQUEST_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)


class ArbetsformedlingenScraper:
    """Thin client for the Arbetsformedlingen JobTech search API."""

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.session = session or requests.Session()

    def search_jobs(
        self,
        query: str = DEFAULT_QUERY,
        limit: int = DEFAULT_LIMIT,
        max_pages: int = MAX_PAGES,
    ) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        for page in range(max_pages):
            offset = page * limit
            params = {"q": query, "limit": limit, "offset": offset}
            response = self.session.get(self.base_url, params=params, timeout=self.timeout)
            response.raise_for_status()

            payload = response.json()
            hits = payload.get("hits", [])
            if not isinstance(hits, list):
                raise ValueError("Expected Arbetsformedlingen API response to contain a list of hits.")

            logger.info("Page %d returned %d jobs", page + 1, len(hits))
            jobs.extend(hits)

            if len(hits) < limit:
                break

        return jobs

    def close(self) -> None:
        self.session.close()
