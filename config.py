import os
from dotenv import load_dotenv

load_dotenv()

# Your Polymarket wallet
POLY_PRIVATE_KEY = os.getenv("POLY_PRIVATE_KEY", "")
POLY_FUNDER_ADDRESS = os.getenv("POLY_FUNDER_ADDRESS", "")

# Target wallets to copy (comma-separated in .env, or use defaults)
_default_targets = ",".join([
    "0x909fa9f89976058b8b3ab87adc502ec7415ea8c3",  # BAdiosB — ROI 11.3%, WR 90.8%
    "0x45bc74efa620b45c02308acaecdff1f7c06f978b",  # simonbanza — WR 59%, $1.9M/2wks, sports
    "0x63ce342161250d705dc0b16df89036c8e5f9ba9a",  # LucasMeow — WR 94.9%, systematic
])
TARGET_WALLETS_STR = os.getenv("TARGET_WALLETS", _default_targets)
TARGET_WALLETS: list[dict] = []

_names = {
    "0x909fa9f89976058b8b3ab87adc502ec7415ea8c3": "BAdiosB",
    "0x45bc74efa620b45c02308acaecdff1f7c06f978b": "simonbanza",
    "0x63ce342161250d705dc0b16df89036c8e5f9ba9a": "LucasMeow",
}

for addr in TARGET_WALLETS_STR.split(","):
    addr = addr.strip().lower()
    if addr:
        TARGET_WALLETS.append({
            "address": addr,
            "name": _names.get(addr, addr[:10] + "..."),
        })

# Legacy single target (first in list)
TARGET_WALLET = TARGET_WALLETS[0]["address"] if TARGET_WALLETS else ""

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
