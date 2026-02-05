from sqlalchemy.orm import Session
# Try/Except block handles if you run this file directly vs as a module
try:
    from . import models
except ImportError:
    import models

def get_user_by_telegram_id(db: Session, telegram_id: int):
    # Ensure telegram_id is treated as a Big Integer safely
    return db.query(models.User).filter(models.User.telegram_id == telegram_id).first()

def create_user(db: Session, telegram_id: int):
    user = models.User(telegram_id=telegram_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user_email(db: Session, telegram_id: int, email: str):
    user = get_user_by_telegram_id(db, telegram_id)
    if user:
        user.email = email
        user.notify_by_email = True
        db.commit()
        db.refresh(user)
    return user

def save_resume(db: Session, user_id: int, text_content: str, parsed_json: str = None):
    # Check if resume exists
    resume = db.query(models.Resume).filter(models.Resume.user_id == user_id).first()
    if resume:
        resume.text_content = text_content
        # Only update parsed_json if the column exists (Safety check)
        if hasattr(resume, 'parsed_json'):
            resume.parsed_json = parsed_json
    else:
        # Create new
        resume = models.Resume(user_id=user_id, text_content=text_content)
        if parsed_json and hasattr(resume, 'parsed_json'):
            resume.parsed_json = parsed_json

        db.add(resume)

    db.commit()
    return resume

def get_or_create_skill(db: Session, skill_name: str):
    # Normalize skill name
    if not skill_name:
        return None

    skill_name = skill_name.strip().title()
    skill = db.query(models.Skill).filter(models.Skill.name == skill_name).first()
    if not skill:
        skill = models.Skill(name=skill_name)
        db.add(skill)
        db.flush() # Flush adds ID but doesn't close transaction
    return skill

def link_skills_to_user(db: Session, user_id: int, skill_names: list[str]):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return

    # Clear old skills
    user.skills.clear()

    for name in skill_names:
        if name:
            skill = get_or_create_skill(db, name)
            if skill:
                user.skills.append(skill)

    db.commit()

def get_users_for_notification(db: Session):
    """Fetch users who specifically want email notifications."""
    return db.query(models.User).filter(models.User.notify_by_email == True).all()
