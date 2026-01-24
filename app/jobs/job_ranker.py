"""
Job ranker module.

This module is responsible for ranking already matched jobs
based on their similarity score and assigning confidence labels.

No job fetching, embeddings, or ML logic is implemented here.
"""

from __future__ import annotations

from typing import Dict, List

from app.utils.logger import get_logger

logger = get_logger(__name__)


class JobRanker:
    """
    Rank matched jobs based on similarity score.
    """

    def rank_jobs(self, matched_jobs: List[Dict[str, object]]) -> List[Dict[str, object]]:
        """
        Rank jobs and assign confidence labels.

        Args:
            matched_jobs: List of job dictionaries containing `match_score`.

        Returns:
            Ranked list of jobs with confidence labels added.
        """
        if not matched_jobs:
            return []

        logger.info("Ranking %d matched jobs", len(matched_jobs))

        ranked_jobs = sorted(
            matched_jobs,
            key=self._safe_score,
            reverse=True,
        )

        for job in ranked_jobs:
            score = self._safe_score(job)
            job["confidence"] = self._confidence_label(score)

        logger.info("Job ranking completed")
        return ranked_jobs

    @staticmethod
    def _safe_score(job: Dict[str, object]) -> float:
        """
        Safely extract match_score as float.
        """
        score = job.get("match_score")

        if isinstance(score, (int, float)):
            return float(score)

        return 0.0

    @staticmethod
    def _confidence_label(score: float) -> str:
        """
        Determine confidence label based on similarity score.
        """
        if score >= 0.7:
            return "High"
        if score >= 0.4:
            return "Medium"
        return "Low"
