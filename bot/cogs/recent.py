import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.services.get_users import get_recent_classified_messages
from bot.utils.guild_decorator import guild_decorator

logger = logging.getLogger("refensebot.recent")


class RecentClassified(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="recent",
        description="Lists recently classified messages in this server",
    )
    @app_commands.guild_only()
    @app_commands.choices(
        limit=[
            app_commands.Choice(name="10 most recent", value=10),
            app_commands.Choice(name="25 most recent", value=25),
            app_commands.Choice(name="50 most recent", value=50),
        ]
    )
    @guild_decorator
    async def recent(
        self,
        interaction: discord.Interaction,
        limit: app_commands.Choice[int],
    ):
        try:
            await interaction.response.defer()
            guild = interaction.guild
            if guild is None:
                await interaction.followup.send(
                    "This command can only be used in a server.",
                    ephemeral=True,
                )
                return

            messages = await get_recent_classified_messages(
                guild,
                limit=limit.value,
            )

            if not messages:
                await interaction.followup.send(
                    "No classified messages found for this server."
                )
                return

            embeds = []
            for start in range(0, len(messages), 10):
                batch = messages[start : start + 10]
                lines = []
                for index, message in enumerate(batch, start=start + 1):
                    user = message.user
                    name = user.display_name or user.discord_id
                    content = message.content.strip() if message.content else "(image-only)"
                    if len(content) > 200:
                        content = content[:197] + "..."
                    if message.image_url and message.content:
                        content += " (image attached)"

                    lines.append(
                        f"**{index}. {name}** | danger {message.danger_score:.2%}\n"
                        f"{content}\n"
                        f"Message ID: `{message.message_id}`"
                    )

                page = start // 10 + 1
                page_count = (len(messages) + 9) // 10
                embeds.append(
                    discord.Embed(
                        title=f"Recent Classified Messages - {guild.name} "
                        f"({page}/{page_count})",
                        description="\n\n".join(lines),
                        color=discord.Color.orange(),
                    )
                )

            await interaction.followup.send(embeds=embeds)
        except (discord.NotFound, discord.HTTPException) as exc:
            logger.warning("Ignoring stale /recent interaction: %s", exc)


async def setup(bot: commands.Bot):
    await bot.add_cog(RecentClassified(bot))
