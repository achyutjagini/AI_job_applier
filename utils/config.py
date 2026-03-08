"""Configuration module for job scraper."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT}/jobs.db")
DATABASE_PATH = PROJECT_ROOT / "jobs.db"

# Scraper configuration
HEADLESS_MODE = os.getenv("HEADLESS_MODE", "true").lower() == "true"
SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "30000"))
SCRAPER_WAIT_TIME = int(os.getenv("SCRAPER_WAIT_TIME", "5000"))

# LinkedIn configuration
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")
LINKEDIN_BASE_URL = "https://www.linkedin.com"
LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/search/"

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = PROJECT_ROOT / "scraper.log"
