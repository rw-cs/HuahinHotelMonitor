"""
Core Monitor for Hua Hin Hotel Prices & Crowd Busyness Index.
Scrapes market inventory and bellwether hotels, then computes a unified 0-100 Busyness Score.
"""

import asyncio
import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

from config import (
    BENCHMARK_HOTELS,
    MAX_BASELINE_INVENTORY,
    WEIGHT_MACRO_SCARCITY,
    WEIGHT_BELLWETHER_SURGE,
    get_crowd_level,
)
from db import save_scan_result


def get_default_dates(target_mode: str = "weekend") -> Tuple[str, str, int]:
    """
    Computes default target dates:
    - 'weekend': Next Friday to Sunday (2 nights)
    - 'tonight': Tonight to tomorrow (1 night)
    - 'next_weekend': The weekend after next (2 nights)
    - 'midweek': Next Tuesday to Thursday (2 nights, filters out domestic weekend traffic)
    - 'week' / 'snowbird': 7 nights starting next Tuesday (long-stay international vacationers)
    """
    today = date.today()
    
    if target_mode == "tonight":
        checkin = today
        checkout = today + timedelta(days=1)
        return checkin.strftime("%Y-%m-%d"), checkout.strftime("%Y-%m-%d"), 1

    if target_mode in ["midweek", "week", "snowbird"]:
        # Find next Tuesday (weekday 1: Mon=0, Tue=1)
        days_until_tue = (1 - today.weekday()) % 7
        if days_until_tue == 0:
            tuesday = today + timedelta(days=7)
        else:
            tuesday = today + timedelta(days=days_until_tue)

        if target_mode in ["week", "snowbird"]:
            checkout = tuesday + timedelta(days=7)
            return tuesday.strftime("%Y-%m-%d"), checkout.strftime("%Y-%m-%d"), 7
        else:
            checkout = tuesday + timedelta(days=2) # Tuesday to Thursday
            return tuesday.strftime("%Y-%m-%d"), checkout.strftime("%Y-%m-%d"), 2

    # Find next Friday (weekday 4 in Python: Mon=0, Sun=6)
    days_until_friday = (4 - today.weekday()) % 7
    if days_until_friday == 0 and target_mode == "weekend":
        friday = today
    elif days_until_friday == 0:
        friday = today + timedelta(days=7)
    else:
        friday = today + timedelta(days=days_until_friday)

    if target_mode == "next_weekend":
        friday = friday + timedelta(days=7)

    sunday = friday + timedelta(days=2)
    return friday.strftime("%Y-%m-%d"), sunday.strftime("%Y-%m-%d"), 2


def match_hotel(raw_title: str) -> Optional[Dict[str, Any]]:
    """Matches a scraped hotel title to one of our defined benchmark hotels."""
    lower_title = raw_title.lower()
    for benchmark in BENCHMARK_HOTELS:
        if benchmark["name"].lower() in lower_title:
            return benchmark
        for alias in benchmark.get("aliases", []):
            if alias.lower() in lower_title:
                return benchmark
    return None


async def scrape_hua_hin(
    checkin: str,
    checkout: str,
    pages_to_scrape: int = 3,
    headless: bool = True
) -> Dict[str, Any]:
    """
    Scrapes Booking.com Hua Hin search results for the given date range.
    Returns macro availability numbers and list of scraped property cards.
    """
    scraped_properties = []
    total_available_properties = None
    unavailable_pct_banner = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="en-US",
            viewport={"width": 1280, "height": 900}
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        for page_idx in range(pages_to_scrape):
            offset = page_idx * 25
            url = (
                f"https://www.booking.com/searchresults.html?ss=Hua+Hin"
                f"&checkin={checkin}&checkout={checkout}"
                f"&group_adults=2&no_rooms=1&group_children=0"
                f"&selected_currency=THB"
            )
            if offset > 0:
                url += f"&offset={offset}"

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(3000)

                # Scroll down to trigger lazy loading
                for _ in range(3):
                    await page.mouse.wheel(0, 2500)
                    await page.wait_for_timeout(800)

                # Extract Macro metrics on page 1
                if page_idx == 0:
                    body_text = await page.inner_text("body")
                    
                    # 1. Total available properties count
                    prop_match = re.search(r"Hua Hin:\s*([\d,]+)\s*properties found", body_text, re.IGNORECASE)
                    if prop_match:
                        total_available_properties = int(prop_match.group(1).replace(",", ""))

                    # 2. Percentage unavailable banner
                    pct_match = re.search(r"(\d+)%\s+of\s+places\s+to\s+stay\s+are\s+unavailable", body_text, re.IGNORECASE)
                    if pct_match:
                        unavailable_pct_banner = float(pct_match.group(1))

                # Extract property cards
                cards = await page.query_selector_all('[data-testid="property-card"]')
                for card in cards:
                    card_text = await card.inner_text()
                    title_el = await card.query_selector('[data-testid="title"]')
                    if not title_el:
                        continue

                    title = (await title_el.inner_text()).strip()
                    is_sold_out = "unavailable on our site" in card_text.lower()

                    nightly_price = None
                    total_price = None

                    # Check for explicit "Per night" pattern in card text
                    per_night_match = re.search(r"Per night\s*\n?\s*THB\s*([\d,]+)", card_text, re.IGNORECASE)
                    total_match = re.search(r"Total\s*\n?\s*THB\s*([\d,]+)", card_text, re.IGNORECASE)

                    if per_night_match:
                        nightly_price = float(per_night_match.group(1).replace(",", ""))
                    
                    if total_match:
                        total_price = float(total_match.group(1).replace(",", ""))

                    # Fallback to price-and-discounted-price testid
                    if nightly_price is None and total_price is None:
                        price_el = await card.query_selector('[data-testid="price-and-discounted-price"]')
                        if price_el:
                            p_text = await price_el.inner_text()
                            digits = re.sub(r"[^\d]", "", p_text)
                            if digits:
                                raw_val = float(digits)
                                # If card text mentions "per night" anywhere near price
                                if "per night" in card_text.lower():
                                    nightly_price = raw_val
                                else:
                                    total_price = raw_val

                    scraped_properties.append({
                        "raw_name": title,
                        "is_sold_out": is_sold_out,
                        "nightly_price_thb": nightly_price,
                        "total_price_thb": total_price,
                    })

            except Exception as e:
                print(f"[Scraper Warning] Page {page_idx + 1} encountered: {e}")
                break

        await browser.close()

    return {
        "macro_available": total_available_properties,
        "macro_unavailable_pct": unavailable_pct_banner,
        "properties": scraped_properties,
    }


def compute_busyness(
    checkin: str,
    checkout: str,
    nights: int,
    macro_available: Optional[int],
    macro_unavailable_pct: Optional[float],
    scraped_properties: List[Dict[str, Any]],
    target_mode: str = "weekend"
) -> Dict[str, Any]:
    """
    Computes the unified Busyness Score (0-100) based on macro capacity and
    the price surge / availability of benchmark hotels.
    """
    # 1. Compute Macro Scarcity Score (0-100)
    if macro_unavailable_pct is not None:
        macro_score = macro_unavailable_pct
    elif macro_available is not None:
        # Scale against off-peak baseline (850 total inventory)
        available_clamped = max(150, min(MAX_BASELINE_INVENTORY, macro_available))
        macro_score = (1.0 - (available_clamped - 150) / (MAX_BASELINE_INVENTORY - 150)) * 100
    else:
        macro_score = 50.0  # fallback neutral

    # 2. Match benchmark hotels
    matched_hotels = {}
    for prop in scraped_properties:
        benchmark = match_hotel(prop["raw_name"])
        if benchmark and benchmark["id"] not in matched_hotels:
            matched_hotels[benchmark["id"]] = {
                "benchmark": benchmark,
                "raw_name": prop["raw_name"],
                "is_sold_out": prop["is_sold_out"],
                "nightly_price_thb": prop.get("nightly_price_thb"),
                "total_price_thb": prop.get("total_price_thb"),
            }

    hotel_records = []
    surge_ratios = []
    sold_out_count = 0

    for bench in BENCHMARK_HOTELS:
        b_id = bench["id"]
        if b_id in matched_hotels:
            item = matched_hotels[b_id]
            is_sold_out = item["is_sold_out"]
            nightly_price = item["nightly_price_thb"]
            total_price = item["total_price_thb"]

            # If nightly price is missing but total is known:
            if nightly_price is None and total_price is not None:
                nightly_price = round(total_price / nights, 1)
            elif nightly_price is not None and total_price is None:
                total_price = round(nightly_price * nights, 1)

            if is_sold_out or (nightly_price is None and total_price is None):
                is_sold_out = True
                nightly_price = None
                surge_ratio = 2.4  # Sold out corresponds to high surge ceiling
                sold_out_count += 1
            else:
                surge_ratio = round(nightly_price / bench["baseline_thb"], 2)

            surge_ratios.append(surge_ratio)
            hotel_records.append({
                "id": b_id,
                "name": bench["name"],
                "tier": bench["tier"],
                "area": bench["area"],
                "baseline_thb": bench["baseline_thb"],
                "total_price_thb": total_price,
                "nightly_price_thb": nightly_price,
                "surge_ratio": surge_ratio,
                "is_sold_out": is_sold_out,
                "matched_raw_name": item["raw_name"],
            })
        else:
            # If not in top scraped results, we don't penalize, but record as unobserved
            pass

    # 3. Compute Bellwether Surge Score (0-100)
    if surge_ratios:
        avg_surge = sum(surge_ratios) / len(surge_ratios)
        # Convert surge ratio (e.g. 0.8x - 2.5x) to 0-100 scale
        if avg_surge <= 1.0:
            bellwether_score = max(5.0, avg_surge * 30.0)
        elif avg_surge <= 1.5:
            bellwether_score = 30.0 + (avg_surge - 1.0) * 60.0
        elif avg_surge <= 2.0:
            bellwether_score = 60.0 + (avg_surge - 1.5) * 45.0
        else:
            bellwether_score = min(100.0, 82.5 + (avg_surge - 2.0) * 35.0)

        # Bonus factor if large portion is sold out
        sold_out_ratio = sold_out_count / len(surge_ratios)
        if sold_out_ratio > 0.3:
            bellwether_score = min(100.0, bellwether_score + (sold_out_ratio * 15.0))
    else:
        avg_surge = 1.0
        bellwether_score = macro_score

    # 4. Compute Unified Busyness Score
    busyness_score = (macro_score * WEIGHT_MACRO_SCARCITY) + (bellwether_score * WEIGHT_BELLWETHER_SURGE)
    busyness_score = round(max(0.0, min(100.0, busyness_score)), 1)

    crowd_info = get_crowd_level(busyness_score)
    is_intl = target_mode in ["midweek", "week", "snowbird"]

    # Specialized international description if midweek/week
    desc = crowd_info["description"]
    if is_intl:
        diff_pct = int((avg_surge - 1.0) * 100)
        sign = "+" if diff_pct > 0 else ""
        if avg_surge >= 1.25:
            desc = f"🌍 High International Tourist Density! Midweek rates holding strong at {sign}{diff_pct}% above baseline, reflecting heavy European snowbird and long-stay occupancy."
        elif avg_surge >= 1.0:
            desc = f"🌍 Steady International Influx. Midweek floor is stable ({sign}{diff_pct}% vs baseline), unaffected by Bangkok weekend traffic."
        else:
            desc = f"🌍 Light International Influx. Midweek room rates are discounted ({diff_pct}%), indicating lower foreign vacationer density."

    return {
        "checkin_date": checkin,
        "checkout_date": checkout,
        "nights": nights,
        "target_mode": target_mode,
        "is_international_focus": is_intl,
        "macro_available": macro_available,
        "macro_unavailable_pct": macro_unavailable_pct,
        "macro_score": round(macro_score, 1),
        "bellwether_score": round(bellwether_score, 1),
        "busyness_score": busyness_score,
        "crowd_tag": crowd_info["tag"],
        "crowd_label": crowd_info["label"],
        "crowd_emoji": crowd_info["emoji"],
        "crowd_color": crowd_info["color"],
        "crowd_desc": desc,
        "avg_surge_ratio": round(avg_surge, 2),
        "total_hotels_scanned": len(scraped_properties),
        "benchmark_hotels_matched": len(hotel_records),
        "sold_out_count": sold_out_count,
        "hotels": sorted(hotel_records, key=lambda x: (x["tier"], -x["surge_ratio"])),
    }


async def run_monitor(
    target_mode: str = "weekend",
    checkin: Optional[str] = None,
    checkout: Optional[str] = None,
    save_to_db: bool = True
) -> Dict[str, Any]:
    """
    Executes a complete monitoring pass for Hua Hin:
    - Scrapes live hotel data
    - Computes busyness index
    - Saves to SQLite
    - Returns structured result
    """
    if checkin and checkout:
        d_in = datetime.strptime(checkin, "%Y-%m-%d").date()
        d_out = datetime.strptime(checkout, "%Y-%m-%d").date()
        nights = max(1, (d_out - d_in).days)
    else:
        checkin, checkout, nights = get_default_dates(target_mode)

    raw_data = await scrape_hua_hin(checkin, checkout, pages_to_scrape=3)
    result = compute_busyness(
        checkin=checkin,
        checkout=checkout,
        nights=nights,
        macro_available=raw_data["macro_available"],
        macro_unavailable_pct=raw_data["macro_unavailable_pct"],
        scraped_properties=raw_data["properties"],
        target_mode=target_mode,
    )

    if save_to_db:
        scan_id = save_scan_result(result)
        result["scan_id"] = scan_id

    return result


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "weekend"
    print(f"Running monitor for mode='{mode}'...")
    res = asyncio.run(run_monitor(target_mode=mode))
    print(f"Result: {res['crowd_emoji']} {res['crowd_label']} - Score: {res['busyness_score']}% (Surge: {res['avg_surge_ratio']}x)")
