from sqlalchemy.orm import Session

from database import models


def get_user_by_telegram_id(db: Session, telegram_id: int):
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
        user.email = email.strip()
        user.notify_by_email = True
        db.commit()
        db.refresh(user)
    return user


def save_resume(db: Session, user_id: int, text_content: str, parsed_json: str | None = None):
    resume = db.query(models.Resume).filter(models.Resume.user_id == user_id).first()

    if resume:
        resume.text_content = text_content
        resume.parsed_json = parsed_json
    else:
        resume = models.Resume(
            user_id=user_id,
            text_content=text_content,
            parsed_json=parsed_json,
        )
        db.add(resume)

    db.commit()
    return resume


def get_or_create_skill(db: Session, skill_name: str):
    if not skill_name:
        return None

    skill_name = " ".join(skill_name.strip().split())
    if not skill_name:
        return None

    skill = db.query(models.Skill).filter(models.Skill.name == skill_name).first()

    if not skill:
        skill = models.Skill(name=skill_name)
        db.add(skill)
        db.flush()

    return skill


def link_skills_to_user(db: Session, user_id: int, skill_names: list[str]):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return

    user.skills.clear()

    for name in skill_names:
        skill = get_or_create_skill(db, name)
        if skill:
            user.skills.append(skill)

    db.commit()


def get_users_for_notification(db: Session):
    return db.query(models.User).filter(models.User.notify_by_email.is_(True)).all()
