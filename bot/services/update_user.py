from datetime import datetime, timezone

import discord
from bot.database.session import SessionLocal
from bot.database.models.user_model import DangerMessage, Guild, UserProfile
from bot.ml.all_classifier import classify_message_and_image


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


async def add_vote(discord_id: str):
    """
    adds a vote to a user, only by user ID. updates across all profiles
    if no guild profile for that guild, then vote doesnt coutn.
    """
    db = SessionLocal()
    try:
        users = (
            db.query(UserProfile)
            .filter_by(discord_id=str(discord_id))
            .all()
        )
        for user in users:
            user.votes += 1
            user.last_voted = datetime.now(timezone.utc)
        
        db.commit()

    finally:
        db.close()



async def spend_vote(discord_id: str, guild: discord.Guild):
    """
    spends a vote from the user to remove a danger message (only enabled on servers that allow)
    returns true if it was sucessful
    returns false if it was not
    """
    db = SessionLocal()
    try:
        await get_or_create_guild(db, guild)
        user = await get_or_create_user(db, discord_id, guild)

        top_messages = sorted(
            user.messages,
            key=lambda x: x.danger_score,
            reverse=True
        )

        if len(top_messages) > 0:
            if user.votes_used < user.votes:
                user.votes_used += 1
                highest = top_messages[0]
                db.delete(highest)
                db.commit()

                await update_topten(user)

                db.commit()
                return True, highest.content
            
            else:
                return False, "You need to vote before you spend.\nYou can check your vote balance with /classify user verbose=True"
        else:
            return False, "No messages to delete."
    
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

        scores, new_content, is_image = await classify_message_and_image(content, message_id, attachments)
            
        new_message = DangerMessage(
            message_id=str(message_id),
            content=new_content,
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
            await update_topten(user)
            
        db.commit()

    finally:
        db.close()



async def update_topten(user):
    updated_top = sorted(
        user.messages,
        key=lambda x: x.danger_score,
        reverse=True
    )
    if len(updated_top) <= 0:
        user.danger_score = 0
    else:
        user.danger_score = (
            sum(msg.danger_score for msg in updated_top)
            / len(updated_top)
        )
