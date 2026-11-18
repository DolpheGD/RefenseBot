# functions for general user utilities, such as help commands, user info, etc.
import logging

import discord

from discord.ext import commands
from discord import app_commands
from bot.services.get_users import get_highest_danger
from bot.services.update_user import recalibrate_server_image_urls
from bot.utils.guild_decorator import guild_decorator
from bot.utils.views import AchievementGuideView, LeaderboardView

logger = logging.getLogger("refensebot.user_utils")


class UserUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # COMMAND: /help
    # This command lists all available bot commands to the user.
    @guild_decorator
    @app_commands.command(
        name = "help",
        description = "Lists all bot commands"
    )
    async def help(self, ctx: discord.Interaction):
        output = "Here are the available commands:\n" \
        "`/classify text <text>` - Classifies the provided text.\n" \
        "`/classify id <message_id>` - Classifies the message with the given ID.\n" \
        "`/classify user <user> <verbose [Optional]>` - Classifies the user with a danger rating and dangerous messages.\n" \
        "`/recent <limit>` - Lists the 10, 25, or 50 most recently classified messages in this server.\n" \
        "`/gemini <prompt> [context_messages]` - Prompts Gemini; reply to its prompt or answer to continue.\n" \
        "`/leaderboard` - Displays the top 10 most dangerous users.\n" \
        "`/achievements` - Displays the list of possible achievements in RefenseBot.\n" \
        "`/vote link` - Displays the link to vote for bot.\n" \
        "`/vote allow <vote [Optional]>` **(ADMIN ONLY)** - Toggle allowing `/vote spend` to remove dangerous messages using votes.\n" \
        "`/vote spend` - Spend one vote to remove your most dangerous message. Only works in servers that enable it with `/vote allow`\n" \
        "`/help` - Displays this help message."
        
        await ctx.response.send_message(output, ephemeral=True)


    # COMMAND: /leaderboard
    # This command lists the most dangerous users for this server
    # lets the user go through the list of all users
    @guild_decorator
    @app_commands.command(
        name = "leaderboard",
        description = "Lists the rankings of the most dangerous users for this server"
    )
    async def leaderboard(self, ctx: discord.Interaction):
        server_id = ctx.guild.id
        server_name = ctx.guild.name
        author_id = ctx.user.id

        users = await get_highest_danger(server_id)

        if not users:
            await ctx.response.send_message(
                "No users found."
            )
            return
        
        view = LeaderboardView(users, server_name, author_id)

        await ctx.response.send_message(
            embed=view.create_embed(),
            view=view
        )


    # COMMAND: /achievements
    # This command lists all the possible achievements in Refensebot
    @guild_decorator
    @app_commands.command(
        name = "achievements",
        description = "Lists all possible achievements in Refensebot"
    )
    async def achievements(self, ctx: discord.Interaction):
        author = ctx.user

        view = AchievementGuideView(author)

        await ctx.response.send_message(
            embed=view.create_embed(),
            view=view
        )

    @guild_decorator
    @app_commands.command(
        name="recalibrate",
        description="Refresh stored image URLs for dangerous messages in this server"
    )
    @app_commands.describe(
        user="Optional user to refresh; defaults to all users in the server"
    )
    @app_commands.default_permissions(administrator=True)
    async def recalibrate(self, ctx: discord.Interaction, user: discord.User | None = None):
        try:
            await ctx.response.defer(ephemeral=True)
            updated = await recalibrate_server_image_urls(ctx.guild, user.id if user is not None else None)
            if user is not None:
                await ctx.followup.send(
                    f"Recalibrated `{updated}` stored image records for {user.mention}.",
                    ephemeral=True
                )
            else:
                await ctx.followup.send(
                    f"Recalibrated `{updated}` stored image records across `{ctx.guild.name}`.",
                    ephemeral=True
                )
        except (discord.NotFound, discord.HTTPException) as exc:
            logger.warning("Ignoring stale /recalibrate interaction: %s", exc)

async def setup(bot):
    await bot.add_cog(UserUtils(bot))