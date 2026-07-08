import discord

from bot.services.get_users import get_vote_allow, set_vote_allow
from bot.services.update_user import add_vote
from discord.ext import commands
from discord import app_commands
from bot.utils.guild_decorator import guild_decorator


@guild_decorator
class Vote(commands.GroupCog, name="vote"):
    def __init__(self, bot):
        self.bot = bot


    # COMMAND: /vote
    # This command displays the vote url. for now it just gives one vote
    @app_commands.command(
        name = "link",
        description = "Gives the vote link"
    )
    @app_commands.default_permissions(administrator=True)
    async def link(self, ctx: discord.Interaction):
        can_vote = await get_vote_allow(ctx.guild)
        if can_vote:
            await add_vote(ctx.user.id, ctx.guild)
            await ctx.response.send_message("Added 1 vote", ephemeral= True)
        else:
            await ctx.response.send_message(f"Voting disabled for `{ctx.guild.name}`", ephemeral= True)        


    # COMMAND: /vote
    # This command displays the vote url. for now it just gives one vote
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





async def setup(bot):
    await bot.add_cog(Vote(bot))