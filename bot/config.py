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
# Graceful memory watchdog: if Python RSS exceeds this threshold (MB) the bot
# exits cleanly so a supervisor / systemd can restart it before Linux OOM-kills it.
# 512MB is too aggressive for a CPU-heavy moderation bot; 1024MB is a safer default
# for Raspberry Pi / small Linux hosts that load local models or OCR dependencies.
BOT_MEMORY_LIMIT_MB = int(os.getenv("BOT_MEMORY_LIMIT_MB", "1024"))
BOT_MEMORY_CHECK_SECONDS = int(os.getenv("BOT_MEMORY_CHECK_SECONDS", "60"))