"""Polymarket CLOB client for order placement and market queries."""

import time
import httpx
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType, MarketOrderArgs
from py_clob_client.order_builder.constants import BUY, SELL

import config

CLOB_HOST = "https://clob.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"
DATA_API = "https://data-api.polymarket.com"
CHAIN_ID = 137


class PolymarketClient:

    def __init__(self):
        self.http = httpx.Client(timeout=15.0)
        self.clob = self._init_clob()

    def _init_clob(self) -> ClobClient:
        client = ClobClient(
            host=CLOB_HOST,
            key=config.POLY_PRIVATE_KEY,
            chain_id=CHAIN_ID,
            signature_type=1,
            funder=config.POLY_FUNDER_ADDRESS,
        )
        try:
            creds = client.create_or_derive_api_creds()
            if creds:
                client.set_api_creds(creds)
        except Exception as e:
            print(f"  [!] CLOB creds warning: {e}")
        return client

    # ── Balance ──────────────────────────────────────────────────────
    def get_balance(self) -> float:
        """Get USDC balance from Polymarket data API."""
        try:
            wallet = config.POLY_FUNDER_ADDRESS or ""
            if not wallet:
                return 0.0
            r = self.http.get(
                f"{DATA_API}/value",
                params={"user": wallet.lower()},
            )
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and data:
                    return float(data[0].get("value", 0))
                elif isinstance(data, dict):
                    return float(data.get("value", 0))
        except Exception:
            pass
        return 0.0

    # ── Target Activity ──────────────────────────────────────────────
    def get_user_trades(self, wallet: str, limit: int = 20) -> list:
        """Fetch recent trades for a wallet via data API."""
        try:
            r = self.http.get(
                f"{DATA_API}/activity",
                params={"user": wallet.lower(), "limit": limit},
            )
            if r.status_code == 200:
                return r.json() if isinstance(r.json(), list) else []
        except Exception:
            pass

        # Fallback: CLOB trades endpoint
        try:
            r = self.http.get(
                f"{CLOB_HOST}/trades",
                params={"maker": wallet.lower(), "limit": limit},
            )
            if r.status_code == 200:
                data = r.json()
                return data if isinstance(data, list) else data.get("trades", [])
        except Exception:
            pass

        return []

    # ── Market Info ──────────────────────────────────────────────────
    def get_market_by_condition(self, condition_id: str) -> dict | None:
        """Lookup market details by condition ID."""
        try:
            r = self.http.get(
                f"{GAMMA_API}/markets",
                params={"condition_id": condition_id, "limit": 1},
            )
            if r.status_code == 200:
                markets = r.json()
                if markets:
                    return markets[0] if isinstance(markets, list) else markets
        except Exception:
            pass
        return None

    def get_token_price(self, token_id: str) -> float | None:
        """Get current best price for a token."""
        try:
            r = self.http.get(f"{CLOB_HOST}/price", params={"token_id": token_id, "side": "buy"})
            if r.status_code == 200:
                data = r.json()
                return float(data.get("price", 0))
        except Exception:
            pass
        return None

    # ── Order Placement ──────────────────────────────────────────────
    def submit_buy(self, token_id: str, price: float, shares: int, label: str = "") -> str | None:
        """Place a maker GTC BUY order. Returns order ID or None."""
        try:
            args = OrderArgs(
                token_id=token_id,
                price=round(price, 2),
                size=shares,
                side=BUY,
                fee_rate_bps=0,
            )
            signed = self.clob.create_order(args)
            resp = self.clob.post_order(signed, OrderType.GTC)

            oid = None
            if isinstance(resp, dict):
                oid = resp.get("orderID") or resp.get("id")
            elif isinstance(resp, str):
                oid = resp

            tag = f" [{label}]" if label else ""
            print(f"  [ORDER] BUY{tag} @ {price} x {shares}sh | ID: {oid}")
            return oid

        except Exception as e:
            print(f"  [ORDER ERR] {label}: {e}")
            return None

    def submit_sell(self, token_id: str, price: float, shares: float, label: str = "") -> str | None:
        """Place a FOK SELL order to cash out winning tokens."""
        try:
            # Update conditional token allowance
            try:
                from py_clob_client.clob_types import BalanceAllowanceParams, AssetType
                self.clob.update_balance_allowance(
                    BalanceAllowanceParams(
                        asset_type=AssetType.CONDITIONAL,
                        token_id=token_id,
                    )
                )
            except Exception:
                pass

            args = MarketOrderArgs(
                token_id=token_id,
                amount=round(shares, 2),
                price=0.99,
                side=SELL,
                fee_rate_bps=1000,
            )
            signed = self.clob.create_market_order(args)
            resp = self.clob.post_order(signed, OrderType.FOK)

            oid = None
            if isinstance(resp, dict):
                oid = resp.get("orderID") or resp.get("id")

            print(f"  [SELL] {label} @ 0.99 x {shares:.2f}sh | ID: {oid}")
            return oid

        except Exception as e:
            print(f"  [SELL ERR] {label}: {e}")
            return None
