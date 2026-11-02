from datetime import datetime, timezone

import discord
from bot.database.session import SessionLocal
from bot.database.models.user_model import DangerMessage, Guild, UserProfile
from bot.ml.all_classifier import classify_message_and_image


async def get_or_create_user(db, discord_id: str, message_guild: discord.Guild):
    """
    gets or creates a user profile for the given discord_id and guild
    """
    guild = await get_or_create_guild(db, message_guild)
    user = (
        db.query(UserProfile)
        .filter_by(
            guild_id=guild.id,
            discord_id=str(discord_id)
        )
        .first()
    )

    if user is None:
        user = UserProfile(discord_id=discord_id, guild_id=guild.id)
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



def get_image_url_from_attachments(attachments: list[discord.Attachment]) -> str:
    image_urls = [
        attachment.url
        for attachment in attachments
        if attachment.content_type and attachment.content_type.startswith("image/")
    ]
    return "; ".join(image_urls)


async def get_message_attachment_url(guild: discord.Guild, message_id: str):
    for channel in guild.channels:
        if not hasattr(channel, "fetch_message"):
            continue
        try:
            message = await channel.fetch_message(str(message_id))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            continue

        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith("image/"):
                return attachment.url
        for embed in message.embeds:
            if embed.image and embed.image.url:
                return embed.image.url
    return ""


async def recalibrate_server_image_urls(guild: discord.Guild, discord_id: str | None = None):
    db = SessionLocal()
    try:
        guild_db = await get_or_create_guild(db, guild)
        query = db.query(UserProfile).filter_by(guild_id=guild_db.id)
        if discord_id is not None:
            query = query.filter_by(discord_id=str(discord_id))

        users = query.all()
        updated = 0

        for user in users:
            for message in user.messages:
                message_ref = await get_message_attachment_url(guild, message.message_id)
                if not message_ref:
                    continue

                message.image_url = message_ref
                updated += 1

                fetched_message = None
                for channel in guild.channels:
                    if not hasattr(channel, "fetch_message"):
                        continue
                    try:
                        fetched_message = await channel.fetch_message(str(message.message_id))
                        break
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                        continue

                if fetched_message is not None:
                    if fetched_message.content:
                        message.content = fetched_message.content
                    if fetched_message.created_at:
                        message.timestamp = fetched_message.created_at

        db.commit()
        return updated
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

        image_url = get_image_url_from_attachments(attachments)
        scores, new_content, is_image = await classify_message_and_image(content, message_id, attachments)
            
        new_message = DangerMessage(
            message_id=str(message_id),
            content=new_content,
            image_url=image_url,
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
