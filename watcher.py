"""Watches a target wallet for new BUY trades on Polymarket."""

import time
from dataclasses import dataclass, field
from market import PolymarketClient
import config


@dataclass
class DetectedTrade:
    """A new trade detected from the target wallet."""
    trade_id: str
    token_id: str
    condition_id: str
    side: str           # BUY / SELL
    price: float
    size: float         # shares
    cost_usd: float     # price * size
    title: str
    outcome: str
    event_slug: str
    timestamp: int


class WalletWatcher:
    """Polls target wallet activity and yields new BUY trades."""

    def __init__(self, client: PolymarketClient, target: str = ""):
        self.client = client
        self.target = target or config.TARGET_WALLET
        self.seen_ids: set[str] = set()
        self._first_poll = True

    def poll(self) -> list[DetectedTrade]:
        """Check for new trades. Returns list of unseen BUY trades."""
        raw = self.client.get_user_trades(self.target, limit=20)
        if not raw:
            return []

        new_trades = []
        for t in raw:
            tid = self._extract_id(t)
            if not tid or tid in self.seen_ids:
                continue
            self.seen_ids.add(tid)

            # On first poll, just seed the seen set — don't copy old trades
            if self._first_poll:
                continue

            side = (t.get("side") or t.get("type") or "").upper()
            if side != "BUY":
                continue

            trade = self._parse_trade(t, tid)
            if trade:
                new_trades.append(trade)

        self._first_poll = False
        return new_trades

    def _extract_id(self, t: dict) -> str:
        """Extract a unique ID from a trade dict."""
        return (
            t.get("id")
            or t.get("transactionHash")
            or t.get("transaction_hash")
            or f"{t.get('timestamp', '')}-{t.get('asset', '')}-{t.get('size', '')}"
        )

    def _parse_trade(self, t: dict, tid: str) -> DetectedTrade | None:
        """Parse raw API trade into DetectedTrade."""
        try:
            token_id = t.get("asset") or t.get("token_id") or ""
            condition_id = t.get("conditionId") or t.get("condition_id") or ""
            price = float(t.get("price", 0))
            size = float(t.get("size", 0))
            title = t.get("title") or t.get("market") or ""
            outcome = t.get("outcome") or t.get("name") or ""
            event_slug = t.get("eventSlug") or t.get("slug") or ""
            timestamp = int(t.get("timestamp") or t.get("created_at") or 0)

            if not token_id or price <= 0 or size <= 0:
                return None

            return DetectedTrade(
                trade_id=tid,
                token_id=token_id,
                condition_id=condition_id,
                side="BUY",
                price=price,
                size=size,
                cost_usd=round(price * size, 2),
                title=title,
                outcome=outcome,
                event_slug=event_slug,
                timestamp=timestamp,
            )
        except (ValueError, TypeError):
            return None
