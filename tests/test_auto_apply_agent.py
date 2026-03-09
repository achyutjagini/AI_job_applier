from __future__ import annotations

import json
from pathlib import Path

from agents.auto_apply_agent import AutoApplyAgent


def test_load_applications_reads_job_folders() -> None:
    applications_dir = Path.cwd() / "test_auto_apply_applications"
    job_dir = applications_dir / "job_123"
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        (job_dir / "resume.txt").write_text("resume", encoding="utf-8")
        (job_dir / "cover_letter.txt").write_text("cover", encoding="utf-8")
        (job_dir / "job.json").write_text(
            json.dumps(
                {
                    "title": "Python Developer",
                    "company": "Spotify",
                    "url": "https://example.com/job/1",
                    "description": "Python backend development",
                }
            ),
            encoding="utf-8",
        )

        agent = AutoApplyAgent(applications_dir=str(applications_dir))
        applications = agent.load_applications()

        assert len(applications) == 1
        assert applications[0]["job"]["title"] == "Python Developer"
    finally:
        for path in job_dir.glob("*"):
            path.unlink(missing_ok=True)
        job_dir.rmdir()
        applications_dir.rmdir()


def test_run_returns_summary(monkeypatch) -> None:
    agent = AutoApplyAgent(applications_dir="unused")
    monkeypatch.setattr(
        agent,
        "load_applications",
        lambda: [
            {
                "job": {"title": "Data Scientist", "company": "Example", "url": "https://example.com/1"},
                "resume_path": Path("resume.txt"),
                "cover_letter_path": Path("cover_letter.txt"),
            },
            {
                "job": {"title": "ML Engineer", "company": "Example", "url": "https://example.com/2"},
                "resume_path": Path("resume.txt"),
                "cover_letter_path": Path("cover_letter.txt"),
            },
        ],
    )

    results = iter(["success", "manual"])
    monkeypatch.setattr(agent, "apply_to_job", lambda job, resume_path, cover_letter_path: next(results))

    summary = agent.run()

    assert summary["processed"] == 2
    assert summary["successful_attempts"] == 1
    assert summary["manual_applications_required"] == 1
    assert summary["failed_attempts"] == 0
