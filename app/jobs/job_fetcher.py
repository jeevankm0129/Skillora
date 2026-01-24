"""
Job fetching module.

Hybrid strategy:
1. Use cached jobs from DB if available
2. Fetch from real job API
3. Fallback to mock jobs if API fails
"""

from __future__ import annotations

import os
from typing import Dict, List

import requests

from app.database.crud import get_cached_jobs, save_jobs
from app.database.db import get_session
from app.utils.logger import get_logger

logger = get_logger(__name__)


class JobFetcher:
    """
    Fetch job listings using a hybrid strategy.
    """

    def fetch_jobs(self) -> List[Dict[str, object]]:
        """
        Fetch jobs using cache → API → mock fallback.
        """

        # 1️⃣ Try DB cache
        with get_session() as session:
            cached_jobs = get_cached_jobs(session)
            if cached_jobs:
                logger.info("Using cached jobs from database")
                return [
                    {
                        "title": job.title,
                        "location": job.location,
                        "required_skills": job.skills.split(","),
                    }
                    for job in cached_jobs
                ]

        # 2️⃣ Fetch from API
        try:
            jobs = self._fetch_from_api()

            with get_session() as session:
                save_jobs(session, jobs, source="jsearch")

            return jobs

        except Exception as exc:
            logger.error("Job API fetch failed: %s", exc)

        # 3️⃣ Fallback to mock data
        logger.warning("Falling back to mock job data")
        return self._mock_jobs()

    def _fetch_from_api(self) -> List[Dict[str, object]]:
        """
        Fetch jobs from JSearch API.
        """
        logger.info("JOB_API_KEY visible: %s", bool(os.getenv("JOB_API_KEY")))

        api_key = os.getenv("JOB_API_KEY")
        if not api_key:
            raise RuntimeError("JOB_API_KEY is not configured")

        url = "https://jsearch.p.rapidapi.com/search"
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        }
        params = {
            "query": "software engineer",
            "page": 1,
            "num_pages": 1,
            "country": "IN",
            "employment_types": "FULLTIME",
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json().get("data", [])
        if not data:
            raise RuntimeError("API returned no job data")

        jobs: List[Dict[str, object]] = []

        for item in data:
            skills = item.get("job_required_skills") or []

            if not isinstance(skills, list):
                skills = []

            jobs.append(
                {
                    "title": item.get("job_title", "Software Engineer"),
                    "location": item.get("job_city") or "Remote",
                    "required_skills": [skill.lower() for skill in skills],
                }
            )

        logger.info("Fetched %d jobs from API", len(jobs))
        return jobs

    def _mock_jobs(self) -> List[Dict[str, object]]:
        """
        Mock job data (fallback).
        """
        return [
            {
                "title": "Junior Backend Software Engineer",
                "location": "Bengaluru",
                "required_skills": [
                    "software development",
                    "backend development",
                    "api development",
                    "database design",
                    "sql querying",
                    "version control",
                    "debugging",
                    "unit testing",
                    "agile methodology",
                ],
            }
        ]
