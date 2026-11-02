# functions for general user utilities, such as help commands, user info, etc.
import discord

from discord.ext import commands
from discord import app_commands
from bot.services.get_users import get_highest_danger, get_recent_classified_messages
from bot.services.update_user import recalibrate_server_image_urls
from bot.utils.guild_decorator import guild_decorator
from bot.utils.views import AchievementGuideView, LeaderboardView


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

    @guild_decorator
    @app_commands.command(
        name="log",
        description="Shows the most recent classified danger messages for this server"
    )
    @app_commands.describe(
        limit="How many recent classified messages to show",
        user="Optional user filter"
    )
    @app_commands.default_permissions(administrator=True)
    async def log(self, ctx: discord.Interaction, limit: int = 10, user: discord.User | None = None):
        limit = max(1, min(limit, 25))
        recent_messages = await get_recent_classified_messages(ctx.guild, limit=limit, discord_id=user.id if user else None)

        if not recent_messages:
            await ctx.response.send_message("No classified messages found for this server.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"Recent Classified Messages - {ctx.guild.name}",
            color=discord.Color.orange(),
        )

        lines = []
        for message in recent_messages:
            user_profile = message.user
            member_name = user_profile.display_name or user_profile.discord_id
            content = message.content.strip() if message.content else "(image-only)"
            if len(content) > 100:
                content = content[:97] + "..."

            image_note = f" | Image: {message.image_url}" if message.image_url else ""
            lines.append(f"{member_name}: {content}{image_note}\n(ID: {message.message_id})")

        embed.description = "\n\n".join(lines)
        await ctx.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(UserUtils(bot))