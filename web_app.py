"""
FastAPI Web Dashboard for Hua Hin Hotel Price & Busyness Monitor.
Provides a modern visual UI with live crowd meters, hotel rate comparisons, and historical charts.
"""

import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from monitor import run_monitor, get_default_dates
from db import get_latest_scan, get_recent_scans

app = FastAPI(title="Hua Hin Hotel Price & Busyness Monitor")

class ScanRequest(BaseModel):
    target: Optional[str] = "weekend"
    checkin: Optional[str] = None
    checkout: Optional[str] = None

@app.get("/api/latest")
async def api_latest():
    scan = get_latest_scan()
    if not scan:
        return JSONResponse({"status": "no_data", "message": "No scans recorded yet."}, status_code=404)
    return scan

@app.get("/api/history")
async def api_history(limit: int = 20):
    scans = get_recent_scans(limit=limit)
    return scans

@app.get("/api/transit")
async def api_transit(date: Optional[str] = None):
    from transport import check_transit_influx
    data = await check_transit_influx(travel_date=date)
    return data

@app.get("/api/tours")
async def api_tours():
    from tours import scrape_international_tours
    data = await scrape_international_tours()
    return data

@app.post("/api/scan")
async def api_run_scan(req: ScanRequest):
    result = await run_monitor(
        target_mode=req.target or "weekend",
        checkin=req.checkin,
        checkout=req.checkout,
        save_to_db=True
    )
    return result

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTML_CONTENT

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hua Hin Live Pulse | Hotel Price & Crowd Monitor</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #0b0f19; color: #f3f4f6; }
    .glass { background: rgba(17, 24, 39, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
    .glow-orange { box-shadow: 0 0 35px -5px rgba(249, 115, 22, 0.25); }
    .glow-green { box-shadow: 0 0 35px -5px rgba(16, 185, 129, 0.25); }
    .glow-red { box-shadow: 0 0 35px -5px rgba(239, 68, 68, 0.25); }
  </style>
</head>
<body class="min-h-screen pb-16">
  <!-- Top Navigation -->
  <header class="border-b border-gray-800 bg-gray-900/60 sticky top-0 z-30 backdrop-blur-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="text-3xl">🏖️</span>
        <div>
          <h1 class="text-lg font-bold text-white flex items-center gap-2">
            Hua Hin Live Pulse
            <span class="text-xs px-2 py-0.5 rounded-full bg-orange-500/10 text-orange-400 font-semibold border border-orange-500/20">Crowd Index</span>
          </h1>
          <p class="text-xs text-gray-400">Hotel Price & Tourism Density Monitor</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <button id="scanBtn" onclick="triggerScan()" class="px-4 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold transition flex items-center gap-2 shadow-lg shadow-orange-500/20">
          <svg id="scanIcon" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
          <span id="scanText">Scan Now</span>
        </button>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 space-y-6">
    <!-- Preset Selection Bar -->
    <div class="flex flex-wrap items-center justify-between gap-4 p-4 rounded-2xl glass">
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider mr-2">Target Date:</span>
        <button onclick="setTarget('weekend')" class="date-preset px-3 py-1.5 rounded-lg text-sm font-medium bg-orange-500 text-white" data-target="weekend">This Weekend</button>
        <button onclick="setTarget('tonight')" class="date-preset px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-800 text-gray-300 hover:bg-gray-700" data-target="tonight">Tonight</button>
        <button onclick="setTarget('next_weekend')" class="date-preset px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-800 text-gray-300 hover:bg-gray-700" data-target="next_weekend">Next Weekend</button>
        <span class="text-gray-600">|</span>
        <button onclick="setTarget('midweek')" class="date-preset px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-800 text-cyan-300 hover:bg-gray-700 border border-cyan-500/20" data-target="midweek">🌍 Midweek (Int'l Focus)</button>
        <button onclick="setTarget('snowbird')" class="date-preset px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-800 text-indigo-300 hover:bg-gray-700 border border-indigo-500/20" data-target="snowbird">❄️ 7-Night (Snowbird)</button>
      </div>
      <div class="text-xs text-gray-400 flex items-center gap-2">
        <span>Last updated:</span>
        <span id="lastUpdated" class="font-mono text-gray-200">-</span>
      </div>
    </div>

    <!-- Hero Score Card & Key Stats Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Main Busyness Meter -->
      <div id="meterCard" class="glass rounded-3xl p-6 flex flex-col justify-between glow-orange relative overflow-hidden">
        <div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-gray-400">Current Crowd Index</span>
            <span id="crowdBadge" class="px-2.5 py-1 rounded-full text-xs font-bold bg-orange-500/20 text-orange-400 border border-orange-500/30">Loading...</span>
          </div>
          <div class="mt-4 flex items-baseline gap-2">
            <span id="scoreValue" class="text-6xl font-extrabold tracking-tight text-white">--</span>
            <span class="text-2xl font-bold text-gray-400">/ 100</span>
          </div>
          <div class="w-full bg-gray-800 rounded-full h-3 mt-4 overflow-hidden p-0.5">
            <div id="scoreBar" class="bg-gradient-to-r from-emerald-400 via-amber-400 to-orange-500 h-full rounded-full transition-all duration-700" style="width: 0%"></div>
          </div>
        </div>

        <div class="mt-6 pt-4 border-t border-gray-800">
          <p id="crowdDesc" class="text-sm text-gray-300 leading-relaxed italic">Analyzing Hua Hin hotel rates and occupancy...</p>
        </div>
      </div>

      <!-- Macro Availability & Surge Cards -->
      <div class="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <!-- Card 1: Available Properties -->
        <div class="glass rounded-2xl p-5 flex flex-col justify-between">
          <div class="flex items-center justify-between text-gray-400 text-xs font-semibold uppercase">
            <span>Market Availability</span>
            <span class="text-lg">🏨</span>
          </div>
          <div class="mt-3">
            <div id="macroAvailable" class="text-3xl font-extrabold text-white">--</div>
            <div class="text-xs text-gray-400 mt-1">Total properties available in Hua Hin</div>
          </div>
          <div class="mt-4 pt-3 border-t border-gray-800/80 text-xs flex justify-between">
            <span class="text-gray-400">Scarcity Index:</span>
            <span id="macroScore" class="font-bold text-gray-200">--%</span>
          </div>
        </div>

        <!-- Card 2: Price Surge Factor -->
        <div class="glass rounded-2xl p-5 flex flex-col justify-between">
          <div class="flex items-center justify-between text-gray-400 text-xs font-semibold uppercase">
            <span>Price Surge Multiplier</span>
            <span class="text-lg">📈</span>
          </div>
          <div class="mt-3">
            <div id="surgeFactor" class="text-3xl font-extrabold text-white">--x</div>
            <div class="text-xs text-gray-400 mt-1">Average vs. low-season baseline</div>
          </div>
          <div class="mt-4 pt-3 border-t border-gray-800/80 text-xs flex justify-between">
            <span class="text-gray-400">Bellwether Index:</span>
            <span id="bellwetherScore" class="font-bold text-gray-200">--%</span>
          </div>
        </div>

        <!-- Card 3: Sold Out Ratio -->
        <div class="glass rounded-2xl p-5 flex flex-col justify-between">
          <div class="flex items-center justify-between text-gray-400 text-xs font-semibold uppercase">
            <span>Sold-Out Benchmarks</span>
            <span class="text-lg">🚫</span>
          </div>
          <div class="mt-3">
            <div id="soldOutRatio" class="text-3xl font-extrabold text-white">-- / --</div>
            <div class="text-xs text-gray-400 mt-1">Key resorts with no remaining rooms</div>
          </div>
          <div class="mt-4 pt-3 border-t border-gray-800/80 text-xs flex justify-between">
            <span class="text-gray-400">Capacity Pressure:</span>
            <span id="soldOutTag" class="font-bold text-gray-200">Normal</span>
          </div>
        </div>

        <!-- Card 4: Date Scope -->
        <div class="glass rounded-2xl p-5 flex flex-col justify-between">
          <div class="flex items-center justify-between text-gray-400 text-xs font-semibold uppercase">
            <span>Monitored Window</span>
            <span class="text-lg">📅</span>
          </div>
          <div class="mt-3">
            <div id="monitoredDates" class="text-xl font-bold text-white">-- → --</div>
            <div id="monitoredNights" class="text-xs text-gray-400 mt-1">2 nights stay</div>
          </div>
          <div class="mt-4 pt-3 border-t border-gray-800/80 text-xs flex justify-between">
            <span class="text-gray-400">Location:</span>
            <span class="font-bold text-orange-400">Hua Hin & Cha-Am, TH</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Live Transit & Inflow Indicator (12Go & Airport Bus) -->
    <div class="glass rounded-3xl p-6 border-l-4 border-l-cyan-500">
      <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div>
          <h2 class="text-base font-bold text-white flex items-center gap-2">
            🚍 Transit & Passenger Influx Pulse
            <span id="transitBadge" class="text-xs px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/30">Loading...</span>
          </h2>
          <p class="text-xs text-gray-400">Incoming arrivals via Suvarnabhumi Airport Bus & Bangkok SRT trains/vans (via 12Go.asia)</p>
        </div>
        <div class="text-right">
          <div class="text-xs text-gray-400 uppercase font-semibold">Transit Stress Index</div>
          <div id="transitStressScore" class="text-2xl font-extrabold text-cyan-400">--%</div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Airport Bus Box -->
        <div class="bg-gray-900/60 p-4 rounded-2xl border border-gray-800 flex items-start gap-3">
          <div class="p-2.5 bg-orange-500/10 text-orange-400 rounded-xl text-xl">✈️</div>
          <div>
            <div class="text-xs uppercase font-bold text-gray-400">Suvarnabhumi Airport Bus</div>
            <div id="airportBusOperator" class="text-sm font-semibold text-white mt-0.5">Roong Reuang Coach (VIP 24)</div>
            <div class="text-xs text-gray-300 mt-1 flex items-center gap-3">
              <span id="airportBusStatus">13 daily departures</span>
              <span class="text-gray-500">•</span>
              <span id="airportBusFare" class="text-emerald-400 font-semibold">From ฿461</span>
            </div>
          </div>
        </div>

        <!-- Trains & Vans Box -->
        <div class="bg-gray-900/60 p-4 rounded-2xl border border-gray-800 flex items-start gap-3">
          <div class="p-2.5 bg-cyan-500/10 text-cyan-400 rounded-xl text-xl">🚆</div>
          <div>
            <div class="text-xs uppercase font-bold text-gray-400">Bangkok Trains & Minivans</div>
            <div id="trainsStatus" class="text-sm font-semibold text-white mt-0.5">Thai Railway + Mochit/Ekkamai Vans</div>
            <div class="text-xs text-gray-300 mt-1 flex items-center gap-3">
              <span id="trainsCount">~4 trains / day</span>
              <span class="text-gray-500">•</span>
              <span id="vansCount">~12 minivan services</span>
              <span class="text-gray-500">•</span>
              <span id="soldOutTransit" class="text-emerald-400">Seats available</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Live International Tours Indicator (GetYourGuide / Western Inbound OTAs) -->
    <div class="glass rounded-3xl p-6 border-l-4 border-l-emerald-500">
      <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div>
          <h2 class="text-base font-bold text-white flex items-center gap-2">
            🎒 International Tour & Activity Pulse (GetYourGuide)
            <span id="tourBadge" class="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30">Loading...</span>
          </h2>
          <p class="text-xs text-gray-400">Demand for Western day trips (WFFT Elephant Rescue, Kui Buri Safari, Phraya Nakhon Cave)</p>
        </div>
        <div class="text-right">
          <div class="text-xs text-gray-400 uppercase font-semibold">Excursion Demand Index</div>
          <div id="tourDemandScore" class="text-2xl font-extrabold text-emerald-400">--%</div>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead>
            <tr class="border-b border-gray-800 text-gray-400 text-xs uppercase font-semibold">
              <th class="py-2.5 px-3">Category</th>
              <th class="py-2.5 px-3">Top Excursions</th>
              <th class="py-2.5 px-3 text-right">Fare</th>
              <th class="py-2.5 px-3 text-center">Rating</th>
              <th class="py-2.5 px-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody id="toursTableBody" class="divide-y divide-gray-800/60 font-medium">
            <tr><td colspan="5" class="text-center py-4 text-gray-500">Loading tour data...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Bellwether Hotel Basket Table -->
    <div class="glass rounded-3xl p-6">
      <div class="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div>
          <h2 class="text-base font-bold text-white flex items-center gap-2">
            🏨 Benchmark Hotel Basket
            <span id="hotelCountBadge" class="text-xs px-2 py-0.5 rounded-full bg-gray-800 text-gray-300">0 hotels</span>
          </h2>
          <p class="text-xs text-gray-400">Real-time room rates vs off-peak baselines</p>
        </div>
        <div class="flex items-center gap-1.5 bg-gray-800/80 p-1 rounded-xl text-xs">
          <button onclick="filterTier('all')" class="tier-btn px-2.5 py-1 rounded-lg bg-orange-500 text-white font-medium" data-tier="all">All</button>
          <button onclick="filterTier('Luxury')" class="tier-btn px-2.5 py-1 rounded-lg text-gray-400 hover:text-white" data-tier="Luxury">Luxury</button>
          <button onclick="filterTier('Midscale')" class="tier-btn px-2.5 py-1 rounded-lg text-gray-400 hover:text-white" data-tier="Midscale">Midscale</button>
          <button onclick="filterTier('Budget')" class="tier-btn px-2.5 py-1 rounded-lg text-gray-400 hover:text-white" data-tier="Budget">Budget</button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead>
            <tr class="border-b border-gray-800 text-gray-400 text-xs uppercase font-semibold">
              <th class="py-3 px-3">Hotel</th>
              <th class="py-3 px-3">Tier</th>
              <th class="py-3 px-3">Area</th>
              <th class="py-3 px-3 text-right">Baseline</th>
              <th class="py-3 px-3 text-right">Current Rate / Nt</th>
              <th class="py-3 px-3 text-right">Surge Factor</th>
              <th class="py-3 px-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody id="hotelsTableBody" class="divide-y divide-gray-800/60 font-medium">
            <tr><td colspan="7" class="text-center py-8 text-gray-500">Loading hotel rates...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Historical Busyness Chart -->
    <div class="glass rounded-3xl p-6">
      <div class="mb-4">
        <h2 class="text-base font-bold text-white flex items-center gap-2">
          📉 Crowd Index History
        </h2>
        <p class="text-xs text-gray-400">Tracking how Hua Hin busyness score evolves over time</p>
      </div>
      <div class="h-64 w-full">
        <canvas id="historyChart"></canvas>
      </div>
    </div>
  </main>

  <script>
    let currentTarget = "weekend";
    let allHotels = [];
    let currentTierFilter = "all";
    let chartInstance = null;

    async function loadLatest() {
      try {
        const res = await fetch('/api/latest');
        if (!res.ok) return;
        const data = await res.json();
        renderDashboard(data);
      } catch (e) {
        console.error("Error loading latest scan:", e);
      }
    }

    async function loadHistory() {
      try {
        const res = await fetch('/api/history?limit=15');
        const list = await res.json();
        if (!Array.isArray(list) || list.length === 0) return;
        renderChart(list.reverse());
      } catch (e) {
        console.error("Error loading history:", e);
      }
    }

    function renderDashboard(data) {
      document.getElementById('scoreValue').textContent = data.busyness_score.toFixed(1);
      document.getElementById('scoreBar').style.width = data.busyness_score + '%';
      
      const badge = document.getElementById('crowdBadge');
      const isIntl = data.is_international_focus || data.nights >= 7;
      if (isIntl) {
        badge.textContent = `🌍 INTL: ${data.crowd_label.toUpperCase()}`;
        badge.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30';
      } else {
        badge.textContent = `${data.crowd_label.toUpperCase()}`;
        badge.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-orange-500/20 text-orange-400 border border-orange-500/30';
      }
      
      const desc = document.getElementById('crowdDesc');
      desc.textContent = data.crowd_desc || "Normal operating conditions in Hua Hin.";
      
      document.getElementById('lastUpdated').textContent = data.created_at || "Just now";
      document.getElementById('macroAvailable').textContent = (data.macro_available || '--') + ' rooms';
      document.getElementById('macroScore').textContent = data.macro_score + '%';
      document.getElementById('surgeFactor').textContent = data.avg_surge_ratio.toFixed(2) + 'x';
      document.getElementById('bellwetherScore').textContent = data.bellwether_score + '%';
      
      document.getElementById('monitoredDates').textContent = `${data.checkin_date} → ${data.checkout_date}`;
      document.getElementById('monitoredNights').textContent = `${data.nights} night(s) stay`;

      const soldCount = data.sold_out_count || 0;
      const totalCount = data.hotels ? data.hotels.length : 0;
      document.getElementById('soldOutRatio').textContent = `${soldCount} / ${totalCount}`;
      document.getElementById('soldOutTag').textContent = soldCount > 2 ? 'High Demand' : 'Normal';

      allHotels = data.hotels || [];
      document.getElementById('hotelCountBadge').textContent = `${allHotels.length} benchmark hotels`;
      renderHotelsTable();
    }

    function renderHotelsTable() {
      const tbody = document.getElementById('hotelsTableBody');
      const filtered = currentTierFilter === 'all' 
        ? allHotels 
        : allHotels.filter(h => h.tier.toLowerCase() === currentTierFilter.toLowerCase());

      if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center py-6 text-gray-500">No hotels match this filter.</td></tr>';
        return;
      }

      tbody.innerHTML = filtered.map(h => {
        const isSoldOut = h.is_sold_out;
        const name = h.hotel_name || h.name;
        const base = '฿' + Math.round(h.baseline_thb).toLocaleString();
        const curr = isSoldOut ? '<span class="text-red-400 font-bold">SOLD OUT</span>' : '฿' + Math.round(h.nightly_price_thb).toLocaleString();
        
        let surgeBadge = '';
        if (isSoldOut) {
          surgeBadge = '<span class="px-2 py-0.5 rounded text-xs bg-red-500/20 text-red-400 font-bold">SOLD OUT</span>';
        } else {
          const ratio = h.surge_ratio;
          const diffPct = Math.round((ratio - 1) * 100);
          const colorClass = ratio > 1.3 ? 'text-red-400 bg-red-500/10' : (ratio > 1.1 ? 'text-amber-400 bg-amber-500/10' : 'text-emerald-400 bg-emerald-500/10');
          const sign = diffPct > 0 ? '+' : '';
          surgeBadge = `<span class="px-2 py-0.5 rounded text-xs font-semibold ${colorClass}">${ratio.toFixed(2)}x (${sign}${diffPct}%)</span>`;
        }

        const statusPill = isSoldOut
          ? '<span class="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 font-medium">🚫 Booked</span>'
          : '<span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-medium">✓ Available</span>';

        const tierColors = {
          'Luxury': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
          'Midscale': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
          'Budget': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
        };
        const tierBadge = `<span class="px-2 py-0.5 rounded-md text-xs font-semibold border ${tierColors[h.tier] || ''}">${h.tier}</span>`;

        return `
          <tr class="hover:bg-gray-800/40 transition">
            <td class="py-3 px-3 text-white font-semibold">${name}</td>
            <td class="py-3 px-3">${tierBadge}</td>
            <td class="py-3 px-3 text-gray-400 text-xs">${h.area || ''}</td>
            <td class="py-3 px-3 text-right text-gray-400">${base}</td>
            <td class="py-3 px-3 text-right font-bold text-white">${curr}</td>
            <td class="py-3 px-3 text-right">${surgeBadge}</td>
            <td class="py-3 px-3 text-center">${statusPill}</td>
          </tr>
        `;
      }).join('');
    }

    function filterTier(tier) {
      currentTierFilter = tier;
      document.querySelectorAll('.tier-btn').forEach(b => {
        if (b.dataset.tier === tier) {
          b.className = 'tier-btn px-2.5 py-1 rounded-lg bg-orange-500 text-white font-medium';
        } else {
          b.className = 'tier-btn px-2.5 py-1 rounded-lg text-gray-400 hover:text-white';
        }
      });
      renderHotelsTable();
    }

    function setTarget(target) {
      currentTarget = target;
      document.querySelectorAll('.date-preset').forEach(b => {
        if (b.dataset.target === target) {
          b.className = 'date-preset px-3 py-1.5 rounded-lg text-sm font-medium bg-orange-500 text-white';
        } else {
          b.className = 'date-preset px-3 py-1.5 rounded-lg text-sm font-medium bg-gray-800 text-gray-300 hover:bg-gray-700';
        }
      });
      triggerScan();
    }

    async function triggerScan() {
      const btn = document.getElementById('scanBtn');
      const text = document.getElementById('scanText');
      const icon = document.getElementById('scanIcon');
      
      text.textContent = 'Scanning...';
      icon.classList.add('animate-spin');
      btn.disabled = true;

      try {
        const res = await fetch('/api/scan', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({target: currentTarget})
        });
        const data = await res.json();
        renderDashboard(data);
        await loadHistory();
      } catch (e) {
        alert('Scan error: ' + e);
      } finally {
        text.textContent = 'Scan Now';
        icon.classList.remove('animate-spin');
        btn.disabled = false;
      }
    }

    function renderChart(history) {
      const ctx = document.getElementById('historyChart').getContext('2d');
      const labels = history.map(h => (h.created_at || '').substring(5, 16));
      const scores = history.map(h => h.busyness_score);

      if (chartInstance) chartInstance.destroy();

      chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Hua Hin Busyness Score',
            data: scores,
            borderColor: '#f97316',
            backgroundColor: 'rgba(249, 115, 22, 0.15)',
            borderWidth: 2,
            tension: 0.35,
            fill: true,
            pointBackgroundColor: '#f97316',
            pointRadius: 4,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false }
          },
          scales: {
            y: {
              min: 0,
              max: 100,
              grid: { color: 'rgba(255, 255, 255, 0.05)' },
              ticks: { color: '#9ca3af' }
            },
            x: {
              grid: { display: false },
              ticks: { color: '#9ca3af' }
            }
          }
        }
      });
    }

    async function loadTransit(travelDate) {
      try {
        const url = travelDate ? `/api/transit?date=${travelDate}` : '/api/transit';
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        
        document.getElementById('transitStressScore').textContent = data.transit_stress_score.toFixed(1) + '%';
        document.getElementById('transitBadge').textContent = data.influx_label.toUpperCase();
        document.getElementById('airportBusOperator').textContent = data.airport_bus.operator;
        document.getElementById('airportBusStatus').textContent = data.airport_bus.status;
        document.getElementById('airportBusFare').textContent = 'From ฿' + data.airport_bus.min_fare_thb;

        document.getElementById('trainsCount').textContent = `~${data.bangkok_transit.trains_available} trains / day`;
        document.getElementById('vansCount').textContent = `~${data.bangkok_transit.vans_buses_available} minivan services`;
        
        const soldOutEl = document.getElementById('soldOutTransit');
        if (data.bangkok_transit.sold_out_markers > 0) {
          soldOutEl.textContent = `${data.bangkok_transit.sold_out_markers} departures full`;
          soldOutEl.className = 'text-red-400 font-semibold';
        } else {
          soldOutEl.textContent = 'Seats available';
          soldOutEl.className = 'text-emerald-400 font-semibold';
        }
      } catch (e) {
        console.error("Transit load error:", e);
      }
    }

    async function loadTours() {
      try {
        const res = await fetch('/api/tours');
        if (!res.ok) return;
        const data = await res.json();
        
        document.getElementById('tourDemandScore').textContent = data.tour_demand_score.toFixed(1) + '%';
        document.getElementById('tourBadge').textContent = data.tour_label.toUpperCase();
        
        const tbody = document.getElementById('toursTableBody');
        if (!data.benchmark_tours || data.benchmark_tours.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-gray-500">No tours loaded.</td></tr>';
          return;
        }

        tbody.innerHTML = data.benchmark_tours.map(t => {
          const fare = '฿' + t.price_thb.toLocaleString();
          const rating = t.rating ? `★ ${t.rating} (${t.reviews_count})` : '★ 4.7 (250+)';
          const status = t.is_high_demand 
            ? '<span class="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 font-bold">🔥 High Demand</span>'
            : '<span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-medium">✓ Available</span>';

          return `
            <tr class="hover:bg-gray-800/40 transition">
              <td class="py-2.5 px-3 text-xs text-gray-400">${t.category}</td>
              <td class="py-2.5 px-3 text-white font-medium">${t.name}</td>
              <td class="py-2.5 px-3 text-right font-bold text-cyan-400">${fare}</td>
              <td class="py-2.5 px-3 text-center text-xs text-amber-300 font-medium">${rating}</td>
              <td class="py-2.5 px-3 text-center">${status}</td>
            </tr>
          `;
        }).join('');
      } catch (e) {
        console.error("Tours load error:", e);
      }
    }

    // Initialize
    loadLatest();
    loadHistory();
    loadTransit();
    loadTours();
  </script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
