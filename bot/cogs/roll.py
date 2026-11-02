import secrets

import discord
from discord import app_commands
from discord.ext import commands

from bot.roll_game import MAX_ROLL, RANK_EMOJIS, get_badge_emoji, score_roll


class Roll(commands.Cog):
    """Standalone, stateless roll game."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="roll", description="Roll a number and discover its rarity")
    async def roll(self, interaction: discord.Interaction):
        result = score_roll(secrets.randbelow(MAX_ROLL + 1))
        embed = discord.Embed(
            title=f"🎲 {result.number:,}",
            description=(
                f"**{RANK_EMOJIS[result.rank]} {result.rank}** roll — "
                f"**{result.score} points**"
            ),
            color=discord.Color.gold(),
        )

        if result.traits:
            badge_lines = [
                f"{get_badge_emoji(trait)} {trait}: **+{points}**"
                for trait, points in result.traits
            ]
            field_values = []
            current_value = ""
            for line in badge_lines:
                if current_value and len(current_value) + len(line) + 1 > 1_000:
                    field_values.append(current_value)
                    current_value = ""
                current_value = f"{current_value}\n{line}".strip()
            if current_value:
                field_values.append(current_value)

            for index, field_value in enumerate(field_values):
                embed.add_field(
                    name="Roll badges" if index == 0 else "More roll badges",
                    value=field_value,
                    inline=False,
                )
        else:
            embed.add_field(name="Roll badges", value="No special traits this time.", inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Roll(bot))
