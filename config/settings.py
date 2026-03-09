from __future__ import annotations

from typing import Final

API_BASE_URL: Final[str] = "https://jobsearch.api.jobtechdev.se/search"
DATABASE_URL: Final[str] = "sqlite:///arbetsformedlingen_jobs.db"
TECH_JOB_QUERIES: Final[list[str]] = [
    "software developer",
    "python developer",
    "backend developer",
    "machine learning",
    "data engineer",
]
SEARCH_LOCATIONS: Final[list[str]] = [
    "Stockholm",
    "Göteborg",
    "Malmö",
]
DEFAULT_QUERY: Final[str] = TECH_JOB_QUERIES[0]
DEFAULT_LIMIT: Final[int] = 20
MAX_PAGES: Final[int] = 3
REQUEST_TIMEOUT_SECONDS: Final[int] = 10
SOURCE_NAME: Final[str] = "arbetsformedlingen"
