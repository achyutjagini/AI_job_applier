from __future__ import annotations

from pathlib import Path
from typing import Mapping

from config.settings import APPLICATIONS_DIR
from models.job import JobSchema


def load_resume(path: str) -> str:
    """Read the base resume text from disk."""

    return Path(path).read_text(encoding="utf-8").strip()


def generate_resume(job: JobSchema | Mapping[str, object], resume_text: str) -> str:
    """Generate a tailored plain-text resume for a job."""

    parsed_job = _coerce_job(job)
    company = parsed_job.company or "the company"
    relevant_skills = ", ".join(parsed_job.skills[:5]) or "relevant engineering skills"
    description_summary = _truncate(parsed_job.description or "", 600)

    return (
        f"Tailored Resume for {parsed_job.title} at {company}\n\n"
        "Professional Summary\n"
        f"Targeting the {parsed_job.title} role at {company} with emphasis on {relevant_skills}.\n\n"
        "Relevant Focus Areas\n"
        f"- Role alignment: {parsed_job.title}\n"
        f"- Key skills to emphasize: {relevant_skills}\n"
        f"- Location: {parsed_job.location or 'Not specified'}\n\n"
        "Job Description Highlights\n"
        f"{description_summary}\n\n"
        "Base Resume\n"
        f"{resume_text.strip()}\n"
    )


def generate_cover_letter(job: JobSchema | Mapping[str, object], resume_text: str) -> str:
    """Generate a tailored plain-text cover letter for a job."""

    parsed_job = _coerce_job(job)
    company = parsed_job.company or "your company"
    relevant_skills = ", ".join(parsed_job.skills[:3]) or "software engineering"
    resume_snippet = _truncate(" ".join(resume_text.split()), 240)

    return (
        "Dear Hiring Manager,\n\n"
        f"I am applying for the {parsed_job.title} role at {company}. "
        f"My experience in {relevant_skills} aligns closely with your requirements.\n\n"
        f"My background includes {resume_snippet}\n\n"
        "I would welcome the opportunity to contribute to your team.\n\n"
        "Sincerely,\n"
        "AI Job Applier Candidate\n"
    )


def save_application(job_id: str | int, resume_text: str, cover_letter: str) -> tuple[Path, Path]:
    """Persist generated application documents for a ranked job."""

    output_dir = Path(APPLICATIONS_DIR) / f"job_{job_id}"
    output_dir.mkdir(parents=True, exist_ok=True)

    resume_path = output_dir / "resume.txt"
    cover_letter_path = output_dir / "cover_letter.txt"

    resume_path.write_text(resume_text, encoding="utf-8")
    cover_letter_path.write_text(cover_letter, encoding="utf-8")
    return resume_path, cover_letter_path


def _coerce_job(job: JobSchema | Mapping[str, object]) -> JobSchema:
    if isinstance(job, JobSchema):
        return job
    return JobSchema(**job)


def _truncate(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 3].rstrip()}..."
