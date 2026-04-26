import io
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Known platform keywords → used to detect profile links and display names
# ---------------------------------------------------------------------------
_PLATFORM_PATTERNS: List[Tuple[str, str]] = [
    (r"github\.com",    "GitHub"),
    (r"linkedin\.com",  "LinkedIn"),
    (r"leetcode\.com",  "LeetCode"),
    (r"codeforces\.com","Codeforces"),
    (r"codechef\.com",  "CodeChef"),
    (r"hackerrank\.com","HackerRank"),
    (r"kaggle\.com",    "Kaggle"),
    (r"twitter\.com",   "Twitter"),
    (r"x\.com",         "X (Twitter)"),
    (r"portfolio",      "Portfolio"),
    (r"medium\.com",    "Medium"),
    (r"stackoverflow\.com", "Stack Overflow"),
]

# Regex that loosely matches a URL token
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)

# Regex for an email address
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Regex for a phone number (loose: digits, spaces, hyphens, +, parens, min 7 digits)
_PHONE_RE = re.compile(r"[\+\(]?[\d\s\-\(\)]{7,20}")


def _classify_contact_token(token: str) -> str:
    """Return 'email', 'phone', 'url', or 'other' for a single contact token."""
    token = token.strip()
    if _EMAIL_RE.search(token):
        return "email"
    if _URL_RE.search(token):
        return "url"
    # Phone: token must contain at least 7 digits
    digits = re.sub(r"\D", "", token)
    if len(digits) >= 7:
        return "phone"
    return "other"


def _url_to_display_name(url: str) -> str:
    """
    Return a human-friendly platform name for a URL, e.g.
    'https://github.com/user123' → 'GitHub'.
    Falls back to the bare hostname.
    """
    url_lower = url.lower()
    for pattern, name in _PLATFORM_PATTERNS:
        if re.search(pattern, url_lower):
            return name
    # Fallback: extract hostname
    m = re.search(r"https?://([^/\s]+)", url_lower)
    if m:
        host = m.group(1)
        host = re.sub(r"^www\.", "", host)
        return host.split(".")[0].capitalize()
    return url


def _ensure_https(url: str) -> str:
    """Prepend https:// if the URL has no scheme."""
    if url.startswith("http://") or url.startswith("https://"):
        return url
    return "https://" + url


# ---------------------------------------------------------------------------
# Style Definitions
# ---------------------------------------------------------------------------

def _build_styles() -> Dict[str, ParagraphStyle]:
    """
    Builds and returns all named paragraph styles used in the resume.
    Centralising styles here makes future tweaks a one-line change.
    """
    return {
        # Candidate full name — large, bold, centred
        "name": ParagraphStyle(
            "Name",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            alignment=1,           # centre
            spaceAfter=2,
        ),
        # Contact line (email | phone | links) — small, centred
        "contact": ParagraphStyle(
            "Contact",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            alignment=1,
            spaceAfter=3,
        ),
        # Section heading (e.g. EDUCATION) — bold, left-aligned
        "section_heading": ParagraphStyle(
            "SectionHeading",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=10,
            spaceAfter=2,
        ),
        # Regular body text
        "body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=2,
        ),
        # Bullet item — indented, with a hanging indent so wrapped lines align
        "bullet": ParagraphStyle(
            "Bullet",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            leftIndent=14,
            firstLineIndent=-14,    # hanging indent
            spaceAfter=2,
        ),
        # Project title — bold body text
        "project_title": ParagraphStyle(
            "ProjectTitle",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=14,
            spaceAfter=1,
            spaceBefore=5,
        ),
    }


# ---------------------------------------------------------------------------
# FIX 1 — Contact block: two structured lines with clickable links
# ---------------------------------------------------------------------------

def _format_contact_block(
    contact_raw: str,
    styles: Dict[str, ParagraphStyle],
) -> List[Flowable]:
    """
    Parses the raw contact string and produces up to two centred Paragraphs:

      Line 1:  email  •  phone
      Line 2:  <link href="...">GitHub</link>  |  <link>LinkedIn</link>  |  …

    Rules:
    - Raw URLs are never shown; only the platform display name is rendered.
    - Each link on line 2 is a proper PDF hyperlink (blue, underlined).
    - If a category is absent, that line is omitted entirely.
    """
    # Tokenise: split on common separators |, newline, comma, semicolon
    raw_tokens = re.split(r"[|\n,;]+", contact_raw)

    line1_parts: List[str] = []   # email + phone (plain text)
    link_parts:  List[str] = []   # profile URLs (rendered as hyperlinks)

    for tok in raw_tokens:
        tok = tok.strip()
        if not tok:
            continue
        kind = _classify_contact_token(tok)
        if kind == "email":
            line1_parts.append(tok)
        elif kind == "phone":
            line1_parts.append(tok)
        elif kind == "url":
            url = _ensure_https(_URL_RE.search(tok).group(0))   # type: ignore[union-attr]
            display = _url_to_display_name(url)
            link_parts.append(f'<link href="{url}" color="blue"><u>{display}</u></link>')
        else:
            # Could be a plain label like "Portfolio: somesite.com" — check for embedded URL
            url_match = _URL_RE.search(tok)
            if url_match:
                url = _ensure_https(url_match.group(0))
                display = _url_to_display_name(url)
                link_parts.append(f'<link href="{url}" color="blue"><u>{display}</u></link>')
            else:
                # Plain text with no URL — treat as supplementary info on line 1
                line1_parts.append(tok)

    result: List[Flowable] = []

    if line1_parts:
        line1_text = "  •  ".join(line1_parts)
        result.append(Paragraph(line1_text, styles["contact"]))

    if link_parts:
        line2_text = "  |  ".join(link_parts)
        result.append(Paragraph(line2_text, styles["contact"]))

    return result


# ---------------------------------------------------------------------------
# FIX 2 — Projects section: title + grouped bullet points
# ---------------------------------------------------------------------------

def _is_bullet_line(line: str) -> bool:
    """True if the line starts with a bullet character or a dash."""
    return line.startswith("•") or line.startswith("-")


def _parse_projects(raw: str) -> List[Dict[str, Any]]:
    """
    Parses the raw project text into a structured list of projects.

    Each project is a dict:  {"title": str, "bullets": List[str]}

    Parsing logic:
    - A line that does NOT start with '•' or '-' and is followed by bullet
      lines is treated as a project title.
    - Bullet lines (starting with '•' or '-') open a new bullet.
    - Continuation lines (non-bullet, non-empty, coming after a bullet has
      started) are appended to the current bullet rather than starting a new one.
    - An explicit blank line separates projects when there is no title.
    """
    lines = [l.rstrip() for l in raw.split("\n")]
    projects: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {"title": "", "bullets": []}
    current_bullet: Optional[str] = None

    def _flush_bullet() -> None:
        nonlocal current_bullet
        if current_bullet is not None:
            current["bullets"].append(current_bullet.strip())
            current_bullet = None

    def _flush_project() -> None:
        _flush_bullet()
        if current["title"] or current["bullets"]:
            projects.append({"title": current["title"], "bullets": list(current["bullets"])})

    for line in lines:
        stripped = line.strip()

        # Blank line → hard project boundary
        if not stripped:
            _flush_project()
            current = {"title": "", "bullets": []}
            current_bullet = None
            continue

        if _is_bullet_line(stripped):
            # New bullet — flush previous one first
            _flush_bullet()
            current_bullet = stripped.lstrip("-").lstrip("•").strip()
            current_bullet = "• " + current_bullet
        else:
            # Non-bullet line
            if current_bullet is not None:
                # Continuation of the current bullet — merge into it
                current_bullet = current_bullet.rstrip() + " " + stripped
            elif not current["bullets"]:
                # No bullets started yet → this is a project title
                _flush_project()
                current = {"title": stripped, "bullets": []}
                current_bullet = None
            else:
                # Non-bullet line after bullets — treat as a new project title
                _flush_project()
                current = {"title": stripped, "bullets": []}
                current_bullet = None

    _flush_project()
    return projects


def _add_projects_section(
    story: List[Flowable],
    content: str,
    styles: Dict[str, ParagraphStyle],
) -> None:
    """
    Renders the PROJECTS section with:
      - A bold project title per project
      - Up to 4 structured bullet points per project
      - Multi-line descriptions merged into single bullets
    """
    if not content or content.strip().lower() in {"none", "na", "n/a", ""}:
        return

    story.append(Paragraph("PROJECTS", styles["section_heading"]))
    story.append(
        HRFlowable(width="100%", thickness=0.75, color=colors.black, spaceAfter=4)
    )

    projects = _parse_projects(content)

    for proj in projects:
        title = proj.get("title", "").strip()
        bullets = proj.get("bullets", [])

        if title:
            story.append(Paragraph(title, styles["project_title"]))

        for bullet in bullets[:4]:   # max 4 bullets per project
            bullet_text = bullet if bullet.startswith("•") else f"• {bullet}"
            story.append(Paragraph(bullet_text, styles["bullet"]))

        story.append(Spacer(1, 4))

    story.append(Spacer(1, 2))


# ---------------------------------------------------------------------------
# Helper: generic section builder (unchanged)
# ---------------------------------------------------------------------------

def _add_section(
    story: List[Flowable],
    heading: str,
    content: str,
    styles: Dict[str, ParagraphStyle],
) -> None:
    """
    Appends a section heading (with a full-width HR rule beneath it) plus
    the section body to *story*.  Blank / 'none' / 'na' content is skipped.
    """
    if not content or content.strip().lower() in {"none", "na", "n/a", ""}:
        return

    story.append(Paragraph(heading, styles["section_heading"]))
    story.append(
        HRFlowable(
            width="100%",
            thickness=0.75,
            color=colors.black,
            spaceAfter=4,
        )
    )

    for line in content.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("•"):
            story.append(Paragraph(stripped, styles["bullet"]))
        else:
            story.append(Paragraph(stripped, styles["body"]))

    story.append(Spacer(1, 6))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_ats_resume_pdf(user_data: Dict[str, Any]) -> Optional[io.BytesIO]:
    """
    Generates a professional, ATS-friendly single-page PDF resume from the
    conversational data collected by the Telegram bot.

    Args:
        user_data: Dictionary produced by the resume-builder conversation.
                   Expected keys (all optional except 'name'):
                     name, contact, summary, education, skills, projects,
                     internships, experience, exams, extracurricular, achievements

    Returns:
        An in-memory BytesIO buffer containing the PDF, or None on failure.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )

    styles = _build_styles()
    story: List[Flowable] = []

    # ------------------------------------------------------------------
    # Header block: Name + Contact (FIX 1)
    # ------------------------------------------------------------------
    name = (user_data.get("name") or "").strip().upper()
    story.append(Paragraph(name, styles["name"]))

    contact_raw = (user_data.get("contact") or "").strip()
    if contact_raw:
        story.extend(_format_contact_block(contact_raw, styles))

    story.append(Spacer(1, 4))

    # ------------------------------------------------------------------
    # Ordered sections
    # ------------------------------------------------------------------
    sections = [
        ("TECHNICAL SUMMARY",        "summary"),
        ("EDUCATION",                "education"),
        ("TECHNICAL SKILLS",         "skills"),
        # PROJECTS handled separately (FIX 2)
        ("INTERNSHIPS",              "internships"),
        ("EXPERIENCE",               "experience"),
        ("COMPETITIVE EXAMS",        "exams"),
        ("ACHIEVEMENTS & ACTIVITIES","achievements"),
        ("EXTRACURRICULAR ACTIVITIES","extracurricular"),
    ]

    for heading, key in sections:
        # Insert PROJECTS just before INTERNSHIPS, in the correct order
        if key == "internships":
            projects_raw = str(user_data.get("projects") or "")
            _add_projects_section(story, projects_raw, styles)

        _add_section(story, heading, str(user_data.get(key) or ""), styles)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    try:
        doc.build(story)
        buffer.seek(0)
        logger.info("ATS resume PDF generated successfully.")
        return buffer
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}", exc_info=True)
        return None
