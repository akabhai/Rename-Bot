import os

# Safe Integer Conversion function
def get_int(env_name, default=0):
    val = os.environ.get(env_name, "")
    if not val or val.strip() == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default

# Required Variables Config
API_ID = get_int("API_ID")
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN = get_int("ADMIN")

# Premium 4GB Renaming Client Config
STRING_SESSION = os.environ.get("STRING_SESSION", "")

# Log & Force Channel Config
FORCE_SUBS = os.environ.get("FORCE_SUBS", "")
LOG_CHANNEL = get_int("LOG_CHANNEL")

# Mongo DB Database Config
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# CRITICAL FIX: The "or" ensures that if DATABASE_NAME is an empty string "", 
# it will use "TechifyBots" as the fallback.
DATABASE_NAME = os.environ.get("DATABASE_NAME") or "TechifyBots"

# Other Variables Config
START_PIC = os.environ.get("START_PIC", "https://graph.org/file/ada3f739fed7efdbe7b08.jpg")
