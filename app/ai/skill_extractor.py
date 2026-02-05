"""
Skill extraction module.

This module provides simple, explainable, keyword-based skill extraction
from resume text. No ML or AI models are used.

Skills are matched against a predefined skill_keywords.json file.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Set

from app.utils.logger import get_logger

logger = get_logger(__name__)


class SkillExtractorError(Exception):
    """Custom exception for skill extraction errors."""


class SkillExtractor:
    """
    Extract skills from resume text using keyword matching.
    """

    def __init__(self, keywords_path: str | None = None) -> None:
        """
        Initialize the SkillExtractor.

        Args:
            keywords_path: Optional custom path to skill_keywords.json.
                           If not provided, the default path is used.
        """
        base_dir = Path(__file__).resolve().parents[2]  # Skillora/
        default_path = base_dir / "data" / "skill_keywords.json"

        self.keywords_path = str(keywords_path or default_path)

        self._skills = self._load_keywords()

    def _load_keywords(self) -> Set[str]:
        """
        Load skill keywords from JSON file.

        Returns:
            A set of skill keywords.

        Raises:
            SkillExtractorError: If the file cannot be loaded or parsed.
        """
        logger.info("Loading skill keywords from %s", self.keywords_path)

        if not os.path.exists(self.keywords_path):
            raise SkillExtractorError(f"Skill keywords file not found: {self.keywords_path}")

        try:
            with open(self.keywords_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise SkillExtractorError("skill_keywords.json must contain a list of strings")

            return {skill.lower() for skill in data if isinstance(skill, str)}

        except Exception as exc:
            logger.error("Failed to load skill keywords: %s", exc)
            raise SkillExtractorError("Unable to load skill keywords") from exc

    def extract(self, text: str) -> List[str]:
        """
        Extract skills from resume text.

        Args:
            text: Cleaned resume text.

        Returns:
            A list of unique matched skills.
        """
        if not text:
            return []

        text_lower = text.lower()
        matched_skills: Set[str] = {skill for skill in self._skills if skill in text_lower}

        logger.info("Extracted %d skills", len(matched_skills))

        return sorted(matched_skills)
