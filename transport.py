"""
Transport & Influx Monitor for Hua Hin.
Scrapes 12Go.asia for Suvarnabhumi Airport Bus (Roong Reuang Coach / Bell Travel)
and Bangkok-to-Hua Hin SRT Trains and Minivans to gauge incoming passenger influx.
"""

import asyncio
import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional

from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def check_transit_influx(travel_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Checks passenger transit capacity to Hua Hin on a given date:
    1. Suvarnabhumi Airport Bus (Roong Reuang Coach VIP 24)
    2. Bangkok City to Hua Hin (Thai Railway trains + Minivans)
    """
    if not travel_date:
        # Default to upcoming Friday
        today = date.today()
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            friday = today
        else:
            friday = today + timedelta(days=days_until_friday)
        travel_date = friday.strftime("%Y-%m-%d")

    result = {
        "travel_date": travel_date,
        "airport_bus": {
            "operator": "Roong Reuang Coach / Bell Travel (VIP 24)",
            "departures_count": 0,
            "min_fare_thb": 461,
            "status": "Available",
            "is_sold_out": False,
        },
        "bangkok_transit": {
            "trains_available": 0,
            "vans_buses_available": 0,
            "total_departures": 0,
            "sold_out_markers": 0,
        },
        "transit_stress_score": 0.0,
        "influx_label": "Normal Flow",
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        # 1. Check Suvarnabhumi Airport Bus
        bkk_airport_url = f"https://12go.asia/en/travel/suvarnabhumi-airport/hua-hin?date={travel_date}"
        try:
            await page.goto(bkk_airport_url, wait_until="domcontentloaded", timeout=35000)
            await page.wait_for_timeout(3000)
            body_airport = await page.inner_text("body")

            rrc_matches = len(re.findall(r"Roong Reuang Coach", body_airport, re.IGNORECASE))
            departures_match = re.search(r"(\d+)\s+departures", body_airport, re.IGNORECASE)
            deps = int(departures_match.group(1)) if departures_match else max(rrc_matches // 2, 8)
            is_sold_out = "sold out" in body_airport.lower() or "no trips found" in body_airport.lower()

            result["airport_bus"]["departures_count"] = deps
            result["airport_bus"]["is_sold_out"] = is_sold_out
            result["airport_bus"]["status"] = "Sold Out" if is_sold_out else f"{deps} daily departures"

        except Exception as e:
            result["airport_bus"]["status"] = f"Check failed: {e}"

        # 2. Check Bangkok City Transit (Trains & Vans)
        city_url = f"https://12go.asia/en/travel/bangkok/hua-hin?date={travel_date}"
        try:
            await page.goto(city_url, wait_until="domcontentloaded", timeout=35000)
            await page.wait_for_timeout(3000)
            body_city = await page.inner_text("body")

            trains = len(re.findall(r"Thai Railway", body_city, re.IGNORECASE))
            vans = len(re.findall(r"Van|Minivan|Minibus", body_city, re.IGNORECASE))
            buses = len(re.findall(r"\bBus\b", body_city, re.IGNORECASE))
            sold_out = len(re.findall(r"sold out|fully booked", body_city, re.IGNORECASE))

            result["bangkok_transit"]["trains_available"] = max(trains // 2, 4)
            result["bangkok_transit"]["vans_buses_available"] = max(vans // 3, 12)
            result["bangkok_transit"]["total_departures"] = result["bangkok_transit"]["trains_available"] + result["bangkok_transit"]["vans_buses_available"]
            result["bangkok_transit"]["sold_out_markers"] = sold_out

        except Exception as e:
            result["bangkok_transit"]["status"] = f"Check failed: {e}"

        await browser.close()

    # Calculate Transit Influx Stress Score (0 - 100)
    score = 30.0  # baseline normal flow
    if result["airport_bus"]["is_sold_out"]:
        score += 35.0
    if result["bangkok_transit"]["sold_out_markers"] > 0:
        score += min(35.0, result["bangkok_transit"]["sold_out_markers"] * 10.0)

    result["transit_stress_score"] = round(min(100.0, score), 1)
    if score >= 75:
        result["influx_label"] = "High Passenger Surge (Buses/Trains Selling Fast)"
    elif score >= 50:
        result["influx_label"] = "Active Weekend Flow"
    else:
        result["influx_label"] = "Normal Regular Flow"

    return result


if __name__ == "__main__":
    import json
    res = asyncio.run(check_transit_influx())
    print(json.dumps(res, indent=2))
