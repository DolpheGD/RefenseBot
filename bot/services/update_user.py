from datetime import datetime
from bot.database.session import SessionLocal
from bot.database.models.user_model import DangerMessage, UserProfile
from bot.ml.classifier import classify_danger_level


def get_or_create_user(db, discord_id: str):
    user = db.query(UserProfile).filter_by(discord_id=discord_id).first()

    if not user:
        user = UserProfile(discord_id=discord_id)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


def update_user(discord_id: str, message_id: str, content: str, timestamp: datetime):
    """
    updates the users total messages, and top 10 most dangerous messages list
    """
    db = SessionLocal()

    try:
        user = get_or_create_user(db, discord_id)
        user.total_messages += 1

        # classify message
        scores = classify_danger_level(content)

        new_message = DangerMessage(
            message_id=str(message_id),
            content=content,
            danger_score=scores["Danger"],
            sexual_score=scores["Sexual"],
            hate_score=scores["Hate"],
            concern_score=scores["Concern"]
        )


        # old top
        top_messages = sorted(
            user.messages,
            key=lambda x: x.danger_score,
            reverse=True
        )
        
        # if new top, then update the message list
        changed = False
        if len(top_messages) < 10:
            user.messages.append(new_message)
            changed = True
        else:
            lowest = top_messages[-1]
            if scores["Danger"] > lowest.danger_score:
                db.delete(lowest)
                user.messages.append(new_message)
                changed = True

        # update the new top 10
        if changed:
            updated_top = sorted(
                user.messages,
                key=lambda x: x.danger_score,
                reverse=True
            )
            user.danger_score = (
                sum(msg.danger_score for msg in updated_top)
                / len(updated_top)
            )

        db.commit()

    finally:
        db.close()


def get_top_ten_and_avg(discord_id: int):
    """
    returns top ten danger and avg danger
    top ten danger is a list of message objects (I think)
    """
    db = SessionLocal()
    try:
        user = get_or_create_user(db, discord_id)

        top_messages = sorted(
            user.messages,
            key=lambda x: x.danger_score,
            reverse=True
        )
        danger_avg = user.danger_score

    finally:
        db.close()
    
    return top_messages, danger_avg