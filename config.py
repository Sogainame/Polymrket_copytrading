import os
from dotenv import load_dotenv

load_dotenv()

# Your Polymarket wallet
POLY_PRIVATE_KEY = os.getenv("POLY_PRIVATE_KEY", "")
POLY_FUNDER_ADDRESS = os.getenv("POLY_FUNDER_ADDRESS", "")

# Target wallet to copy
TARGET_WALLET = os.getenv(
    "TARGET_WALLET",
    "0x909fa9f89976058b8b3ab87adc502ec7415ea8c3",  # BAdiosB
)

# Copy settings
COPY_RATIO = float(os.getenv("COPY_RATIO", "0.1"))
MAX_BET_USD = float(os.getenv("MAX_BET_USD", "10.0"))
MIN_BET_USD = float(os.getenv("MIN_BET_USD", "1.0"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))
MAX_PRICE = float(os.getenv("MAX_PRICE", "0.95"))
MIN_PRICE = float(os.getenv("MIN_PRICE", "0.05"))
COOLDOWN_SEC = int(os.getenv("COOLDOWN_SEC", "10"))

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
