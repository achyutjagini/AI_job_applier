from __future__ import annotations

from processors.job_processor import extract_skills, filter_jobs, normalize_job, process_jobs


def test_extract_skills() -> None:
    skills = extract_skills("Python developer with AWS and Docker experience")

    assert skills == ["python", "aws", "docker"]


def test_normalize_job() -> None:
    normalized_job = normalize_job(
        {
            "title": " Python Developer ",
            "company": " Test Company ",
            "location": " Stockholm ",
            "description": "Example description",
            "url": "https://example.com",
        }
    )

    assert normalized_job["title"] == "Python Developer"
    assert normalized_job["company"] == "Test Company"
    assert normalized_job["location"] == "Stockholm"


def test_filter_jobs() -> None:
    filtered_jobs = filter_jobs(
        [
            {"title": "Python Developer", "description": "Valid job"},
            {"title": "", "description": ""},
        ]
    )

    assert len(filtered_jobs) == 1
    assert filtered_jobs[0]["title"] == "Python Developer"


def test_process_jobs() -> None:
    processed_jobs = process_jobs(
        [
            {
                "title": "Python Developer",
                "company": "Example",
                "location": "Stockholm",
                "description": "Python developer with AWS",
                "url": "https://example.com/job",
            }
        ]
    )

    assert len(processed_jobs) == 1
    assert processed_jobs[0].title == "Python Developer"
    assert processed_jobs[0].company == "Example"
    assert "python" in processed_jobs[0].skills
    assert processed_jobs[0].skills == ["python", "aws"]
