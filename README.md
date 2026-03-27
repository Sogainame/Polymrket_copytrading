# Polymarket CopyTrading Bot

Automated copy-trading bot for [Polymarket](https://polymarket.com) prediction markets. Monitors a target wallet in real-time and mirrors their trades proportionally on your account.

## How It Works

1. **Watcher** polls the target wallet's activity every 30 seconds via Polymarket Data API
2. When a new **BUY** trade is detected, the bot evaluates it against safety filters (price range, bet size, market liquidity)
3. If it passes all checks, **Copier** places a maker GTC order on the same token with proportional sizing
4. After a market resolves as a WIN, the bot **auto-sells** winning tokens at $0.99 to recycle USDC back into balance
5. All trades are logged to CSV and optionally sent to Telegram

## Default Target

**BAdiosB** — `0x909fa9f89976058b8b3ab87adc502ec7415ea8c3`

| Metric | Value |
|--------|-------|
| PnL | $141,872 |
| Win Rate | 90.8% |
| ROI | 11.3% |
| Strategy | Manual directional bets, no hedging, no bots |

You can change the target wallet in `.env` to copy anyone.

## Safety Filters

- **Price range**: Skip tokens priced above $0.95 (no edge) or below $0.05 (too risky)
- **Max bet cap**: Hard USD limit per trade (default $10)
- **Copy ratio**: Proportional to target's size (default 10%)
- **Duplicate check**: Won't copy the same trade twice
- **Cooldown**: Minimum 10 seconds between orders

## Quick Start

```bash
git clone https://github.com/Sogainame/Polymrket_copytrading.git
cd Polymrket_copytrading
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys
```

### Dry Run (no real orders)
```bash
python bot.py
```

### Live Trading
```bash
python bot.py --live
```

### Options
```bash
python bot.py --live --max-bet 25 --ratio 0.2
python bot.py --target 0xANOTHER_WALLET --live
python bot.py --live --verbose
```

## Project Structure

```
├── bot.py              # Entry point + CLI
├── watcher.py          # Monitors target wallet activity
├── copier.py           # Evaluates and executes copy trades
├── market.py           # Polymarket CLOB API client
├── config.py           # Environment config loader
├── notifier.py         # Telegram notifications
├── requirements.txt
├── .env.example
└── data/               # Trade logs (CSV)
```

## Environment Variables

```
POLY_PRIVATE_KEY=0x...          # Your wallet private key
POLY_FUNDER_ADDRESS=0x...       # Your Polymarket proxy/funder address
TARGET_WALLET=0x909fa9f...      # Wallet to copy (default: BAdiosB)
COPY_RATIO=0.1                  # 10% of target's bet size
MAX_BET_USD=10                  # Hard cap per trade
POLL_INTERVAL=30                # Seconds between activity checks
TELEGRAM_BOT_TOKEN=             # Optional
TELEGRAM_CHAT_ID=               # Optional
```

## How to Find Wallets to Copy

1. **polymarket.com/leaderboard** — filter by category/time
2. **polymarketanalytics.com/traders** — search by name, filter by WR/ROI
3. **polyburg.com** — free alerts when tracked wallets trade
4. **polycopy.app** — curated leaderboard with copy-ready playbooks

### What Makes a Good Copy Target

- Win rate 60%+ over 50+ closed trades
- 4+ months track record
- Trades liquid markets (>$100K volume)
- Manual trader (<100 predictions/month)
- Builds positions over days, not hours
- Specializes in 2-3 categories

## Disclaimer

This bot is for educational purposes. Trading on prediction markets involves risk. Past performance does not guarantee future results. Never trade with money you can't afford to lose.
