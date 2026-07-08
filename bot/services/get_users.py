import discord
from sqlalchemy import select

from bot.database.session import SessionLocal
from bot.database.models.user_model import UserProfile
from bot.services.update_user import get_or_create_guild, get_or_create_user

async def get_top_ten_and_avg(discord_id: int, guild: discord.Guild):
    """
    returns top ten danger and avg danger of a user within a server
    top ten danger is a list of message objects (I think)
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
        danger_avg = user.danger_score

    finally:
        db.close()
    
    return top_messages, danger_avg



async def get_highest_danger(server_id: int):
    """
    returns the highest danger individuals for the server
    """
    db = SessionLocal()
    try:
        users = (
            db.query(UserProfile)
            .filter_by(guild_id=server_id)
            .order_by(UserProfile.danger_score.desc())
            .where(UserProfile.is_banned == False)
            .all()
        )

        if not users:
            return None
        
        return users
        
    finally:
        db.close()


async def get_total_messages(discord_id: int, guild: discord.Guild):
    """
    returns the total number of messages for a user in this guild
    """
    db = SessionLocal()
    try:
        await get_or_create_guild(db, guild)
        user = await get_or_create_user(db, discord_id, guild)
        total_messages = user.total_messages

        return total_messages
    finally:
        db.close()


async def get_vote_count(discord_id: int, guild: discord.Guild):
    """
    returns the total number of votes accumulated for a user in this guild
    """
    db = SessionLocal()
    try:
        await get_or_create_guild(db, guild)
        user = await get_or_create_user(db, discord_id, guild)
        votes = user.votes

        return votes
    finally:
        db.close()


async def get_is_banned(discord_id: int, guild: discord.Guild):
    """
    returns the user ban
    """
    db = SessionLocal()
    try:
        await get_or_create_guild(db, guild)
        user = await get_or_create_user(db, discord_id, guild)
        is_banned = user.is_banned

        return is_banned
    finally:
        db.close()



async def get_vote_allow(guild: discord.Guild):
    """
    gets if this server allows votes
    """
    db = SessionLocal()
    try:
        user_guild = await get_or_create_guild(db, guild)
        allow_vote = user_guild.allow_votes

        return allow_vote
    finally:
        db.close()


async def set_vote_allow(guild: discord.Guild, setting: bool):
    """
    gets if this server allows votes
    """
    db = SessionLocal()
    try:
        user_guild = await get_or_create_guild(db, guild)
        user_guild.allow_votes = setting
        print(f'setting {user_guild.name} to {setting}')
        db.commit()
        
    finally:
        db.close()



async def set_user_banned(discord_id: int, guild: discord.Guild, banned):
    db = SessionLocal()
    try:
        
        await get_or_create_guild(db, guild)
        user = await get_or_create_user(db, discord_id, guild)

        if user is None:
            return

        user.is_banned = banned

        db.commit()
        
    finally:
        db.close()
