import asyncio
import json
import os
from pathlib import Path

from services.ai_service import extract_skills_from_resume
from utils.resume_parser import parse_resume


def get_resume_path() -> str:
    print("\n=== SKILLORA Resume Skill Debugger ===")
    print("Tip: Drag & drop the resume file into this terminal, then press Enter.\n")

    while True:
        raw = input("Resume path: ")
        path = raw.strip().strip('"').strip("'")

        print(f"\n[DEBUG] You entered: {repr(path)}")
        print(f"[DEBUG] Absolute path: {os.path.abspath(path)}")
        print(f"[DEBUG] Exists? {os.path.exists(path)}\n")

        if not path:
            print("❌ Path cannot be empty.\n")
            continue

        if not os.path.exists(path):
            print("❌ File not found. Try again.\n")
            continue

        ext = Path(path).suffix.lower()
        if ext not in [".pdf", ".docx"]:
            print("❌ Only PDF and DOCX files supported.\n")
            continue

        return path


async def main():
    print("[DEBUG] Starting test.py...\n")

    resume_path = get_resume_path()

    print("📄 Parsing resume...")
    resume_text = parse_resume(resume_path)

    if not resume_text or len(resume_text.strip()) < 50:
        print("❌ Resume parsing failed or text too small.")
        print("If PDF is scanned/image-based, use text-based PDF or DOCX.")
        return

    print(f"✅ Parsed text length: {len(resume_text)} characters")

    preview = resume_text[:600].replace("\n", " ")
    print(f"\n📝 Preview:\n{preview}...\n")

    print("🧠 Extracting skills using HuggingFace model...")
    print("[DEBUG] Calling extract_skills_from_resume() with timeout=60s...")

    try:
        extracted = await asyncio.wait_for(extract_skills_from_resume(resume_text), timeout=60)
    except asyncio.TimeoutError:
        print("❌ AI extraction timed out (60s). HF might be slow / rate-limited.")
        return
    except Exception as e:
        print(f"❌ AI extraction failed: {e}")
        return

    print("[DEBUG] AI returned successfully.")

    with open("skill_extraction_debug.json", "w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)

    print("✅ Raw AI output saved to skill_extraction_debug.json")

    skills = []
    if isinstance(extracted, dict):
        raw_skills = extracted.get("skills", [])
        if isinstance(raw_skills, list):
            skills = [s.strip() for s in raw_skills if isinstance(s, str) and s.strip()]

    print("\n🎯 Extracted Skills:")
    print(skills)

    if not skills:
        print("\n⚠️ Skills list is empty.")
        print("Check skill_extraction_debug.json to inspect model response.\n")


if __name__ == "__main__":
    asyncio.run(main())
