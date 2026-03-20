import os

# Safe Integer Conversion
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN = int(os.environ.get("ADMIN", "0"))
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0"))

# String Variables
STRING_SESSION = os.environ.get("STRING_SESSION", "")
FORCE_SUBS = os.environ.get("FORCE_SUBS", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "TechifyBots")
START_PIC = os.environ.get("START_PIC", "https://graph.org/file/ada3f739fed7efdbe7b08.jpg")
