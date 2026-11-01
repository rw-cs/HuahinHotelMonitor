# 🏖️ Hua Hin Hotel Price & Busyness Monitor

> A real-time **Crowd Density & Hotel Price Pulse Index (0–100%)** for Hua Hin, Thailand.

Instead of guessing whether Hua Hin is packed or empty, this system uses hotel dynamic pricing algorithms and area inventory as a live occupancy proxy. It tracks both macro market capacity and a curated basket of benchmark hotels to gauge tourist influx.

---

## 📊 How the "Hua Hin Busyness Score" Works

The system calculates a normalized **0–100% Crowd Index** by combining two weighted signals:

$$\text{Busyness Score} = 40\% \times \text{Macro Scarcity} + 60\% \times \text{Bellwether Surge}$$

1. **Macro Scarcity (40% weight)**:
   - Evaluates total available accommodations in Hua Hin against off-peak baseline inventory (~850 properties).
   - Scrapes explicit OTA market banners (e.g. *"85% of places to stay are unavailable for your dates"*).

2. **Bellwether Price Surge & Sellout Multiplier (60% weight)**:
   - Tracks a representative basket of **8–12 benchmark hotels** spanning **Luxury**, **Upper-Midscale / Families**, and **Budget**:
     - **Luxury / Beachfront**: *The Standard Hua Hin, Hua Hin Marriott, Centara Grand, Hilton Hua Hin, InterContinental, Mövenpick Asara*
     - **Midscale / Family**: *Holiday Inn Resort Vana Nava, G Hua Hin Resort, The Peri Hotel, Amari Hua Hin, NH Hua Hin*
     - **Budget & Hostels (< ฿1,200)**: *Hub Hua Hin 57 Hostel (฿450), Mad Monkey Hostel (฿450), Hua Hin Home Hill (฿500), Sea Residence Hua Hin 45 (฿550), Mandarin Lodge (฿600), Chaba Chalet (฿700), Huahin Terminal (฿750), Thipurai City (฿850), Baan Manthana (฿850), ibis Hua Hin (฿1,100), City Beach (฿1,100), Kiang Haad Beach (฿1,200)*
   - Calculates the **Price Surge Multiplier** vs. low-season weekday baselines:
     $$\text{Surge Multiplier} = \frac{\text{Current Rate / Night}}{\text{Baseline Rate}}$$
   - Any property completely booked out automatically receives a maximum surge penalty.

### 🚥 Crowd Levels & Classification

| Score Range | Status | Color | What It Feels Like in Hua Hin |
| :--- | :--- | :---: | :--- |
| **0 – 30%** | 🟢 **Chill / Very Quiet** | Emerald | Ghost town vibes, empty beaches, instant seating at restaurants, deep hotel discounts. |
| **31 – 55%** | 🟡 **Moderate / Relaxed** | Amber | Pleasant weekday crowd, relaxed cafe atmosphere, easy parking, smooth traffic. |
| **56 – 75%** | 🟠 **Busy / High Energy** | Orange | Classic weekend rush! Cicada and Tamarind night markets buzzing, active beach clubs. |
| **76 – 90%** | 🔴 **Very Busy / Crowded** | Red | High tourist influx, Rama II traffic heavy from Bangkok, top resorts fully booked. |
| **91 – 100%** | 🚨 **Peak / Packed Out** | Purple | Long holiday gridlock (Songkran / NYE), severe traffic delays, virtually sold out town. |

---

## 🚀 Quick Start

### 1. Environment Setup
The project uses Python 3.10+ and Playwright for stealth scraping:

```bash
# Clone/enter the directory
cd /Users/rob/Documents/HuahinHotelMonitor

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (already pre-installed in workspace)
pip install -r requirements.txt
playwright install chromium
```

---

## 💻 CLI Usage

The rich command-line interface provides instant visual terminal reports:

```bash
# 1. Run a live scan for the upcoming weekend (Friday - Sunday)
python cli.py scan

# 2. Run a Midweek International Scan (Tuesday - Thursday: isolates foreign vacationers from Bangkok weekenders)
python cli.py scan --target midweek

# 3. Run a 7-Night Snowbird Long-Stay Scan (Evaluates multi-week capacity)
python cli.py scan --target snowbird

# 4. Check live Suvarnabhumi Airport Bus & 12Go transit arrivals
python cli.py transit

# 5. Check Western international tour bookings (GetYourGuide)
python cli.py tours

# 6. Run a live scan for tonight (1 night)
python cli.py scan --target tonight

# 7. View the most recent scan report
python cli.py latest

# 8. Show recent scan history
python cli.py history
```

---

## 🌐 Web Dashboard

Start the local web dashboard for an interactive, visual interface:

```bash
python web_app.py
```
Then open [http://localhost:8000](http://localhost:8000) in your browser.

**Web Dashboard Features:**
- **Live Crowd Gauge**: Visual radial meter with dynamic status badges.
- **Preset Buttons**: Quick toggles between *This Weekend*, *Tonight*, and *Next Weekend*.
- **1-Click "Scan Now"**: Triggers an on-demand background scrape with real-time UI refresh.
- **Benchmark Breakdown Table**: Filterable by hotel tier (*Luxury*, *Midscale*, *Budget*) with exact surge rates and sellout indicators.
- **Historical Timeline**: Chart.js graph tracking crowd level changes over consecutive days.

---

## ⏰ Automated Background Scheduler & Alerts

To continuously monitor Hua Hin and receive notifications when weekend crowding surges:

```bash
# Runs automatically every 6 hours (or pass custom hour interval)
python scheduler.py 6
```

### Discord / Telegram Alerts (Optional)
Export your webhook or bot tokens before starting the scheduler:

```bash
# Discord Webhook
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."

# Telegram Bot
export TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
export TELEGRAM_CHAT_ID="-100123456789"

# Alert threshold (default: triggers alert if Busyness Score >= 70%)
export ALERT_THRESHOLD=70.0
```

---

## ⚙️ Customization

Edit [`config.py`](file:///Users/rob/Documents/HuahinHotelMonitor/config.py) to:
- Add or remove benchmark hotels
- Adjust baseline low-season prices (`baseline_thb`)
- Tweak the weights between macro scarcity and hotel price surges
