# Oil Desk — Discord Stock Bot

A Discord bot for tracking oil ETFs and energy funds in a server. Supports live price lookups, a group watchlist, price floor/ceiling alerts, volatility alerts, and daily market summaries.

## Default Watchlist

| Ticker | Fund |
|---|---|
| USO | United States Oil Fund |
| UCO | ProShares Ultra Bloomberg Crude Oil (2x) |
| BNO | United States Brent Oil Fund |
| XOP | SPDR S&P Oil & Gas E&P ETF |
| XLE | Energy Select Sector SPDR Fund |

## Commands

| Command | Description |
|---|---|
| `/price <symbol>` | Live price for any ticker |
| `/watchlist` | Show all tracked symbols with prices |
| `/add <symbol>` | Add a symbol to the group watchlist |
| `/remove <symbol>` | Remove a symbol from the watchlist |
| `/alert <symbol> [floor] [ceiling]` | DM alert when price breaks a range |
| `/alerts` | List your active alerts |
| `/alert_remove <id>` | Delete an alert |
| `/volconfig <symbol> <threshold%>` | Ping channel when symbol moves X%+ in a day |
| `/subscribe` | Opt in to daily open/close summaries via DM |
| `/unsubscribe` | Opt out of DM summaries |
| `/setchannel <channel>` | Set channel for daily updates (admin only) |
| `/help` | Show all commands |

## Setup

### 1. Clone & install
```bash
git clone https://github.com/craig-DeVille/discord_stock_bot.git
cd discord_stock_bot
pip install -r requirements.txt
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

The bot will sync slash commands to your server automatically on startup.

## Creating a Discord Bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) → New Application
2. **Bot** tab → Add Bot → Reset Token → copy it into `.env`
3. **OAuth2 → URL Generator** → check `bot` + `applications.commands` → copy invite URL → add to your server

## Stack

- [discord.py 2.x](https://discordpy.readthedocs.io/)
- [yfinance](https://github.com/ranaroussi/yfinance) — market data, no API key required
- SQLite — watchlists, alerts, subscriptions
- Python 3.12+

## Disclaimer

All price data is for entertainment purposes only. Not financial advice.
