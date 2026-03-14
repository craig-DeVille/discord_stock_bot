import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Whitelisted guild IDs — bot will leave any server not in this list
ALLOWED_GUILDS = {
    1402827341431967915,
    1442280884869922908,
    1475640131179511830,
}

# Pre-loaded oil watchlist
DEFAULT_WATCHLIST = ["USO", "UCO", "BNO", "CLJ26.NYM"]

# Default volatility alert threshold (% move in a single day)
DEFAULT_VOL_THRESHOLD = 5.0

# How often the alert checker runs (seconds)
ALERT_CHECK_INTERVAL = 300  # 5 minutes

# Market open/close summary times (ET)
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MINUTE = 35
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 5

TIMEZONE = "America/New_York"
