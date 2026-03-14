# Oil Desk — Discord Stock Bot

A Discord bot for tracking oil ETFs and energy funds in a server. Posts daily market open/close summaries, optional intraday updates, price alerts, and volatility alerts to a configured channel.

## Default Watchlist

| Ticker | Fund |
|---|---|
| USO | United States Oil Fund |
| UCO | ProShares Ultra Bloomberg Crude Oil (2x) |
| BNO | United States Brent Oil Fund |
| XOP | SPDR S&P Oil & Gas E&P ETF |
| XLE | Energy Select Sector SPDR Fund |

## Commands

### Prices
| Command | Description |
|---|---|
| `/price <symbol>` | Live price for any ticker |
| `/watchlist` | Show all tracked symbols with prices |
| `/add <symbol>` | Add a symbol to the group watchlist (max 25) |
| `/remove <symbol>` | Remove a symbol from the watchlist |

### Alerts
| Command | Description |
|---|---|
| `/alert <symbol> [floor] [ceiling]` | Ping the channel when price breaks a range (max 10 per user) |
| `/alerts` | List your active alerts |
| `/alert_remove <id>` | Delete an alert |

### Scheduled Updates
| Command | Description |
|---|---|
| `/subscribe <interval>` | Add intraday price updates to the channel (15m / 30m / 1h / 2h / 4h) |
| `/unsubscribe` | Pause all scheduled updates (intraday and daily) |

### Admin
| Command | Description |
|---|---|
| `/setchannel <channel>` | Set the channel for all updates and alerts |

### Help
| Command | Description |
|---|---|
| `/help` | Show all commands |

## How Scheduled Updates Work

- **Daily open summary** posts automatically at 9:35 AM ET on market days
- **Daily close summary** posts automatically at 4:05 PM ET on market days
- Both are on by default once `/setchannel` is set
- `/subscribe` adds optional intraday updates at your chosen interval on top of the daily posts
- `/unsubscribe` pauses everything — daily and intraday — until you run `/subscribe` again

## Setup

### 1. Clone & install
```bash
git clone https://github.com/craig-DeVille/discord_stock_bot.git
cd discord_stock_bot
pip install -r requirements.txt
pip install audioop-lts  # required for Python 3.13+
```

### 2. Configure
```bash
cp .env.example .env
# Add your Discord bot token to .env
```

### 3. Run
```bash
python bot.py
```

### 4. First-time Discord setup
1. Run `/setchannel #your-channel` in your server — this enables daily open/close posts
2. Optionally run `/subscribe 1h` to add hourly intraday updates

## Creating a Discord Bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) → New Application
2. **Bot** tab → Add Bot → Reset Token → copy into `.env`
3. **OAuth2 → URL Generator** → check `bot` + `applications.commands` → copy invite URL → add to your server

## Stack

- [discord.py 2.x](https://discordpy.readthedocs.io/)
- [yfinance](https://github.com/ranaroussi/yfinance) — market data, no API key required
- SQLite — watchlist, alerts, vol configs, scheduler config
- Python 3.13+

## Disclaimer

All price data is for entertainment purposes only. Not financial advice.
