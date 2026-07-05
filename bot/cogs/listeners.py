# listeners to update data
import discord

from discord.ext import commands
from discord import app_commands
from bot.config import SERVER_ID
from bot.ml.image_classifier import classify_image
from bot.services.update_user import update_user
from bot.utils.guild_decorator import guild_decorator

@guild_decorator
class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # LISTENER: on_message
    # This listener triggers whenever a message is sent in the server
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.author.bot:
            return

        content = str(message.clean_content)
        attachments = message.attachments
        
        if len(content) > 0 and len(attachments) > 0:
            print('Message with both text and attachments detected. Processing both.')
        elif len(content) > 0:
            print('Message with text detected. Processing text.')
        elif len(attachments) > 0:
            print('Message with attachments detected. Processing attachments.')
        else:
            print('Message with no text or attachments detected. Skipping processing.')
            return
        
            
        user_id = str(message.author.id)
        message_id = str(message.id)
        message_time = message.created_at
        messsage_guild = message.guild

        username = message.author.name
        display_name = message.author.display_name
        if message.author.avatar:
            avatar_url = message.author.avatar.url
        else:
            avatar_url = ""        

        await update_user(user_id, message_id, content, message_time, username, display_name, avatar_url, messsage_guild, attachments)
        


async def setup(bot):
    await bot.add_cog(Listeners(bot))