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