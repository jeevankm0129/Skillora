import re
from pathlib import Path
from typing import List, Set

from rapidfuzz import fuzz

from config import SKILLS_FILE_PATH


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def load_skill_list() -> List[str]:
    path = Path(SKILLS_FILE_PATH)
    if not path.exists():
        return []
    skills = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            skills.append(s)
    return skills


def extract_skills_rule_based(
    resume_text: str,
    skills_list: List[str] | None = None,
    fuzzy_threshold: int = 90,
    max_skills: int = 30,
) -> List[str]:
    """
    Rule-based skill extraction:
    - Exact match (case-insensitive)
    - Fuzzy match (rapidfuzz partial_ratio)
    Returns unique skills (preserves casing from skills_list).
    """
    if not resume_text:
        return []

    if skills_list is None:
        skills_list = load_skill_list()

    if not skills_list:
        return []

    text_norm = _normalize(resume_text)
    found: Set[str] = set()

    # 1) Exact phrase match
    for skill in skills_list:
        sk = skill.strip()
        if not sk:
            continue
        sk_norm = _normalize(sk)

        # handle very short tokens carefully
        if len(sk_norm) <= 2:
            if sk_norm in text_norm.split():
                found.add(sk)
            continue

        pattern = r"\b" + re.escape(sk_norm) + r"\b"
        if re.search(pattern, text_norm):
            found.add(sk)

    # 2) Fuzzy match on lines (fast enough for resumes)
    lines = [_normalize(l) for l in resume_text.splitlines() if l.strip()]
    for skill in skills_list:
        if skill in found:
            continue
        sk_norm = _normalize(skill)
        if len(sk_norm) < 3:
            continue

        for ln in lines:
            if fuzz.partial_ratio(sk_norm, ln) >= fuzzy_threshold:
                found.add(skill)
                break

    out = sorted(found, key=lambda x: x.lower())
    return out[:max_skills]
