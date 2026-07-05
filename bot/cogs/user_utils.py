# functions for general user utilities, such as help commands, user info, etc.
import discord

from discord.ext import commands
from discord import app_commands
from bot.services.get_users import get_ten_higher_danger
from bot.utils.guild_decorator import guild_decorator
from bot.utils.embedder import get_danger_color, leaderboard_danger_output

from bot.config import SERVER_ID


@guild_decorator
class UserUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # COMMAND: /help
    # This command lists all available bot commands to the user.
    @app_commands.command(
        name = "help",
        description = "Lists all bot commands"
    )
    async def help(self, ctx: discord.Interaction):
        output = "Here are the available commands:\n" \
        "`/classify text <text>` - Classifies the provided text.\n" \
        "`/classify id <message_id>` - Classifies the message with the given ID.\n" \
        "`/classify user <user> <verbose [Optional]>` - Classifies the user with a danger rating and dangerous messages.\n" \
        "`/leaderboard` - Displays the top 10 most dangerous users.\n" \
        "`/help` - Displays this help message."
        
        await ctx.response.send_message(output, ephemeral=True)


    # COMMAND: /leaderboard
    # This command lists the most dangerous users for this server
    @app_commands.command(
        name = "leaderboard",
        description = "Lists the rankings of the most dangerous users for this server"
    )
    async def leaderboard(self, ctx):
        server_id = ctx.guild.id
        server_name = ctx.guild.name

        users = await get_ten_higher_danger(server_id)

        if not users:
            await ctx.response.send_message(
                "No users found."
            )
            return

        await ctx.response.send_message(embed=await leaderboard_danger_output(users, server_name))



async def setup(bot):
    await bot.add_cog(UserUtils(bot))