from __future__ import annotations

import tempfile
from pathlib import Path

from models.job import JobSchema
from rankers import job_ranker


def test_load_cv() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        dir=Path.cwd(),
        delete=False,
    ) as cv_file:
        cv_file.write("Python backend engineer")
        cv_path = Path(cv_file.name)

    try:
        cv_text = job_ranker.load_cv(str(cv_path))
    finally:
        cv_path.unlink(missing_ok=True)

    assert cv_text == "Python backend engineer"


def test_score_job_returns_normalized_similarity(monkeypatch) -> None:
    monkeypatch.setattr(job_ranker, "embed_text", lambda text: [1.0, 0.0] if "python" in text.lower() else [0.0, 1.0])

    score = job_ranker.score_job("Python developer role", [1.0, 0.0])

    assert 0.0 <= score <= 1.0
    assert score == 1.0


def test_rank_jobs_attaches_scores_and_sorts(monkeypatch) -> None:
    embeddings = {
        "cv": [1.0, 0.0],
        "python role": [1.0, 0.0],
        "java role": [0.0, 1.0],
    }
    monkeypatch.setattr(job_ranker, "embed_text", lambda text: embeddings[text])

    jobs = [
        JobSchema(
            title="Java Developer",
            company="Example",
            location="Stockholm",
            description="java role",
            url="https://example.com/java",
        ),
        JobSchema(
            title="Python Developer",
            company="Example",
            location="Stockholm",
            description="python role",
            url="https://example.com/python",
        ),
    ]

    ranked_jobs = job_ranker.rank_jobs(jobs, "cv")

    assert ranked_jobs[0].title == "Python Developer"
    assert ranked_jobs[0].score >= ranked_jobs[1].score
