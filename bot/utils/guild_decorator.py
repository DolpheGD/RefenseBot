import discord
from discord import app_commands
from bot.config import DEV_MODE, SERVER_ID


def guild_decorator(func):
    if DEV_MODE:
        return app_commands.guilds(
            discord.Object(id=SERVER_ID)
        )(func)

    return func