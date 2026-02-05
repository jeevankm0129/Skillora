"""
Central storage for bot user-facing messages.

This module contains only static messages or simple message helpers.
No application logic should be placed here.
"""

from __future__ import annotations


# =====================================================
# Welcome & Instructions
# =====================================================

WELCOME_MESSAGE: str = (
    "👋 Welcome to the AI Resume & Job Recommendation Bot!\n\n"
    "You can:\n"
    "• Upload your resume (PDF or DOCX)\n"
    "• Or build a resume by entering your details\n"
    "• Send text messages for guidance\n\n"
    "I’ll help you create a strong resume and find relevant jobs."
)

INSTRUCTIONS_MESSAGE: str = (
    "📄 How to use this bot:\n\n"
    "1️⃣ Upload your resume\n"
    "2️⃣ OR choose to build a resume step by step\n"
    "3️⃣ Wait while we analyze your profile\n"
    "4️⃣ Get job recommendations\n\n"
    "You’ll be notified once results are ready."
)


# =====================================================
# Error Messages
# =====================================================

GENERIC_ERROR_MESSAGE: str = (
    "⚠️ Something went wrong. Please try again later."
)

INVALID_FILE_MESSAGE: str = (
    "❌ Unsupported file format.\n"
    "Please upload a PDF or DOCX resume."
)

MISSING_INFORMATION_MESSAGE: str = (
    "⚠️ Some required details are missing.\n"
    "Please provide the requested information."
)


# =====================================================
# Resume Upload & Job Messages
# =====================================================

RESUME_RECEIVED_MESSAGE: str = (
    "✅ Resume received successfully.\n"
    "We’re analyzing it now."
)

JOB_RESULTS_HEADER: str = (
    "💼 Job Recommendations Based on Your Profile:"
)


# =====================================================
# Notifications
# =====================================================

PROCESSING_NOTIFICATION: str = (
    "⏳ Processing your request. This may take a moment."
)

COMPLETION_NOTIFICATION: str = (
    "🎉 Your results are ready! Check the recommendations above."
)


# =====================================================
# No-Resume / Resume Build Flow Messages
# =====================================================

NO_RESUME_OPTION_MESSAGE: str = (
    "📌 Don’t have a resume?\n\n"
    "No worries! I can help you build one.\n"
    "You’ll just need to answer a few questions."
)

RESUME_BUILD_START_MESSAGE: str = (
    "📝 Let’s build your resume!\n\n"
    "I’ll ask you a few questions. Please answer them one by one."
)

ASK_FULL_NAME_MESSAGE: str = "👤 What is your full name?"

ASK_EMAIL_MESSAGE: str = "📧 What is your email address?"

ASK_PHONE_MESSAGE: str = "📱 What is your phone number?"

ASK_EDUCATION_MESSAGE: str = (
    "🎓 Please enter your education details.\n"
    "(Example: B.Tech in Computer Science, CVR College of Engineering)"
)

ASK_SKILLS_MESSAGE: str = (
    "🛠️ List your skills.\n"
    "(Example: Python, Java, SQL, Machine Learning)"
)

ASK_EXPERIENCE_MESSAGE: str = (
    "💼 Describe your work experience.\n"
    "If you are a fresher, type 'Fresher'."
)

ASK_PROJECTS_MESSAGE: str = (
    "📂 Mention your projects (if any).\n"
    "You can separate multiple projects with commas."
)

RESUME_BUILD_COMPLETION_MESSAGE: str = (
    "✅ Thank you! I’ve collected all the required details.\n"
    "Your resume will be generated shortly."
)


# =====================================================
# Simple Message Helpers
# =====================================================

def job_count_message(count: int) -> str:
    """
    Generate a message indicating the number of jobs found.

    Args:
        count: Number of job matches.

    Returns:
        A formatted job count message.
    """
    return f"🔎 We found {count} matching job opportunities for you."
