"""
SQLite Database interface for Hua Hin Hotel Price & Busyness Monitor.
Maintains scan runs, historical crowd scores, and hotel pricing records.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

DB_PATH = Path(__file__).parent / "huahin_monitor.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Scans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checkin_date TEXT NOT NULL,
                checkout_date TEXT NOT NULL,
                nights INTEGER NOT NULL,
                macro_available INTEGER,
                macro_unavailable_pct REAL,
                macro_score REAL NOT NULL,
                bellwether_score REAL NOT NULL,
                busyness_score REAL NOT NULL,
                crowd_tag TEXT NOT NULL,
                crowd_label TEXT NOT NULL,
                avg_surge_ratio REAL NOT NULL,
                total_hotels_scanned INTEGER NOT NULL,
                sold_out_count INTEGER NOT NULL,
                notes TEXT
            )
        """)
        
        # Hotel rates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hotel_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL,
                hotel_id TEXT,
                hotel_name TEXT NOT NULL,
                tier TEXT NOT NULL,
                area TEXT,
                baseline_thb REAL NOT NULL,
                total_price_thb REAL,
                nightly_price_thb REAL,
                surge_ratio REAL NOT NULL,
                is_sold_out BOOLEAN NOT NULL,
                matched_raw_name TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans (id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_created ON scans (created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rates_scan ON hotel_rates (scan_id)")
        conn.commit()

def save_scan_result(result: Dict[str, Any]) -> int:
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scans (
                checkin_date, checkout_date, nights,
                macro_available, macro_unavailable_pct,
                macro_score, bellwether_score, busyness_score,
                crowd_tag, crowd_label, avg_surge_ratio,
                total_hotels_scanned, sold_out_count, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result["checkin_date"],
            result["checkout_date"],
            result["nights"],
            result.get("macro_available"),
            result.get("macro_unavailable_pct"),
            result["macro_score"],
            result["bellwether_score"],
            result["busyness_score"],
            result["crowd_tag"],
            result["crowd_label"],
            result["avg_surge_ratio"],
            result["total_hotels_scanned"],
            result["sold_out_count"],
            result.get("notes", "")
        ))
        
        scan_id = cursor.lastrowid
        
        # Insert hotel rates
        for hotel in result.get("hotels", []):
            cursor.execute("""
                INSERT INTO hotel_rates (
                    scan_id, hotel_id, hotel_name, tier, area,
                    baseline_thb, total_price_thb, nightly_price_thb,
                    surge_ratio, is_sold_out, matched_raw_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scan_id,
                hotel.get("id"),
                hotel["name"],
                hotel["tier"],
                hotel.get("area", ""),
                hotel["baseline_thb"],
                hotel.get("total_price_thb"),
                hotel.get("nightly_price_thb"),
                hotel["surge_ratio"],
                1 if hotel.get("is_sold_out") else 0,
                hotel.get("matched_raw_name")
            ))
            
        conn.commit()
        return scan_id

def get_latest_scan() -> Optional[Dict[str, Any]]:
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans ORDER BY id DESC LIMIT 1")
        scan_row = cursor.fetchone()
        if not scan_row:
            return None
            
        scan = dict(scan_row)
        cursor.execute("SELECT * FROM hotel_rates WHERE scan_id = ? ORDER BY surge_ratio DESC", (scan["id"],))
        hotels = [dict(r) for r in cursor.fetchall()]
        scan["hotels"] = hotels
        return scan

def get_recent_scans(limit: int = 15) -> List[Dict[str, Any]]:
    init_db()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans ORDER BY id DESC LIMIT ?", (limit,))
        scans = [dict(r) for r in cursor.fetchall()]
        return scans

# Initialize DB on load
init_db()
