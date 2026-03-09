from __future__ import annotations

import logging
import math
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Mapping

from config.settings import EMBEDDING_MODEL_NAME
from models.job import JobSchema

logger = logging.getLogger(__name__)


def load_cv(path: str) -> str:
    """Read CV text from disk."""

    return Path(path).read_text(encoding="utf-8").strip()


def embed_text(text: str) -> list[float]:
    """Generate an embedding vector for the given text."""

    model = _get_embedding_model()
    embedding = model.encode(text or "", convert_to_numpy=True, normalize_embeddings=True)
    return embedding.tolist()


def score_job(job_description: str, cv_embedding: list[float]) -> float:
    """Compute cosine similarity between a job description and the CV embedding."""

    job_embedding = embed_text(job_description or "")
    similarity = _cosine_similarity(job_embedding, cv_embedding)
    normalized_score = (similarity + 1.0) / 2.0
    return max(0.0, min(1.0, normalized_score))


def rank_jobs(
    jobs: Iterable[JobSchema | Mapping[str, object]],
    cv_text: str,
) -> list[JobSchema]:
    """Attach similarity scores to jobs and sort them by descending relevance."""

    parsed_jobs = [_coerce_job(job) for job in jobs]
    logger.info("Ranking %d jobs", len(parsed_jobs))
    if not parsed_jobs:
        logger.info("Top job score: 0.00")
        return []

    cv_embedding = embed_text(cv_text)
    ranked_jobs = [
        job.model_copy(update={"score": score_job(job.description or "", cv_embedding)})
        for job in parsed_jobs
    ]
    ranked_jobs.sort(key=lambda job: job.score, reverse=True)

    logger.info("Top job score: %.2f", ranked_jobs[0].score)
    return ranked_jobs


@lru_cache(maxsize=1)
def _get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def _coerce_job(job: JobSchema | Mapping[str, object]) -> JobSchema:
    if isinstance(job, JobSchema):
        return job
    return JobSchema(**job)


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    try:
        from sklearn.metrics.pairwise import cosine_similarity
    except ImportError:
        dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return dot_product / (left_norm * right_norm)

    return float(cosine_similarity([left], [right])[0][0])
