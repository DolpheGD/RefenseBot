import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from bot.config import BOT_KEY, SERVER_ID, DEV_MODE
from bot.utils.check_files import check_files


load_dotenv()

# basic bot client setup, including command prefix and intents
class MyClient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(command_prefix='!', intents=intents)


    async def setup_hook(self):
        guild = discord.Object(id=SERVER_ID)

        for filename in os.listdir("bot/cogs"):
            if filename.endswith(".py"):
                extension = f"bot.cogs.{filename[:-3]}"
                await self.load_extension(f"bot.cogs.{filename[:-3]}")
                print(f"Loaded {extension}")


        # Clear and resync guild commands
        self.tree.clear_commands(guild=guild)
        print("Cleared guild commands")

    async def on_ready(self):
        try:
            if DEV_MODE:
                guild = discord.Object(id=SERVER_ID)
                
                synced = await self.tree.sync(guild=guild)
                print(f"Synced {len(synced)} guild commands.")
            else:
                synced = await self.tree.sync()
                print(f"Synced {len(synced)} global commands.")

        except Exception as e:
            print(e)

        print("Registered commands:")

        for cmd in self.tree.get_commands(guild=discord.Object(id=SERVER_ID)):
            print(cmd.name)

            guild = discord.Object(id=SERVER_ID)

        commands = await self.tree.fetch_commands(guild=guild)

        print("Discord has these commands:")

        for command in commands:
            print(command.name, command.type)
            if hasattr(command, "options"):
                print(command.options)

        print(f"Logged in as {self.user}")


def run_bot():
    #check required files
    check_files()
    bot = MyClient()
    bot.run(BOT_KEY)