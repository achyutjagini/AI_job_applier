from __future__ import annotations

from typing import Final

API_BASE_URL: Final[str] = "https://jobsearch.api.jobtechdev.se/search"
DATABASE_URL: Final[str] = "sqlite:///arbetsformedlingen_jobs.db"
DEFAULT_QUERY: Final[str] = "software developer"
DEFAULT_LIMIT: Final[int] = 20
REQUEST_TIMEOUT_SECONDS: Final[int] = 10
SOURCE_NAME: Final[str] = "arbetsformedlingen"
