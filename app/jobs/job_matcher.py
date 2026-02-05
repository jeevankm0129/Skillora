"""
Job matcher module.

This module matches user skills with job requirements using
a simple and explainable ML-based similarity approach.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.utils.logger import get_logger

logger = get_logger(__name__)


class JobMatcher:
    """
    Match user skills with job requirements.
    """

    def match_jobs(
        self,
        user_skills: List[str],
        jobs: List[Dict[str, object]],
        min_score: float = 0.2,
    ) -> List[Dict[str, object]]:
        """
        Match jobs based on skill similarity.

        Args:
            user_skills: List of user skills.
            jobs: List of job dictionaries.
            min_score: Minimum similarity score to consider a job relevant.

        Returns:
            List of matched jobs with match_score added.
        """
        if not user_skills or not jobs:
            return []

        logger.info("Matching jobs for user skills")

        # Prepare user skill text
        user_skill_text = " ".join(user_skills)

        # Prepare job skill text safely
        job_skill_texts: List[str] = []

        for job in jobs:
            skills = job.get("required_skills")

            if isinstance(skills, list):
                job_skill_texts.append(" ".join(str(skill) for skill in skills))
            else:
                job_skill_texts.append("")

        vectorizer = TfidfVectorizer()
        vectors: Any = vectorizer.fit_transform([user_skill_text] + job_skill_texts)

        similarity_matrix = cosine_similarity(vectors[0:1], vectors[1:])

        similarity_scores = similarity_matrix.flatten()

        matched_jobs: List[Dict[str, object]] = []

        for job, score in zip(jobs, similarity_scores):
            if score >= min_score:
                matched_job = job.copy()
                matched_job["match_score"] = round(float(score), 3)
                matched_jobs.append(matched_job)

        logger.info(
            "Matched %d jobs above threshold %.2f",
            len(matched_jobs),
            min_score,
        )

        return matched_jobs
