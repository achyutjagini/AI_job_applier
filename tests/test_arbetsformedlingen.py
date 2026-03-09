from __future__ import annotations

import unittest
from unittest.mock import Mock

from config.settings import API_BASE_URL, REQUEST_TIMEOUT_SECONDS
from models.job import parse_jobs
from scrapers.arbetsformedlingen import ArbetsformedlingenScraper


class ArbetsformedlingenScraperTests(unittest.TestCase):
    def test_search_jobs_returns_raw_hits(self) -> None:
        session = Mock()
        response = Mock()
        response.json.return_value = {
            "hits": [
                {
                    "headline": "Python Developer",
                    "webpage_url": "https://example.com/jobs/1",
                }
            ]
        }
        session.get.return_value = response

        scraper = ArbetsformedlingenScraper(session=session)
        jobs = scraper.search_jobs("python", 5)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["headline"], "Python Developer")
        session.get.assert_called_once_with(
            API_BASE_URL,
            params={"q": "python", "limit": 5},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status.assert_called_once()

    def test_parse_jobs_validates_and_normalizes_payload(self) -> None:
        raw_jobs = [
            {
                "headline": "Backend Engineer",
                "employer": {"name": "Acme"},
                "workplace_address": {"city": "Stockholm"},
                "description": {"text": "Build APIs"},
                "webpage_url": "https://example.com/jobs/2",
                "publication_date": "2026-03-08T10:00:00Z",
            },
            {
                "headline": "Missing URL",
            },
        ]

        parsed_jobs = parse_jobs(raw_jobs)

        self.assertEqual(len(parsed_jobs), 1)
        self.assertEqual(parsed_jobs[0].title, "Backend Engineer")
        self.assertEqual(parsed_jobs[0].company, "Acme")
        self.assertEqual(parsed_jobs[0].location, "Stockholm")
        self.assertEqual(str(parsed_jobs[0].url), "https://example.com/jobs/2")
        self.assertIsNotNone(parsed_jobs[0].published)


if __name__ == "__main__":
    unittest.main()
