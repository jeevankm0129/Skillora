
import asyncio
from utils.resume_parser import parse_resume
from services.ai_service import extract_skills_from_resume

async def main():
    """
    This script is for debugging the skill extraction process.
    It parses a sample resume and calls the AI service to extract skills.
    """
    resume_path = "sample_resume.txt"
    print(f"--- 1. Parsing resume: {resume_path} ---")
    
    # Since it's a .txt, we can just read it directly. 
    # The real parser handles PDF/DOCX.
    with open(resume_path, 'r') as f:
        resume_text = f.read()

    if not resume_text:
        print("Failed to read resume text.")
        return

    print("\n--- 2. Resume Text (first 300 chars) ---")
    print(resume_text[:300])
    
    print("\n--- 3. Calling AI for skill extraction ---")
    skills = await extract_skills_from_resume(resume_text)
    
    print("\n--- 4. Results ---")
    if skills:
        print("Successfully extracted skills:")
        print(skills)
    else:
        print("Failed to extract skills.")

if __name__ == "__main__":
    # This is a simple way to run the async main function from a script
    asyncio.run(main())
