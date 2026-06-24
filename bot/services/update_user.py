from bot.database.session import SessionLocal
from bot.database.models.user_model import UserProfile


def get_or_create_user(db, user_id: str):
    user = db.query(UserProfile).filter_by(user_id=user_id).first()

    if not user:
        user = UserProfile(user_id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


def update_user(user_id: str):
    db = SessionLocal()

    try:
        user = get_or_create_user(db, user_id)

        # update stats
        user.message_count += 1
        db.commit()

    finally:
        db.close()