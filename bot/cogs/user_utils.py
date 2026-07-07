# functions for general user utilities, such as help commands, user info, etc.
import discord

from discord.ext import commands
from discord import app_commands
from bot.services.get_users import get_highest_danger
from bot.services.update_user import add_vote
from bot.utils.guild_decorator import guild_decorator
from bot.utils.views import LeaderboardView


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
    # lets the user go through the list of all users
    @app_commands.command(
        name = "leaderboard",
        description = "Lists the rankings of the most dangerous users for this server"
    )
    async def leaderboard(self, ctx: discord.Interaction):
        server_id = ctx.guild.id
        server_name = ctx.guild.name

        users = await get_highest_danger(server_id)

        if not users:
            await ctx.response.send_message(
                "No users found."
            )
            return
        
        view = LeaderboardView(users, server_name)

        await ctx.response.send_message(
            embed=view.create_embed(),
            view=view
        )

"""
    # COMMAND: /vote
    # This command displays the vote url. for now it just gives one vote
    @app_commands.command(
        name = "vote",
        description = "votes"
    )
    @app_commands.default_permissions(administrator=True)
    async def vote(self, ctx: discord.Interaction):
        add_vote(ctx.user.id, ctx.guild)
        await ctx.response.send_message("Added 1 vote")
"""

async def setup(bot):
    await bot.add_cog(UserUtils(bot))