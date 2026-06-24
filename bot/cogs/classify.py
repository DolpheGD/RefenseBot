import discord

from discord.ext import commands
from discord import app_commands
from bot.ml.classifier import classify_with_output
from bot.config import SERVER_ID

@app_commands.guilds(discord.Object(id=SERVER_ID))  # remove when you want to make the command global
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
    async def classify_text(self, ctx, text: str):
        output = classify_with_output(text)
        await ctx.response.send_message(f"**Classification results:**\n{output}")
    

    # COMMAND: /classify id
    # This command takes a message ID as input and classifies the corresponding message using the classify_message function from the classifier module.
    # It returns the classification results to the user.
    @app_commands.command(
        name = "id",
        description = "Classifies a message by ID"
    )
    @app_commands.describe(
        message_id = "The ID of the message to classify"
    )
    async def classify_id(self, ctx, message_id: str):
        try:
            message = await ctx.channel.fetch_message(message_id)
            output = classify_with_output(message.content)
            await ctx.response.send_message(f"**Classification results:**\n{output}")
        except discord.NotFound:
            await ctx.response.send_message("Message not found.", ephemeral=True)
        except discord.Forbidden:
            await ctx.response.send_message("I do not have permission to fetch that message.", ephemeral=True)
        except discord.HTTPException as e:
            await ctx.response.send_message(f"An error occurred while fetching the message:\n```{e}```", ephemeral=True)
    



async def setup(bot):
    await bot.add_cog(Classify(bot))