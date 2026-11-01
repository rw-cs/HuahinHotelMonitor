"""
Scheduler & Automated Alert Runner for Hua Hin Hotel Busyness Monitor.
Runs periodic scans and optionally sends webhook alerts (Discord / Telegram)
when busyness spikes or drops.
"""

import os
import time
import asyncio
import httpx
from datetime import datetime

from monitor import run_monitor
from db import get_latest_scan

# Webhook URLs (optional, set via environment variable)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Score threshold for "High Crowd" alert
ALERT_THRESHOLD = float(os.getenv("ALERT_THRESHOLD", "70.0"))


async def send_discord_alert(scan: dict):
    if not DISCORD_WEBHOOK_URL:
        return

    score = scan["busyness_score"]
    label = scan["crowd_label"]
    emoji = scan.get("crowd_emoji", "🏖️")
    dates = f"{scan['checkin_date']} → {scan['checkout_date']}"

    payload = {
        "embeds": [{
            "title": f"{emoji} Hua Hin Busyness Alert: {score:.1f}% [{label}]",
            "description": f"Demand for **{dates}** is currently at **{score:.1f}/100**.\n"
                           f"Average hotel surge is **{scan['avg_surge_ratio']:.2f}x** baseline.",
            "color": 0xf97316 if score > 50 else 0x10b981,
            "fields": [
                {"name": "Macro Inventory", "value": f"{scan.get('macro_available', 'N/A')} properties available", "inline": True},
                {"name": "Sold Out Benchmark Ratio", "value": f"{scan['sold_out_count']}/{scan['benchmark_hotels_matched']}", "inline": True},
            ],
            "footer": {"text": "Hua Hin Hotel Pulse Monitor"}
        }]
    }

    try:
        async with httpx.AsyncClient() as client:
            await client.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10.0)
            print("[Alert] Discord webhook notification sent.")
    except Exception as e:
        print(f"[Alert Error] Failed to send Discord webhook: {e}")


async def send_telegram_alert(scan: dict):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    score = scan["busyness_score"]
    label = scan["crowd_label"]
    dates = f"{scan['checkin_date']} → {scan['checkout_date']}"

    msg = (
        f"🏖️ *Hua Hin Busyness Alert*\n"
        f"Target Dates: `{dates}`\n"
        f"Crowd Index: *{score:.1f}%* ({label})\n"
        f"Average Surge: *{scan['avg_surge_ratio']:.2f}x*\n"
        f"Sold Out Benchmarks: *{scan['sold_out_count']} properties*\n"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10.0)
            print("[Alert] Telegram notification sent.")
    except Exception as e:
        print(f"[Alert Error] Failed to send Telegram alert: {e}")


async def run_scheduled_job(interval_hours: int = 6):
    print(f"🚀 Hua Hin Busyness Scheduler started! Running every {interval_hours} hour(s)...")
    while True:
        try:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Executing scheduled monitoring scan...")
            scan = await run_monitor(target_mode="weekend", save_to_db=True)
            print(f"Scan complete: {scan['crowd_label']} - Score: {scan['busyness_score']}%")

            if scan["busyness_score"] >= ALERT_THRESHOLD:
                print(f"[Alert Trigger] Score {scan['busyness_score']}% exceeds threshold {ALERT_THRESHOLD}%!")
                await send_discord_alert(scan)
                await send_telegram_alert(scan)

        except Exception as e:
            print(f"[Scheduler Error] Scan failed: {e}")

        print(f"Sleeping for {interval_hours} hour(s)...")
        await asyncio.sleep(interval_hours * 3600)


if __name__ == "__main__":
    import sys
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    asyncio.run(run_scheduled_job(interval_hours=interval))
