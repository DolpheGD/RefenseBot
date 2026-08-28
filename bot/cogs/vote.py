import discord

from bot.services.get_users import get_last_vote, get_vote_allow, set_vote_allow
from bot.services.update_user import add_vote, spend_vote
from discord.ext import commands
from discord import app_commands
from bot.utils.guild_decorator import guild_decorator
from bot.utils.views import VoteView


@guild_decorator
class Vote(commands.GroupCog, name="vote"):
    def __init__(self, bot):
        self.bot = bot


    # COMMAND: /vote link
    # This command displays the vote url.
    @app_commands.command(
        name = "link",
        description = "Gives the vote link"
    )
    async def link(self, ctx: discord.Interaction):
        last_voted = await get_last_vote(ctx.user.id, ctx.guild)
        view = VoteView(last_voted)
            
        await ctx.response.send_message(embed=view.create_embed(), view=view)
     


    # COMMAND: /vote allow
    # This command is admin only. Toggles vote allow for this server
    @app_commands.command(
        name = "allow",
        description = "Toggles if voting is enabled on this server"
    )
    @app_commands.describe(
        vote = "If the users can vote",
    )
    @app_commands.default_permissions(administrator=True)
    async def allow(self, ctx: discord.Interaction, vote: bool = True):
        can_vote = await get_vote_allow(ctx.guild)
        if can_vote and vote:
            await ctx.response.send_message(f"Voting already enabled for `{ctx.guild.name}`", ephemeral=True)
        elif not(can_vote or vote):
            await ctx.response.send_message(f"Voting already disabled for `{ctx.guild.name}`", ephemeral=True)
        else:
            await set_vote_allow(ctx.guild, vote)
            await ctx.response.send_message(f"Voting set to {vote} for `{ctx.guild.name}`", ephemeral=True)


    # COMMAND: /vote spend
    @app_commands.command(
        name = "spend",
        description = "Spend a vote to remove your most dangerous message. Only allowed if server enables it."
    )
    async def spend(self, ctx: discord.Interaction):
        can_vote = await get_vote_allow(ctx.guild)
        if can_vote:
            success, message = await spend_vote(ctx.user.id, ctx.guild)
            if not success:
                await ctx.response.send_message(f"Vote spending failed.\n**Reason:** `{message}`", ephemeral=True)
            else:
                await ctx.response.send_message(f"Vote spent successfully.\n **Removed:** `{message}`", ephemeral=True)
        else:
            await ctx.response.send_message(f"Vote spending for `{ctx.guild.name}` is disabled", ephemeral= True)
            
async def setup(bot):
    await bot.add_cog(Vote(bot))