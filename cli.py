"""
CLI Interface for Hua Hin Hotel Price & Busyness Monitor.
Provides rich terminal visualizations of Hua Hin crowd levels and hotel rates.
"""

import sys
import argparse
import asyncio
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from monitor import run_monitor, get_default_dates
from db import get_latest_scan, get_recent_scans

console = Console()

def render_meter_bar(score: float, width: int = 32) -> str:
    """Renders a visual gradient progress bar for the busyness score."""
    filled_len = int((score / 100.0) * width)
    empty_len = width - filled_len
    bar = "█" * filled_len + "░" * empty_len
    return bar

def display_scan(scan_data: dict):
    score = scan_data["busyness_score"]
    label = scan_data["crowd_label"]
    tag = scan_data["crowd_tag"]
    color = scan_data.get("crowd_color", "#f97316")
    emoji = scan_data.get("crowd_emoji", "🟠")
    desc = scan_data.get("crowd_desc", "")

    # Header Panel
    bar = render_meter_bar(score)
    meter_text = Text()

    is_intl = scan_data.get("is_international_focus") or scan_data.get("nights", 2) >= 7
    if is_intl:
        meter_text.append(f"\n  🌍  FOCUS: INTERNATIONAL TOURISTS & LONG-STAY SNOWBIRDS\n", style="bold yellow on dark_blue")
        meter_text.append(f"  {emoji}  MIDWEEK INTERNATIONAL INDEX: ", style="bold white")
    else:
        meter_text.append(f"\n  {emoji}  HUA HIN CROWD INDEX: ", style="bold white")

    meter_text.append(f"{score:.1f}% ", style=f"bold {color}")
    meter_text.append(f"[{label.upper()}]\n", style=f"bold {color}")
    meter_text.append(f"  [{bar}] {score:.1f}/100\n\n", style=f"{color}")
    
    meter_text.append(f"  📅 Dates Monitored: ", style="bold cyan")
    meter_text.append(f"{scan_data['checkin_date']} to {scan_data['checkout_date']} ({scan_data['nights']} nights)\n", style="white")
    
    meter_text.append(f"  📊 Macro Scarcity:  ", style="bold cyan")
    avail = scan_data.get('macro_available')
    avail_str = f"{avail} properties available" if avail else "N/A"
    meter_text.append(f"{avail_str} (Macro Index: {scan_data['macro_score']}%)\n", style="white")

    meter_text.append(f"  📈 Bellwether Surge: ", style="bold cyan")
    meter_text.append(f"{scan_data['avg_surge_ratio']:.2f}x average baseline rate (Basket Index: {scan_data['bellwether_score']}%)\n", style="white")

    if desc:
        meter_text.append(f"\n  💡 {desc}\n", style="italic bright_black")

    console.print(Panel(meter_text, title="🏖️  HUA HIN LIVE PULSE MONITOR", border_style=color, box=box.ROUNDED))

    # Hotel Breakdown Table
    hotels = scan_data.get("hotels", [])
    if hotels:
        table = Table(
            title=f"🏨 Bellwether Hotel Basket Breakdown ({len(hotels)} benchmark properties)",
            box=box.SIMPLE_HEAVY,
            header_style="bold cyan"
        )
        table.add_column("Tier", style="dim", width=10)
        table.add_column("Hotel Name", style="bold white", width=34)
        table.add_column("Area", style="dim", width=18)
        table.add_column("Baseline", justify="right", style="cyan", width=12)
        table.add_column("Current / Night", justify="right", style="bold white", width=16)
        table.add_column("Surge Factor", justify="right", width=14)
        table.add_column("Status", justify="center", width=12)

        for h in hotels:
            tier = h.get("tier", "Midscale")
            name = h.get("hotel_name") or h.get("name", "Unknown")
            area = h.get("area", "")
            base = f"฿{int(h['baseline_thb']):,}"
            
            is_sold_out = h.get("is_sold_out", False)
            if is_sold_out:
                curr = "[red]SOLD OUT[/red]"
                surge = "[red]MAX (2.4x)[/red]"
                status = "[bold red]🚫 Full[/bold red]"
            else:
                nightly = h.get("nightly_price_thb")
                curr = f"฿{int(nightly):,}" if nightly else "N/A"
                ratio = h.get("surge_ratio", 1.0)
                diff_pct = int((ratio - 1.0) * 100)
                
                if ratio > 1.5:
                    surge_color = "red"
                elif ratio > 1.15:
                    surge_color = "yellow"
                elif ratio < 0.95:
                    surge_color = "green"
                else:
                    surge_color = "white"

                sign = "+" if diff_pct > 0 else ""
                surge = f"[{surge_color}]{ratio:.2f}x ({sign}{diff_pct}%)[/{surge_color}]"
                status = "[green]✓ Open[/green]"

            table.add_row(tier, name, area, base, curr, surge, status)

        console.print(table)
        console.print("")

def display_history():
    scans = get_recent_scans(10)
    if not scans:
        console.print("[yellow]No scans recorded yet. Run 'python cli.py scan' first![/yellow]")
        return

    table = Table(title="📜 Recent Hua Hin Busyness Scans", box=box.ROUNDED, header_style="bold magenta")
    table.add_column("ID", justify="center", width=5)
    table.add_column("Scanned At", style="dim", width=20)
    table.add_column("Target Dates", style="cyan", width=24)
    table.add_column("Score", justify="right", style="bold white", width=10)
    table.add_column("Crowd Level", width=22)
    table.add_column("Surge", justify="right", width=10)
    table.add_column("Sold Out", justify="center", width=10)

    for s in scans:
        score = s["busyness_score"]
        label = s["crowd_label"]
        ratio = s["avg_surge_ratio"]
        sold = f"{s['sold_out_count']}/{s['total_hotels_scanned']}"
        table.add_row(
            str(s["id"]),
            str(s["created_at"])[:16],
            f"{s['checkin_date']} → {s['checkout_date']}",
            f"{score:.1f}%",
            label,
            f"{ratio:.2f}x",
            sold
        )

    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Hua Hin Hotel Price & Busyness Monitor CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # scan command
    scan_p = subparsers.add_parser("scan", help="Run a live scan of Hua Hin hotel demand")
    scan_p.add_argument("--target", choices=["weekend", "tonight", "next_weekend", "midweek", "snowbird", "week"], default="weekend", help="Target preset (midweek/snowbird isolate international tourists)")
    scan_p.add_argument("--checkin", type=str, help="Custom check-in date (YYYY-MM-DD)")
    scan_p.add_argument("--checkout", type=str, help="Custom check-out date (YYYY-MM-DD)")

    # latest command
    subparsers.add_parser("latest", help="Show the most recent scan report")

    # history command
    subparsers.add_parser("history", help="List recent scan history")

    # transit command
    transit_p = subparsers.add_parser("transit", help="Check Airport Bus & 12Go transit influx")
    transit_p.add_argument("--date", type=str, help="Travel date (YYYY-MM-DD)")

    # tours command
    subparsers.add_parser("tours", help="Check Western international tour bookings (GetYourGuide)")

    args = parser.parse_args()

    if args.command == "tours":
        from tours import scrape_international_tours
        console.print("[bold cyan]🎒 Scraping international tour demand from GetYourGuide...[/bold cyan]")
        t_data = asyncio.run(scrape_international_tours())

        panel_content = Text()
        panel_content.append(f"\n  🎒  TOUR DEMAND INDEX: ", style="bold white")
        panel_content.append(f"{t_data['tour_demand_score']:.1f}% ", style="bold cyan")
        panel_content.append(f"[{t_data['tour_label'].upper()}]\n", style="bold green")
        panel_content.append(f"  📊 Catalog: {t_data['total_activities_available']} international excursions active\n", style="white")
        panel_content.append(f"  🔥 High-Demand Sellout Markers: {t_data['high_demand_markers']}\n\n", style="white")

        console.print(Panel(panel_content, title="🐘 HUA HIN INTERNATIONAL EXCURSIONS PULSE", border_style="green", box=box.ROUNDED))

        table = Table(title="🧭 Top International Benchmark Tours", box=box.SIMPLE_HEAVY, header_style="bold green")
        table.add_column("Category", style="dim", width=20)
        table.add_column("Excursion Name", style="bold white", width=42)
        table.add_column("Current Fare", justify="right", style="cyan", width=14)
        table.add_column("Rating / Reviews", justify="center", width=18)
        table.add_column("Demand Status", justify="center", width=16)

        for b in t_data["benchmark_tours"]:
            fare = f"฿{b['price_thb']:,}"
            rev = f"★ {b['rating']} ({b['reviews_count']})"
            status = "[bold red]🔥 Selling Fast[/bold red]" if b["is_high_demand"] else "[green]✓ Available[/green]"
            table.add_row(b["category"], b["name"], fare, rev, status)

        console.print(table)
        console.print("")

    elif args.command == "transit":
        from transport import check_transit_influx
        t_date = getattr(args, "date", None)
        console.print(f"[bold cyan]🚌 Checking 12Go & Airport Bus influx for {t_date or 'upcoming weekend'}...[/bold cyan]")
        t_data = asyncio.run(check_transit_influx(travel_date=t_date))

        panel_content = Text()
        panel_content.append(f"\n  🚌  TRANSIT INFLUX INDEX: ", style="bold white")
        panel_content.append(f"{t_data['transit_stress_score']:.1f}% ", style="bold orange1")
        panel_content.append(f"[{t_data['influx_label'].upper()}]\n\n", style="bold cyan")

        panel_content.append(f"  ✈️  Suvarnabhumi Airport Bus (RRC VIP 24):\n", style="bold yellow")
        panel_content.append(f"     • Status: {t_data['airport_bus']['status']}\n", style="white")
        panel_content.append(f"     • Fares: From ฿{t_data['airport_bus']['min_fare_thb']} one-way\n\n", style="white")

        panel_content.append(f"  🚆  Bangkok Central Transit (Trains & Vans):\n", style="bold magenta")
        panel_content.append(f"     • Thai Railway (SRT) Departures: ~{t_data['bangkok_transit']['trains_available']} daily scheduled\n", style="white")
        panel_content.append(f"     • Minivans & Buses: ~{t_data['bangkok_transit']['vans_buses_available']} scheduled services\n", style="white")
        panel_content.append(f"     • Sold-out warnings: {t_data['bangkok_transit']['sold_out_markers']}\n", style="white")

        console.print(Panel(panel_content, title="🚍 HUA HIN ARRIVALS & TRANSIT PULSE", border_style="cyan", box=box.ROUNDED))

    elif args.command == "scan" or args.command is None:
        target = getattr(args, "target", "weekend")
        checkin = getattr(args, "checkin", None)
        checkout = getattr(args, "checkout", None)
        
        console.print(f"[bold cyan]🔍 Scanning Hua Hin hotel market (mode: {target})...[/bold cyan]")
        result = asyncio.run(run_monitor(target_mode=target, checkin=checkin, checkout=checkout))
        display_scan(result)

    elif args.command == "latest":
        scan = get_latest_scan()
        if scan:
            display_scan(scan)
        else:
            console.print("[yellow]No scans found. Run 'python cli.py scan' first![/yellow]")

    elif args.command == "history":
        display_history()

if __name__ == "__main__":
    main()
