# listeners to update data

import discord
from discord.ext import commands
from bot.services.get_users import set_user_banned
from bot.services.update_user import update_user, add_vote
from bot.utils.guild_decorator import guild_decorator 

class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # LISTENER: on_message
    # This listener triggers whenever a message is sent in the server
    @guild_decorator
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        if message.author.bot:
            return

        content = str(message.clean_content)
        attachments = message.attachments
        
        if len(attachments) > 0:
            # we only accept images. If there is no image, and no content, return
            has_image = False
            for attachment in attachments:
                if attachment.content_type and attachment.content_type.startswith("image/"):
                    has_image = True
                    break
            if not has_image:
                return
            
        if len(content) <= 0 and len(attachments) <= 0:
            print('Message with no text or attachments detected. Skipping processing.')
            return
        else:
            print(f'Message Processing "{content}" with {len(attachments)} attachments.')
        
            
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
        
        
    @guild_decorator
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        await set_user_banned(
            discord_id=user.id,
            guild=guild,
            banned=True
        )


    @guild_decorator
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        await set_user_banned(
            discord_id=user.id,
            guild=guild,
            banned=False
        )

    @guild_decorator
    @commands.Cog.listener()
    async def on_dbl_vote(self, data: dict):
        user_id = int(data["user"])

        await add_vote(user_id)

        print(f"Vote credited for user {user_id}")


async def setup(bot):
    await bot.add_cog(Listeners(bot))