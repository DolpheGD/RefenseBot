import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from bot.config import BOT_KEY, SERVER_ID, DEV_MODE
from bot.utils.sync_bans import sync_bans
from bot.utils.check_files import check_files
from webhook.webhook import setup_webhook

load_dotenv()

# basic bot client setup, including command prefix and intents
class MyClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(command_prefix='/', intents=intents)


    async def setup_hook(self):
        await sync_bans(self)

        await setup_webhook(self, 5000)

        debug = True
        if not DEV_MODE or debug:
            guild = discord.Object(id=SERVER_ID)

            self.tree.clear_commands(guild=guild)
            await self.tree.sync(guild=guild)


        for filename in os.listdir("bot/cogs"):
            if filename.endswith(".py"):
                await self.load_extension(
                    f"bot.cogs.{filename[:-3]}"
                )

        if DEV_MODE:
            guild = discord.Object(id=SERVER_ID)

            synced = await self.tree.sync(guild=guild)

            print(
                f"Synced {len(synced)} guild commands"
            )

        else:
            synced = await self.tree.sync()

            print(
                f"Synced {len(synced)} global commands"
            )


    async def on_ready(self):
        print(f"Logged in as {self.user}")


def run_bot():
    #check required files
    check_files()
    bot = MyClient()
    bot.run(BOT_KEY)