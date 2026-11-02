import os
from dotenv import load_dotenv

load_dotenv()

BOT_KEY = os.getenv("BOT_KEY")
SERVER_ID = int(os.getenv("SERVER_ID"))
DEV_MODE = os.getenv("DEV_MODE") == "True"
HF_TOKEN = os.getenv("HF_TOKEN")
TOPGG_TOKEN = os.getenv("TOPGG_TOKEN")
# Use local ML models (loads transformers/torch into memory). Set to "True" only if the host has sufficient RAM.
USE_LOCAL_ML = os.getenv("USE_LOCAL_ML", "False") == "True"
# When enabled, the bot starts with the smallest practical Discord cache and intents
# footprint to reduce RAM usage on low-memory hosts.
LOW_RAM_MODE = os.getenv("LOW_RAM_MODE", "True") == "True"
DISCORD_MAX_MESSAGE_CACHE = int(os.getenv("DISCORD_MAX_MESSAGE_CACHE", "2000"))
DISCORD_CHUNK_GUILDS_AT_STARTUP = os.getenv("DISCORD_CHUNK_GUILDS_AT_STARTUP", "False") == "True"
# Graceful memory watchdog: when the RSS exceeds this threshold (MB), the bot
# logs a warning and performs a GC pass. Set this to a positive number only when
# you intentionally want the process to auto-exit on memory pressure. A value of 0
# disables the watchdog entirely to keep the bot running and record the issue in logs.
BOT_MEMORY_LIMIT_MB = int(os.getenv("BOT_MEMORY_LIMIT_MB", "0"))
BOT_MEMORY_CHECK_SECONDS = int(os.getenv("BOT_MEMORY_CHECK_SECONDS", "60"))