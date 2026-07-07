from datetime import datetime

import discord
from bot.database.session import SessionLocal
from bot.database.models.user_model import DangerMessage, Guild, UserProfile
from bot.ml.classifier import classify_danger_level
from bot.ml.image_classifier import classify_image


async def get_or_create_user(db, discord_id: str, message_guild: discord.Guild):
    """
    gets or creates a user profile for the given discord_id and guild
    """
    user = (
        db.query(UserProfile)
        .filter_by(
            guild_id=message_guild.id,
            discord_id=str(discord_id)
        )
        .first()
    )

    if user is None:
        user = UserProfile(discord_id=discord_id, guild_id=message_guild.id)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


async def get_or_create_guild(db, message_guild: discord.Guild):
    """
    gets or creates a guild profile for the given discord guild
    """
    guild = (
        db.query(Guild)
        .filter_by(
            discord_id=str(message_guild.id)
        )
        .first()
    )

    if guild is None:
        guild = Guild(
            discord_id=str(message_guild.id),
            name=message_guild.name
        )

        db.add(guild)
        db.commit()
        db.refresh(guild)
    
    return guild


async def add_vote(discord_id: str, guild: discord.Guild):
    """
    adds a vote to a user
    """
    db = SessionLocal()
    try:
        await get_or_create_guild(db, guild)
        user = await get_or_create_user(db, discord_id, guild)

        user.votes += 1
        db.commit()

    finally:
        db.close()



async def update_user(discord_id: str, message_id: str, content: str, timestamp: datetime, username: str, display_name: str, avatar_url: str, messsage_guild: discord.Guild, attachments: list[discord.Attachment] = []):
    """
    updates the users total messages, and top 10 most dangerous messages list for that user
    also updates any other cache information about the user
    """
    db = SessionLocal()

    try:
        await get_or_create_guild(db, messsage_guild)
        user = await get_or_create_user(db, discord_id, messsage_guild)

        #update cached info
        user.total_messages += 1
        user.username = username
        user.display_name = display_name
        user.avatar_url = avatar_url

        # classify message
        # the bigger danger score is from the image. We only keep track of the max of either the text or the image, not both. This is to avoid double counting.
        scores = await classify_danger_level(content)

        is_image = False
        for attachment in attachments:
            if attachment.content_type and attachment.content_type.startswith("image/"):
                result = await classify_image(attachment)
                if result["Danger"] > scores["Danger"]: #update new scores if the image is more dangerous than the text
                    scores["Danger"] = result["Danger"]
                    scores["Sexual"] = result["Sexual"]
                    scores["Hate"] = result["Hate"]
                    scores["Concern"] = result["Concern"]
                    scores["Scam"] = result["Scam"]
                    is_image = True
        
        if is_image: 
            content = f"[Image Attachment: {message_id}]"
            
        new_message = DangerMessage(
            message_id=str(message_id),
            content=content,
            danger_score=scores["Danger"],
            sexual_score=scores["Sexual"],
            hate_score=scores["Hate"],
            concern_score=scores["Concern"],
            scam_score=scores["Scam"],
            timestamp=timestamp
        )


        # old top
        top_messages = sorted(
            user.messages,
            key=lambda x: x.danger_score,
            reverse=True
        )

        # if exact message is repeated, it is not counted unless image
        if not is_image:
            top_message_content = [message.content for message in top_messages]
            if new_message.content in top_message_content:
                return
        
        
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
