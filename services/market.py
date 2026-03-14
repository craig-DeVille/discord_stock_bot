import asyncio
import time
from typing import Optional
import yfinance as yf

# Simple in-memory TTL cache — avoids hammering Yahoo Finance
_cache: dict[str, tuple[dict, float]] = {}
CACHE_TTL = 60  # seconds


def _is_market_hours() -> bool:
    from datetime import datetime
    import pytz
    et = pytz.timezone("America/New_York")
    now = datetime.now(et)
    if now.weekday() >= 5:  # Saturday/Sunday
        return False
    open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
    close_time = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_time <= now <= close_time


def _fetch_quote(symbol: str) -> Optional[dict]:
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")

        if hist.empty or len(hist) < 1:
            return None

        latest = hist.iloc[-1]
        price = float(latest["Close"])
        day_high = float(latest["High"])
        day_low = float(latest["Low"])
        volume = int(latest["Volume"]) if latest["Volume"] else None

        prev_close = float(hist.iloc[-2]["Close"]) if len(hist) >= 2 else price
        change = price - prev_close
        change_pct = (change / prev_close) * 100

        return {
            "symbol": symbol.upper(),
            "price": price,
            "prev_close": prev_close,
            "change": change,
            "change_pct": change_pct,
            "day_high": day_high,
            "day_low": day_low,
            "volume": volume,
            "market_hours": _is_market_hours(),
        }
    except Exception:
        return None


async def get_quote(symbol: str) -> Optional[dict]:
    symbol = symbol.upper()
    now = time.monotonic()

    if symbol in _cache:
        data, ts = _cache[symbol]
        if now - ts < CACHE_TTL:
            return data

    # Run blocking yfinance call in a thread with a timeout
    try:
        data = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, _fetch_quote, symbol),
            timeout=10,
        )
    except asyncio.TimeoutError:
        return None

    if data:
        _cache[symbol] = (data, now)

    return data


async def get_quotes(symbols: list[str]) -> dict[str, Optional[dict]]:
    results = await asyncio.gather(*[get_quote(s) for s in symbols])
    return {s.upper(): r for s, r in zip(symbols, results)}


def format_change(change_pct: float) -> str:
    if change_pct >= 0:
        return f"🟢 ▲ {abs(change_pct):.2f}%"
    return f"🔴 ▼ {abs(change_pct):.2f}%"


def embed_color(change_pct: float) -> int:
    if change_pct > 0:
        return 0x2ECC71  # green
    elif change_pct < 0:
        return 0xE74C3C  # red
    return 0x95A5A6  # grey
