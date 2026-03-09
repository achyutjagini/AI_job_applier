from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from config.settings import APPLICATIONS_DIR

logger = logging.getLogger(__name__)

APPLY_SELECTORS = [
    "text=Ansök",
    "text=Apply",
    "a:has-text('Ansök')",
    "a:has-text('Apply')",
]


class AutoApplyAgent:
    def __init__(
        self,
        applications_dir: str = APPLICATIONS_DIR,
        test_mode: bool = True,
        headless: bool = False,
        timeout_ms: int = 15000,
    ) -> None:
        self.applications_dir = Path(applications_dir)
        self.test_mode = test_mode
        self.headless = headless
        self.timeout_ms = timeout_ms

    def load_applications(self) -> list[dict[str, Any]]:
        """Load generated application bundles from disk."""

        if not self.applications_dir.exists():
            logger.info("Applications directory does not exist: %s", self.applications_dir)
            return []

        loaded_applications: list[dict[str, Any]] = []
        for application_dir in sorted(self.applications_dir.glob("job_*")):
            if not application_dir.is_dir():
                continue

            job_json_path = application_dir / "job.json"
            resume_path = application_dir / "resume.txt"
            cover_letter_path = application_dir / "cover_letter.txt"
            if not (job_json_path.exists() and resume_path.exists() and cover_letter_path.exists()):
                logger.warning("Skipping incomplete application folder: %s", application_dir)
                continue

            job_data = json.loads(job_json_path.read_text(encoding="utf-8"))
            loaded_applications.append(
                {
                    "directory": application_dir,
                    "job": job_data,
                    "resume_path": resume_path,
                    "cover_letter_path": cover_letter_path,
                }
            )

        logger.info("Loaded %d applications", len(loaded_applications))
        return loaded_applications

    def apply_to_job(
        self,
        job_data: dict[str, Any],
        resume_path: Path,
        cover_letter_path: Path,
    ) -> str:
        """Open the job page and attempt minimal application interaction."""

        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - dependency issue
            logger.error("Playwright is not installed: %s", exc)
            return "failed"

        job_url = job_data.get("url")
        if not isinstance(job_url, str) or not job_url:
            logger.error("Invalid job URL for %s", job_data.get("title", "unknown job"))
            return "failed"

        title = job_data.get("title") or "Unknown role"
        company = job_data.get("company") or "Unknown company"
        logger.info("Opening job page: %s @ %s", title, company)

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=self.headless)
                page = browser.new_page()
                page.goto(job_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                page_title = page.title()
                logger.info("Opened job page: %s", page_title)

                if self.test_mode:
                    browser.close()
                    return "success"

                for selector in APPLY_SELECTORS:
                    locator = page.locator(selector)
                    if locator.count() == 0:
                        continue
                    first_match = locator.first
                    if not first_match.is_visible():
                        continue

                    logger.info("Found apply button using selector: %s", selector)
                    first_match.click(timeout=self.timeout_ms)
                    browser.close()
                    logger.info("Application attempt completed")
                    return "success"

                browser.close()
                logger.info("Manual application required for %s", job_url)
                return "manual"
        except PlaywrightTimeoutError as exc:
            logger.error("Playwright timeout for %s: %s", job_url, exc)
            return "failed"
        except Exception as exc:  # pragma: no cover - defensive runtime protection
            logger.error("Application attempt failed for %s: %s", job_url, exc)
            return "failed"

    def run(self) -> dict[str, int]:
        """Attempt applications for all loaded application bundles."""

        applications = self.load_applications()
        summary = {
            "processed": 0,
            "successful_attempts": 0,
            "manual_applications_required": 0,
            "failed_attempts": 0,
        }

        for application in applications:
            summary["processed"] += 1
            result = self.apply_to_job(
                application["job"],
                application["resume_path"],
                application["cover_letter_path"],
            )

            if result == "success":
                summary["successful_attempts"] += 1
            elif result == "manual":
                summary["manual_applications_required"] += 1
            else:
                summary["failed_attempts"] += 1

        logger.info("Applications processed: %d", summary["processed"])
        logger.info("Successful attempts: %d", summary["successful_attempts"])
        logger.info("Manual applications required: %d", summary["manual_applications_required"])
        logger.info("Failed attempts: %d", summary["failed_attempts"])

        print(f"Applications processed: {summary['processed']}")
        print(f"Successful attempts: {summary['successful_attempts']}")
        print(f"Manual applications required: {summary['manual_applications_required']}")

        return summary
