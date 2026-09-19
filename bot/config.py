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
# Graceful memory watchdog: if Python RSS exceeds this threshold (MB) the bot
# exits cleanly so a supervisor / systemd can restart it before Linux OOM-kills it.
BOT_MEMORY_LIMIT_MB = int(os.getenv("BOT_MEMORY_LIMIT_MB", "512"))
BOT_MEMORY_CHECK_SECONDS = int(os.getenv("BOT_MEMORY_CHECK_SECONDS", "60"))