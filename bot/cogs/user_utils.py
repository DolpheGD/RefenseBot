# functions for general user utilities, such as help commands, user info, etc.
import discord

from discord.ext import commands
from discord import app_commands

from bot.config import SERVER_ID

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # COMMAND: /help
    # This command lists all available bot commands to the user.
    @app_commands.guilds(discord.Object(id=SERVER_ID))  # remove when you want to make the command global
    @app_commands.command(
        name = "help",
        description = "Lists all bot commands"
    )
    async def help(self, ctx):
        output = "Here are the available commands:\n" \
        "`/classify text <text>` - Classifies the provided text.\n" \
        "`/classify id <message_id>` - Classifies the message with the given ID.\n" \
        "`/help` - Displays this help message."
        
        await ctx.response.send_message(output, ephemeral=True)






async def setup(bot):
    await bot.add_cog(Help(bot))