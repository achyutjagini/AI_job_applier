from __future__ import annotations

import tempfile
from pathlib import Path

from models.job import JobSchema
from generators import resume_generator


def test_load_resume() -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".txt",
        dir=Path.cwd(),
        delete=False,
    ) as resume_file:
        resume_file.write("Backend engineer with Python and AWS experience")
        resume_path = Path(resume_file.name)

    try:
        resume_text = resume_generator.load_resume(str(resume_path))
    finally:
        resume_path.unlink(missing_ok=True)

    assert resume_text == "Backend engineer with Python and AWS experience"


def test_generate_resume_includes_job_context() -> None:
    job = JobSchema(
        title="Backend Developer",
        company="Zenseact",
        location="Stockholm",
        description="Python, AWS and scalable backend systems",
        url="https://example.com/backend",
        skills=["python", "aws"],
    )

    tailored_resume = resume_generator.generate_resume(job, "Built APIs and cloud services.")

    assert "Backend Developer" in tailored_resume
    assert "Zenseact" in tailored_resume
    assert "python, aws" in tailored_resume


def test_generate_cover_letter_uses_job_details() -> None:
    job = JobSchema(
        title="ML Engineer",
        company="Spotify",
        location="Stockholm",
        description="Machine learning systems with PyTorch",
        url="https://example.com/ml",
        skills=["machine learning", "pytorch"],
    )

    cover_letter = resume_generator.generate_cover_letter(job, "Machine learning engineer with production experience.")

    assert "ML Engineer" in cover_letter
    assert "Spotify" in cover_letter
    assert "machine learning, pytorch" in cover_letter
    assert cover_letter.startswith("Dear Hiring Manager,")


def test_save_application_writes_documents(monkeypatch) -> None:
    output_dir = Path.cwd() / "test_applications_output"
    monkeypatch.setattr(resume_generator, "APPLICATIONS_DIR", str(output_dir))

    try:
        resume_path, cover_letter_path = resume_generator.save_application(
            "123",
            "resume text",
            "cover letter text",
        )

        assert resume_path.name == "resume.txt"
        assert cover_letter_path.name == "cover_letter.txt"
        assert resume_path.parent.name == "job_123"
        assert resume_path.read_text(encoding="utf-8") == "resume text"
        assert cover_letter_path.read_text(encoding="utf-8") == "cover letter text"
    finally:
        for path in output_dir.rglob("*"):
            if path.is_file():
                path.unlink(missing_ok=True)
        for path in sorted(output_dir.rglob("*"), reverse=True):
            if path.is_dir():
                path.rmdir()
        output_dir.rmdir()
