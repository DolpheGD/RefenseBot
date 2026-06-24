# listeners to update data
import discord

from discord.ext import commands
from discord import app_commands
from bot.config import SERVER_ID
from bot.services.update_user import update_user

@app_commands.guilds(discord.Object(id=SERVER_ID))  # remove when you want to make the command global
class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # LISTENER: on_message
    # This listener triggers whenever a message is sent in the server
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        user_id = str(message.author.id)
        update_user(user_id)
        


async def setup(bot):
    await bot.add_cog(Listeners(bot))