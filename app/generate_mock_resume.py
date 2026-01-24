from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


def create_resume():
    # File definition
    pdf_filename = "Rahul_Sharma_Resume.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=LETTER,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    # Styles Setup
    styles = getSampleStyleSheet()

    # 1. Header Styles (Centered)
    style_name = ParagraphStyle(
        name="Name",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.black,
    )

    style_contact = ParagraphStyle(
        name="Contact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.black,
        spaceAfter=20,
    )

    # 2. Section Headings (Uppercase, Bold)
    style_section_heading = ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=6,
        textTransform="uppercase",
        textColor=colors.black,
    )

    # 3. Content Styles (Clean, Readable)
    style_body = ParagraphStyle(
        name="Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,  # Line spacing
        alignment=TA_LEFT,
        spaceAfter=6,
    )

    style_job_title = ParagraphStyle(
        name="JobTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        spaceAfter=2,
    )

    style_job_details = ParagraphStyle(
        name="JobDetails",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",  # Italic
        fontSize=10.5,
        leading=14,
        spaceAfter=6,
    )

    # 4. Bullet Points Style
    style_bullet = ParagraphStyle(
        name="Bullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        leftIndent=15,
        firstLineIndent=0,
        spaceAfter=2,
        bulletIndent=5,
    )

    # --- CONTENT CONSTRUCTION ---
    story = []

    # NAME & CONTACT
    story.append(Paragraph("RAHUL SHARMA", style_name))
    contact_info = "rahul.sharma@example.com | +91-9876543210 | Bengaluru, India"
    story.append(Paragraph(contact_info, style_contact))

    # Divider Line function
    def add_divider():
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=8))

    # PROFESSIONAL SUMMARY
    story.append(Paragraph("Professional Summary", style_section_heading))
    add_divider()
    summary_text = (
        "Motivated software engineer with strong problem solving and analytical thinking abilities. "
        "Experienced in software development, backend development, and web application development. "
        "Adept at working in agile environments with a focus on clean code, performance optimization, and collaboration."
    )
    story.append(Paragraph(summary_text, style_body))

    # CORE SKILLS
    # Note: Combined into a text block to save vertical space (Best Practice for 1-page resumes)
    story.append(Paragraph("Core Skills", style_section_heading))
    add_divider()
    skills_list = [
        "Software Development",
        "Object Oriented Programming",
        "Data Structures and Algorithms",
        "Backend Development",
        "API Development",
        "RESTful API Design",
        "Database Design",
        "SQL Querying",
        "Version Control (Git)",
        "Debugging",
        "Performance Optimization",
        "Unit & Integration Testing",
        "Agile Methodology",
        "Collaboration",
    ]
    story.append(Paragraph(", ".join(skills_list), style_body))

    # TECHNICAL EXPERIENCE
    story.append(Paragraph("Technical Experience", style_section_heading))
    add_divider()

    # Job 1
    story.append(Paragraph("Software Engineer Intern", style_job_title))
    story.append(
        Paragraph("ABC Tech Solutions — Bengaluru | Jan 2024 – Jun 2024", style_job_details)
    )

    experience_bullets = [
        "Developed backend services for web applications using RESTful API design principles.",
        "Worked on database design and SQL querying to improve data retrieval performance.",
        "Participated in code reviews and followed version control best practices using Git workflow.",
        "Implemented unit testing and integration testing to improve application reliability.",
        "Collaborated with cross-functional teams using agile methodology and scrum practices.",
    ]
    for bullet in experience_bullets:
        story.append(Paragraph(f"• {bullet}", style_bullet))

    story.append(Spacer(1, 6))  # Extra space between jobs/sections

    # PROJECTS
    story.append(Paragraph("Projects", style_section_heading))
    add_divider()

    # Project 1
    story.append(Paragraph("Job Recommendation System", style_job_title))
    project_bullets = [
        "Designed a backend system for job recommendation using skill-based matching.",
        "Applied problem solving and analytical thinking to map resume skills to job requirements.",
        "Improved performance through query optimization and efficient data modeling.",
    ]
    for bullet in project_bullets:
        story.append(Paragraph(f"• {bullet}", style_bullet))

    # EDUCATION
    story.append(Paragraph("Education", style_section_heading))
    add_divider()
    story.append(
        Paragraph("Bachelor of Technology — Computer Science Engineering", style_job_title)
    )
    story.append(Paragraph("XYZ College of Engineering | 2021 – 2025", style_job_details))

    # ADDITIONAL SKILLS
    story.append(Paragraph("Additional Skills", style_section_heading))
    add_divider()
    additional_skills = [
        "Technical Documentation",
        "Requirements Analysis",
        "Time Management",
        "Communication Skills",
    ]
    story.append(Paragraph(" | ".join(additional_skills), style_body))

    # Build PDF
    doc.build(story)
    print(f"Success! {pdf_filename} has been created.")


if __name__ == "__main__":
    create_resume()
