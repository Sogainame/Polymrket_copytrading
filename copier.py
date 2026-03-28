"""Evaluates detected trades and executes copy orders."""

import csv
import os
import time
from dataclasses import dataclass
from watcher import DetectedTrade
from market import PolymarketClient
from notifier import send_telegram
import config

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, "copy_trades.csv")


@dataclass
class CopyResult:
    trade: DetectedTrade
    action: str          # COPIED / SKIPPED / ERROR
    reason: str
    our_price: float
    our_shares: int
    our_cost: float
    order_id: str


class Copier:
    """Decides whether to copy a trade and executes it."""

    def __init__(self, client: PolymarketClient, dry_run: bool = True,
                 max_bet: float = 0, copy_ratio: float = 0):
        self.client = client
        self.dry_run = dry_run
        self.max_bet = max_bet or config.MAX_BET_USD
        self.copy_ratio = copy_ratio or config.COPY_RATIO
        self.last_order_time = 0.0
        self._init_csv()

    # ── Evaluate & Execute ───────────────────────────────────────────
    def process(self, trade: DetectedTrade) -> CopyResult:
        """Evaluate a detected trade and optionally copy it."""

        # Filter 1: Skip 5-minute Up/Down markets (bots only, not copyable)
        _skip_keywords = ["Up or Down", "updown", "5m", "15m", "5-minute", "15-minute"]
        title_lower = trade.title.lower()
        if any(kw.lower() in title_lower for kw in _skip_keywords):
            return self._skip(trade, "5-min bot market — not copyable")

        # Filter 2: Price range
        if trade.price > config.MAX_PRICE:
            return self._skip(trade, f"price {trade.price:.2f} > max {config.MAX_PRICE}")
        if trade.price < config.MIN_PRICE:
            return self._skip(trade, f"price {trade.price:.2f} < min {config.MIN_PRICE}")

        # Filter 3: Calculate our bet size
        target_cost = trade.cost_usd
        our_cost = round(target_cost * self.copy_ratio, 2)
        if our_cost > self.max_bet:
            our_cost = self.max_bet
        if our_cost < config.MIN_BET_USD:
            return self._skip(trade, f"cost ${our_cost:.2f} < min ${config.MIN_BET_USD}")

        # Filter 4: Cooldown
        now = time.time()
        if now - self.last_order_time < config.COOLDOWN_SEC:
            return self._skip(trade, f"cooldown ({config.COOLDOWN_SEC}s)")

        # Filter 5: Check current price on orderbook
        current_price = self.client.get_token_price(trade.token_id)
        if current_price is None:
            return self._skip(trade, "can't fetch current price")
        if current_price > config.MAX_PRICE:
            return self._skip(trade, f"current price {current_price:.2f} > max")

        # Use current price (might have moved since target's trade)
        buy_price = round(current_price, 2)
        shares = max(1, int(our_cost / buy_price))
        actual_cost = round(shares * buy_price, 2)

        # Execute
        label = f"COPY-{trade.outcome or trade.title[:20]}"

        if self.dry_run:
            print(f"  [DRY] Would BUY {shares}sh @ {buy_price} = ${actual_cost:.2f}")
            print(f"         Market: {trade.title}")
            print(f"         Outcome: {trade.outcome}")
            print(f"         Target paid: ${trade.cost_usd:.2f}")
            return self._result(trade, "DRY_COPY", "dry run", buy_price, shares, actual_cost, "DRY")

        order_id = self.client.submit_buy(trade.token_id, buy_price, shares, label)
        self.last_order_time = time.time()

        if order_id:
            msg = (
                f"🔄 <b>COPY TRADE</b>\n"
                f"Market: {trade.title}\n"
                f"Outcome: {trade.outcome}\n"
                f"Price: {buy_price} x {shares}sh = ${actual_cost:.2f}\n"
                f"Target: ${trade.cost_usd:.2f} @ {trade.price}\n"
                f"Order: {order_id}"
            )
            send_telegram(msg)
            result = self._result(trade, "COPIED", "ok", buy_price, shares, actual_cost, order_id)
        else:
            result = self._result(trade, "ERROR", "order failed", buy_price, shares, actual_cost, "")

        self._log_csv(result)
        return result

    # ── Helpers ───────────────────────────────────────────────────────
    def _skip(self, trade: DetectedTrade, reason: str) -> CopyResult:
        print(f"  [SKIP] {reason} | {trade.title[:40]} / {trade.outcome}")
        return self._result(trade, "SKIPPED", reason, 0, 0, 0, "")

    def _result(self, trade, action, reason, price, shares, cost, oid) -> CopyResult:
        return CopyResult(
            trade=trade, action=action, reason=reason,
            our_price=price, our_shares=shares, our_cost=cost, order_id=oid,
        )

    # ── CSV Logging ──────────────────────────────────────────────────
    def _init_csv(self):
        if not os.path.exists(CSV_PATH):
            with open(CSV_PATH, "w", newline="") as f:
                w = csv.writer(f)
                w.writerow([
                    "timestamp", "action", "reason",
                    "market", "outcome", "target_price", "target_size", "target_cost",
                    "our_price", "our_shares", "our_cost", "order_id",
                ])

    def _log_csv(self, r: CopyResult):
        try:
            with open(CSV_PATH, "a", newline="") as f:
                w = csv.writer(f)
                w.writerow([
                    int(time.time()), r.action, r.reason,
                    r.trade.title, r.trade.outcome,
                    r.trade.price, r.trade.size, r.trade.cost_usd,
                    r.our_price, r.our_shares, r.our_cost, r.order_id,
                ])
        except Exception:
            pass
