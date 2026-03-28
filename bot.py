#!/usr/bin/env python3
"""Polymarket CopyTrading Bot — mirrors trades from a target wallet."""

import argparse
import signal
import sys
import time

import config
from market import PolymarketClient
from watcher import WalletWatcher
from copier import Copier
from notifier import send_telegram


def main():
    parser = argparse.ArgumentParser(description="Polymarket CopyTrading Bot")
    parser.add_argument("--live", action="store_true", help="Enable live trading (real orders)")
    parser.add_argument("--target", type=str, default="", help="Target wallet address to copy")
    parser.add_argument("--max-bet", type=float, default=0, help="Max USD per trade")
    parser.add_argument("--ratio", type=float, default=0, help="Copy ratio (0.1 = 10%% of target)")
    parser.add_argument("--interval", type=int, default=0, help="Poll interval in seconds")
    parser.add_argument("--verbose", action="store_true", help="Show all poll activity")
    args = parser.parse_args()

    # Build target list
    if args.target:
        targets = [{"address": args.target.lower(), "name": args.target[:10] + "..."}]
    else:
        targets = config.TARGET_WALLETS

    if not targets:
        print("  ⛔ No target wallets configured!")
        return

    interval = args.interval or config.POLL_INTERVAL
    dry_run = not args.live

    # Banner
    mode = "LIVE" if args.live else "DRY RUN"
    print("=" * 64)
    print(f"  🔄 Polymarket CopyTrading Bot — {mode}")
    print(f"  Targets: {len(targets)} wallets")
    for t in targets:
        print(f"    • {t['name']} ({t['address'][:10]}...)")
    print(f"  Ratio  : {args.ratio or config.COPY_RATIO:.0%}")
    print(f"  Max bet: ${args.max_bet or config.MAX_BET_USD:.2f}")
    print(f"  Poll   : every {interval}s")
    print("=" * 64)

    if args.live:
        print(f"\n  ⚠️  LIVE MODE — REAL MONEY!")
        print(f"  Ctrl+C to stop. Waiting 5 seconds...\n")
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            print("⛔ Aborted.")
            return

    # Init
    client = PolymarketClient()
    watchers = []
    for t in targets:
        watchers.append(WalletWatcher(client, t["address"], t["name"]))

    copier = Copier(
        client,
        dry_run=dry_run,
        max_bet=args.max_bet or 0,
        copy_ratio=args.ratio or 0,
    )

    bal = client.get_balance()
    print(f"  Balance: ${bal:.2f}" if bal else "  Balance: n/a")

    # Graceful shutdown
    running = True

    def handle_signal(sig, frame):
        nonlocal running
        running = False
        print("\n⛔ Shutting down...")

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Startup notification
    names = ", ".join(t["name"] for t in targets)
    send_telegram(
        f"🔄 <b>CopyBot Started</b>\n"
        f"Mode: {mode}\n"
        f"Targets: {names}\n"
        f"Balance: ${bal:.2f}"
    )

    # First poll — seeds seen_ids for all watchers
    print(f"\n  Seeding trade history for {len(watchers)} wallets...")
    for w in watchers:
        w.poll()
        print(f"    ✓ {w.name}")
    print(f"  ✓ Watching for new trades\n")

    # Main loop
    total_copied = 0
    total_skipped = 0

    while running:
        try:
            for w in watchers:
                trades = w.poll()

                if trades:
                    for t in trades:
                        print(f"\n  🆕 NEW TRADE from [{w.name}]:")
                        print(f"     Market  : {t.title}")
                        print(f"     Outcome : {t.outcome}")
                        print(f"     Side    : {t.side}")
                        print(f"     Price   : {t.price:.2f} x {t.size:.1f}sh = ${t.cost_usd:.2f}")

                        result = copier.process(t)

                        if result.action in ("COPIED", "DRY_COPY"):
                            total_copied += 1
                        else:
                            total_skipped += 1

            if args.verbose:
                print(f"  [{time.strftime('%H:%M:%S')}] Polled {len(watchers)} wallets — no new trades")

            time.sleep(interval)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"  [ERR] {e}")
            time.sleep(interval)

    # Summary
    print(f"\n{'=' * 64}")
    print(f"  Session: {total_copied} copied, {total_skipped} skipped")
    print(f"{'=' * 64}")

    send_telegram(
        f"⛔ <b>CopyBot Stopped</b>\n"
        f"Copied: {total_copied}\n"
        f"Skipped: {total_skipped}"
    )


if __name__ == "__main__":
    main()
