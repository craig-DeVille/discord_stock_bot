# Discord Ticker Bot — Specs

## Overview
A Discord bot for tracking oil ETFs in a friend group server. Posts updates, supports on-demand price checks, per-user subscriptions, price floor/ceiling alerts, and high-volatility day alerts.

---

## Default Watchlist (Pre-loaded)

| Ticker | Name | Type |
|---|---|---|
| **USO** | United States Oil Fund | WTI crude futures tracker |
| **UCO** | ProShares Ultra Bloomberg Crude Oil | 2x leveraged crude |
| **BNO** | United States Brent Oil Fund | Brent crude tracker |
| **XOP** | SPDR S&P Oil & Gas Exploration & Production ETF | E&P companies, volatile |
| **XLE** | Energy Select Sector SPDR Fund | Broad energy (Exxon, Chevron) |

---

## Data Source

**yfinance** (Yahoo Finance Python library)
- Free, no API key required
- Handles ETFs perfectly
- No meaningful rate limits for small bots
- Returns: price, prev close, 24h high/low, volume, % change

---

## Features

### Commands

| Command | Description |
|---|---|
| `/price <symbol>` | On-demand price for any symbol |
| `/watchlist` | Show current group watchlist with prices |
| `/add <symbol>` | Add a symbol to the group watchlist |
| `/remove <symbol>` | Remove a symbol from the group watchlist |
| `/subscribe` | Opt in to scheduled daily updates (personal DM or group) |
| `/unsubscribe` | Opt out of alerts/updates |
| `/alert <symbol> floor <price> ceiling <price>` | Set price range alert — ping when breached |
| `/alerts` | List your active alerts |
| `/alert remove <id>` | Remove an alert |
| `/volconfig <symbol> <threshold%>` | Alert the chat when daily % move exceeds threshold |

### Scheduled Updates
- **Daily open summary** (9:35 AM ET, after market open) — posts watchlist prices to a configured channel
- **Daily close summary** (4:05 PM ET) — posts EOD prices + day's % changes
- **High volatility alert** — fires mid-day if any watched symbol moves beyond configured threshold (default: 5%)

### Alert System
- Floor/ceiling alerts: ping user (or channel) when price breaks out of set range
- Volatility alerts: configurable per-symbol % threshold
- Alerts are persistent (survive bot restart)

---

## Technical Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Bot Framework | discord.py 2.x |
| Market Data | yfinance |
| Scheduler | discord.py tasks loop (APScheduler as backup) |
| Database | SQLite + aiosqlite |
| Config | python-dotenv |
| Hosting | Run locally (dev/joke use) or Railway ($5/mo) for always-on |

---

## Project Structure

```
discord_ticker_bot/
├── bot.py                  # Entry point, cog loader, startup
├── config.py               # Settings, env vars, default watchlist
├── requirements.txt
├── .env.example
├── cogs/
│   ├── prices.py           # /price, /watchlist, /add, /remove
│   ├── alerts.py           # /alert commands + background alert checker
│   ├── subscriptions.py    # /subscribe, /unsubscribe
│   └── scheduler.py        # Daily open/close summary + vol alerts
├── services/
│   └── market.py           # yfinance wrapper with TTL cache
└── database/
    └── db.py               # SQLite schema + CRUD
```

---

## Database Schema

```sql
-- Group watchlist (server-wide)
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY,
    guild_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    added_by TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, symbol)
);

-- Per-user subscriptions
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    active INTEGER DEFAULT 1,
    UNIQUE(user_id, guild_id)
);

-- Price alerts
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    floor REAL,
    ceiling REAL,
    triggered INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Volatility configs
CREATE TABLE vol_configs (
    id INTEGER PRIMARY KEY,
    guild_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    threshold_pct REAL NOT NULL,
    UNIQUE(guild_id, symbol)
);

-- Scheduler channel config
CREATE TABLE scheduler_config (
    guild_id TEXT PRIMARY KEY,
    channel_id TEXT NOT NULL
);
```

---

## Implementation Phases

| Phase | What Gets Built |
|---|---|
| 1 | Bot skeleton + `/price` + yfinance service |
| 2 | SQLite + `/watchlist`, `/add`, `/remove` (pre-loaded with USO/UCO/BNO/XOP/XLE) |
| 3 | `/subscribe`, `/unsubscribe` |
| 4 | `/alert` floor/ceiling + background checker (every 5 min) |
| 5 | `/volconfig` + volatility alert background task |
| 6 | Scheduled daily open/close summaries |
| 7 | Polish: error messages, market hours handling, deploy |

---

## Environment Variables

```env
DISCORD_TOKEN=
# No other API keys needed — yfinance is free and keyless
```

---

## Notes
- Market data only available during US market hours (9:30 AM – 4:00 PM ET, weekdays). Bot should handle off-hours gracefully by returning last close price with a label.
- yfinance is unofficial — if it breaks, fallback is Finnhub (free key required).
- All price data is for entertainment purposes only. Not financial advice.
