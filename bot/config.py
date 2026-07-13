import os
from dotenv import load_dotenv

load_dotenv()

BOT_KEY = os.getenv("BOT_KEY")
SERVER_ID = int(os.getenv("SERVER_ID"))
DEV_MODE = os.getenv("DEV_MODE") == "True"
HF_TOKEN = os.getenv("HF_TOKEN")
WEBHOOK_SECRET = os.getenv("TOPGG_WEBHOOK_SECRET")