import discord

from discord.ext import commands
from discord import app_commands
from bot.utils.guild_decorator import guild_decorator
from bot.utils.embedder import classify_user_with_output, classify_with_output

@guild_decorator
class Classify(commands.GroupCog, name="classify"):
    def __init__(self, bot):
        self.bot = bot



    # COMMAND: /classify
    # This command takes a message as input and classifies it using the classify_message function from the classifier module.
    # It returns the classification results to the user.
    @app_commands.command(
        name = "text",
        description = "Classifies text input",
        
    )
    @app_commands.describe(
        text = "Text to classify"
    )
    async def classify_text(self, ctx: discord.Interaction, text: str):
        await ctx.response.send_message(embed=await classify_with_output(text))
    


    # COMMAND: /classify id
    # This command takes a message ID as input and classifies the corresponding message using the classify_message function from the classifier module.
    # It returns the classification results to the user.
    # TODO: classify ID should also check message attachments.
    @app_commands.command(
        name = "id",
        description = "Classifies a message by ID"
    )
    @app_commands.describe(
        message_id = "The ID of the message to classify"
    )
    async def classify_id(self, ctx: discord.Interaction, message_id: str):
        try:
            message = await ctx.channel.fetch_message(message_id)
            await ctx.response.send_message(embed=await classify_with_output(message.content))
        except discord.NotFound:
            await ctx.response.send_message("Message not found.", ephemeral=True)
        except discord.Forbidden:
            await ctx.response.send_message("I do not have permission to fetch that message.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.response.send_message(f"An error occurred while fetching the message:\n```{e}```", ephemeral=True)


    # COMMAND: /classify user
    # This command takes a user and classifies them according to their danger level
    @app_commands.command(
        name = "user",
        description = "Classifies a user according to their danger level"
    )
    @app_commands.describe(
        user = "The user to classify",
        verbose = "Show detailed message information"
    )
    async def classify_user(self, ctx: discord.Interaction, user: discord.Member, verbose: bool = False):
        await ctx.response.send_message(embed=await classify_user_with_output(user, verbose))




async def setup(bot):
    await bot.add_cog(Classify(bot))