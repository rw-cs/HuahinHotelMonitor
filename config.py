"""
Configuration for Hua Hin Hotel Price & Busyness Monitor.
Defines benchmark hotels, baseline prices, scoring thresholds, and scraper settings.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional

# Expected maximum available hotel properties in Hua Hin during off-peak low season
MAX_BASELINE_INVENTORY = 850

# Benchmark "Bellwether" Hotels representing the Hua Hin market spectrum
BENCHMARK_HOTELS = [
    # --- LUXURY / BEACHFRONT RESORTS ---
    {
        "id": "standard",
        "name": "The Standard, Hua Hin",
        "aliases": ["The Standard", "Standard, Hua Hin"],
        "tier": "Luxury",
        "baseline_thb": 4800,  # Typical weekday off-peak rate
        "area": "Central Beachfront",
    },
    {
        "id": "marriott",
        "name": "Hua Hin Marriott Resort & Spa",
        "aliases": ["Hua Hin Marriott", "Marriott Resort and Spa"],
        "tier": "Luxury",
        "baseline_thb": 5000,
        "area": "Central Beachfront",
    },
    {
        "id": "centara_grand",
        "name": "Centara Grand Beach Resort & Villas Hua Hin",
        "aliases": ["Centara Grand", "Centara Grand Beach Resort"],
        "tier": "Luxury",
        "baseline_thb": 4500,
        "area": "Downtown Beachfront",
    },
    {
        "id": "intercon",
        "name": "InterContinental Hua Hin Resort",
        "aliases": ["InterContinental Hua Hin", "InterContinental"],
        "tier": "Luxury",
        "baseline_thb": 5500,
        "area": "Bluport Beachfront",
    },
    {
        "id": "hilton",
        "name": "Hilton Hua Hin Resort & Spa",
        "aliases": ["Hilton Hua Hin"],
        "tier": "Luxury",
        "baseline_thb": 4200,
        "area": "Downtown Beachfront",
    },
    {
        "id": "movenpick",
        "name": "Mövenpick Asara Resort & Spa Hua Hin",
        "aliases": ["Mövenpick", "Movenpick Asara"],
        "tier": "Luxury",
        "baseline_thb": 4500,
        "area": "North Hua Hin",
    },
    {
        "id": "anantara",
        "name": "Anantara Hua Hin Resort",
        "aliases": ["Anantara Hua Hin", "Anantara Resort"],
        "tier": "Luxury",
        "baseline_thb": 4500,
        "area": "North Beachfront",
    },
    {
        "id": "hyatt_regency",
        "name": "Hyatt Regency Hua Hin",
        "aliases": ["Hyatt Regency", "Hyatt Regency Hua Hin"],
        "tier": "Luxury",
        "baseline_thb": 5200,
        "area": "Khao Takiab Beachfront",
    },
    {
        "id": "avani",
        "name": "Avani+ Hua Hin Resort",
        "aliases": ["Avani+", "Avani+ Hua Hin", "Avani Hua Hin"],
        "tier": "Luxury",
        "baseline_thb": 3800,
        "area": "North Hua Hin",
    },
    {
        "id": "dusit_thani",
        "name": "Dusit Thani Hua Hin",
        "aliases": ["Dusit Thani Hua Hin", "Dusit Thani"],
        "tier": "Luxury",
        "baseline_thb": 3600,
        "area": "North / Cha-Am Border",
    },
    {
        "id": "putahracsa",
        "name": "Putahracsa Hua Hin",
        "aliases": ["Putahracsa", "Putahracsa Resort"],
        "tier": "Luxury",
        "baseline_thb": 4200,
        "area": "Central Beachfront",
    },
    {
        "id": "lets_sea",
        "name": "Let's Sea Hua Hin Al Fresco Resort",
        "aliases": ["Let's Sea", "Lets Sea Hua Hin"],
        "tier": "Luxury",
        "baseline_thb": 4800,
        "area": "Khao Takiab Beachfront",
    },
    {
        "id": "veranda",
        "name": "Veranda Resort & Villas Hua Hin Cha Am",
        "aliases": ["Veranda Resort", "Veranda Hua Hin"],
        "tier": "Luxury",
        "baseline_thb": 3600,
        "area": "Cha-Am Beachfront",
    },

    # --- MIDSCALE / BOUTIQUE / FAMILY ---
    {
        "id": "amari",
        "name": "Amari Hua Hin",
        "aliases": ["Amari Hua Hin", "Amari"],
        "tier": "Midscale",
        "baseline_thb": 2300,
        "area": "Khao Takiab",
    },
    {
        "id": "holiday_inn",
        "name": "Holiday Inn Resort Vana Nava Hua Hin",
        "aliases": ["Holiday Inn Resort Vana Nava", "Holiday Inn Vana Nava"],
        "tier": "Midscale",
        "baseline_thb": 3200,
        "area": "Vana Nava / South",
    },
    {
        "id": "peri",
        "name": "The Peri Hotel Hua Hin",
        "aliases": ["The Peri Hotel", "Peri Hotel Hua Hin"],
        "tier": "Midscale",
        "baseline_thb": 2100,
        "area": "Khao Takiab",
    },
    {
        "id": "g_huahin",
        "name": "G Hua Hin Resort & Mall",
        "aliases": ["G Hua Hin Resort"],
        "tier": "Midscale",
        "baseline_thb": 2000,
        "area": "Market Village area",
    },
    {
        "id": "nh",
        "name": "NH Hua Hin",
        "aliases": ["NH Hua Hin"],
        "tier": "Midscale",
        "baseline_thb": 2000,
        "area": "Central",
    },
    {
        "id": "best_western",
        "name": "Best Western Plus Carapace Hotel Hua Hin",
        "aliases": ["Best Western Plus Carapace", "Carapace Hotel"],
        "tier": "Midscale",
        "baseline_thb": 2200,
        "area": "Khao Tao",
    },
    {
        "id": "rest_detail",
        "name": "Rest Detail Hotel Hua Hin",
        "aliases": ["Rest Detail Hotel", "Rest Detail"],
        "tier": "Midscale",
        "baseline_thb": 2800,
        "area": "Soi 19 Beachfront",
    },
    {
        "id": "verso",
        "name": "Verso Hua Hin - a Veranda Collection",
        "aliases": ["Verso Hua Hin", "Verso"],
        "tier": "Midscale",
        "baseline_thb": 3200,
        "area": "Khao Takiab",
    },
    {
        "id": "maven",
        "name": "Maven Stylish Hotel Hua Hin",
        "aliases": ["Maven Stylish Hotel", "Maven Stylish"],
        "tier": "Midscale",
        "baseline_thb": 1800,
        "area": "Central",
    },
    {
        "id": "royal_pavilion",
        "name": "Royal Pavilion Hua Hin",
        "aliases": ["Royal Pavilion", "Royal Pavilion Hotel"],
        "tier": "Midscale",
        "baseline_thb": 1400,
        "area": "Night Market / Central",
    },
    {
        "id": "wora_bura",
        "name": "Wora Bura Hua Hin Resort & Spa",
        "aliases": ["Wora Bura Hua Hin", "Wora Bura"],
        "tier": "Midscale",
        "baseline_thb": 3000,
        "area": "Khao Takiab",
    },
    {
        "id": "marrakesh",
        "name": "Marrakesh Hua Hin Resort & Spa",
        "aliases": ["Marrakesh Hua Hin", "Marrakesh"],
        "tier": "Midscale",
        "baseline_thb": 3400,
        "area": "Central Beachfront",
    },

    # --- BUDGET & VALUE BENCHMARKS (< 1,200 THB) ---
    {
        "id": "hop_inn",
        "name": "Hop Inn Hua Hin",
        "aliases": ["Hop Inn Hua Hin", "Hop Inn"],
        "tier": "Budget",
        "baseline_thb": 700,
        "area": "Phetkasem Rd / North",
    },
    {
        "id": "b2_huahin",
        "name": "B2 Hua Hin Premier Hotel",
        "aliases": ["B2 Hua Hin", "B2 Premier"],
        "tier": "Budget",
        "baseline_thb": 650,
        "area": "Soi 94",
    },
    {
        "id": "my_way",
        "name": "My Way Hua Hin Music Hotel",
        "aliases": ["My Way Hua Hin", "My Way Hotel"],
        "tier": "Budget",
        "baseline_thb": 750,
        "area": "Soi 108 / South",
    },
    {
        "id": "fulay",
        "name": "Fulay Guesthouse",
        "aliases": ["Fulay Guesthouse", "Fulay"],
        "tier": "Budget",
        "baseline_thb": 600,
        "area": "Naresdamri Pier",
    },
    {
        "id": "baan_nilrath",
        "name": "Baan Nilrath Hotel",
        "aliases": ["Baan Nilrath", "Nilrath Hotel"],
        "tier": "Budget",
        "baseline_thb": 750,
        "area": "Downtown Soi 67",
    },
    {
        "id": "mandarin_lodge",
        "name": "Mandarin Lodge by Victor",
        "aliases": ["MANDARIN LODGE", "Mandarin Lodge"],
        "tier": "Budget",
        "baseline_thb": 600,
        "area": "Downtown / Station",
    },
    {
        "id": "sea_residence",
        "name": "Sea Residence Hua Hin 45",
        "aliases": ["Sea Residence Hua Hin 45", "Sea Residence"],
        "tier": "Budget",
        "baseline_thb": 550,
        "area": "Soi 45 / Beachside",
    },
    {
        "id": "home_hill",
        "name": "Hua Hin Home Hill",
        "aliases": ["Hua Hin Home Hill", "Home Hill"],
        "tier": "Budget",
        "baseline_thb": 500,
        "area": "Inland / Hin Lek Fai",
    },
    {
        "id": "mad_monkey",
        "name": "Mad Monkey Hostel Hua Hin",
        "aliases": ["Mad Monkey", "Mad Monkey Hua Hin"],
        "tier": "Budget",
        "baseline_thb": 450,
        "area": "Khao Takiab",
    },
    {
        "id": "hub_57",
        "name": "Hub Hua Hin 57 Hostel",
        "aliases": ["Hub Hua Hin", "Hub Hua Hin 57"],
        "tier": "Budget",
        "baseline_thb": 450,
        "area": "Night Market",
    },
    {
        "id": "terminal",
        "name": "Huahin Terminal",
        "aliases": ["Huahin Terminal", "Terminal Hotel"],
        "tier": "Budget",
        "baseline_thb": 750,
        "area": "Canal Road",
    },
    {
        "id": "chaba_chalet",
        "name": "Chaba Chalet Hotel",
        "aliases": ["Chaba Chalet", "Chaba Chalet Hotel"],
        "tier": "Budget",
        "baseline_thb": 700,
        "area": "Railway Station",
    },
    {
        "id": "thipurai",
        "name": "Thipurai City Hotel",
        "aliases": ["Thipurai City", "Thipurai"],
        "tier": "Budget",
        "baseline_thb": 850,
        "area": "Downtown",
    },
    {
        "id": "baan_manthana",
        "name": "Baan Manthana Hotel",
        "aliases": ["Baan Manthana", "Manthana Hotel"],
        "tier": "Budget",
        "baseline_thb": 850,
        "area": "Night Market",
    },
    {
        "id": "la_maison",
        "name": "La Maison Hua Hin",
        "aliases": ["La Maison Hua Hin", "La Maison"],
        "tier": "Budget",
        "baseline_thb": 1100,
        "area": "Downtown",
    },
    {
        "id": "city_beach",
        "name": "City Beach Resort",
        "aliases": ["City Beach Resort"],
        "tier": "Budget",
        "baseline_thb": 1100,
        "area": "Downtown",
    },
    {
        "id": "ibis",
        "name": "ibis Hua Hin",
        "aliases": ["ibis Hua Hin", "Ibis"],
        "tier": "Budget",
        "baseline_thb": 1100,
        "area": "Khao Takiab",
    },
    {
        "id": "kiang_haad",
        "name": "Kiang Haad Beach Hua Hin",
        "aliases": ["Kiang Haad", "Kiang Haad Beach"],
        "tier": "Budget",
        "baseline_thb": 1200,
        "area": "Market Village",
    },
]

# Weights for unified Crowd Meter Score calculation
WEIGHT_MACRO_SCARCITY = 0.40      # Weight for city-wide availability
WEIGHT_BELLWETHER_SURGE = 0.60    # Weight for basket price surge & sellouts

# Crowd Level Thresholds and Descriptions
CROWD_LEVELS = [
    {
        "min_score": 0,
        "max_score": 30,
        "label": "Chill / Very Quiet",
        "tag": "chill",
        "emoji": "🟢",
        "color": "#10b981", # Emerald
        "description": "Ghost town vibes! Empty beaches, immediate seating at all restaurants, smooth traffic, excellent room deals.",
    },
    {
        "min_score": 31,
        "max_score": 55,
        "label": "Moderate / Relaxed",
        "tag": "moderate",
        "emoji": "🟡",
        "color": "#eab308", # Yellow
        "description": "Pleasant, relaxed weekday atmosphere. Easy dining, gentle beach foot-traffic, light resort occupancy.",
    },
    {
        "min_score": 56,
        "max_score": 75,
        "label": "Busy / High Energy",
        "tag": "busy",
        "emoji": "🟠",
        "color": "#f97316", # Orange
        "description": "Classic weekend rush! Cicada and Tamarind markets buzzing, full resort pools, active nightlife and beach clubs.",
    },
    {
        "min_score": 76,
        "max_score": 90,
        "label": "Very Busy / Crowded",
        "tag": "very_busy",
        "emoji": "🔴",
        "color": "#ef4444", # Red
        "description": "High tourist influx. Popular seafood spots packed, Rama II traffic heavy, top resorts mostly booked up.",
    },
    {
        "min_score": 91,
        "max_score": 100,
        "label": "Peak / Packed Out",
        "tag": "peak",
        "emoji": "🚨",
        "color": "#9333ea", # Purple / Alert
        "description": "Peak holiday gridlock (Songkran / NYE / long weekend). Hotels virtually sold out, surging rates, packed town.",
    },
]

def get_crowd_level(score: float) -> dict:
    for level in CROWD_LEVELS:
        if level["min_score"] <= score <= level["max_score"]:
            return level
    return CROWD_LEVELS[-1]
