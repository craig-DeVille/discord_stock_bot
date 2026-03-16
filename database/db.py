import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "ticker.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY,
                guild_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                added_by TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, symbol)
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                floor REAL,
                ceiling REAL,
                triggered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS vol_configs (
                id INTEGER PRIMARY KEY,
                guild_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                threshold_pct REAL NOT NULL,
                UNIQUE(guild_id, symbol)
            );

            CREATE TABLE IF NOT EXISTS scheduler_config (
                guild_id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL,
                daily_active INTEGER DEFAULT 1,
                intraday_interval_minutes INTEGER DEFAULT NULL,
                last_intraday_post TEXT DEFAULT NULL
            );

            CREATE TABLE IF NOT EXISTS posted_links (
                id INTEGER PRIMARY KEY,
                channel_id TEXT NOT NULL,
                url TEXT NOT NULL,
                message_id TEXT NOT NULL,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(channel_id, url)
            );
        """)
        await db.commit()


async def seed_default_watchlist(guild_id: str, symbols: list[str]):
    async with aiosqlite.connect(DB_PATH) as db:
        for symbol in symbols:
            await db.execute(
                "INSERT OR IGNORE INTO watchlist (guild_id, symbol, added_by) VALUES (?, ?, ?)",
                (guild_id, symbol.upper(), "system"),
            )
        await db.commit()


# --- Watchlist ---

async def get_watchlist(guild_id: str) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT symbol FROM watchlist WHERE guild_id = ? ORDER BY added_at",
            (guild_id,),
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def count_watchlist(guild_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM watchlist WHERE guild_id = ?", (guild_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def add_to_watchlist(guild_id: str, symbol: str, added_by: str) -> bool:
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO watchlist (guild_id, symbol, added_by) VALUES (?, ?, ?)",
                (guild_id, symbol.upper(), added_by),
            )
            await db.commit()
        return True
    except aiosqlite.IntegrityError:
        return False


async def remove_from_watchlist(guild_id: str, symbol: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM watchlist WHERE guild_id = ? AND symbol = ?",
            (guild_id, symbol.upper()),
        )
        await db.commit()
        return cursor.rowcount > 0


# --- Alerts ---

async def count_user_alerts(user_id: str, guild_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM alerts WHERE user_id = ? AND guild_id = ? AND triggered = 0",
            (user_id, guild_id),
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def add_alert(user_id: str, guild_id: str, symbol: str, floor: float | None, ceiling: float | None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO alerts (user_id, guild_id, symbol, floor, ceiling) VALUES (?, ?, ?, ?, ?)",
            (user_id, guild_id, symbol.upper(), floor, ceiling),
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_alerts(user_id: str, guild_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, symbol, floor, ceiling FROM alerts WHERE user_id = ? AND guild_id = ? AND triggered = 0",
            (user_id, guild_id),
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "symbol": r[1], "floor": r[2], "ceiling": r[3]} for r in rows]


async def get_all_active_alerts() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, user_id, guild_id, symbol, floor, ceiling FROM alerts WHERE triggered = 0"
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "user_id": r[1], "guild_id": r[2], "symbol": r[3], "floor": r[4], "ceiling": r[5]} for r in rows]


async def mark_alert_triggered(alert_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE alerts SET triggered = 1 WHERE id = ?", (alert_id,))
        await db.commit()


async def remove_alert(alert_id: int, user_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM alerts WHERE id = ? AND user_id = ?", (alert_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0


# --- Volatility Configs ---

async def set_vol_config(guild_id: str, symbol: str, threshold_pct: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO vol_configs (guild_id, symbol, threshold_pct) VALUES (?, ?, ?) "
            "ON CONFLICT(guild_id, symbol) DO UPDATE SET threshold_pct = excluded.threshold_pct",
            (guild_id, symbol.upper(), threshold_pct),
        )
        await db.commit()


async def count_vol_configs(guild_id: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM vol_configs WHERE guild_id = ?", (guild_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_vol_configs(guild_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT symbol, threshold_pct FROM vol_configs WHERE guild_id = ?", (guild_id,)
        )
        rows = await cursor.fetchall()
        return [{"symbol": r[0], "threshold_pct": r[1]} for r in rows]


# --- Scheduler Config ---

async def set_scheduler_channel(guild_id: str, channel_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO scheduler_config (guild_id, channel_id) VALUES (?, ?) "
            "ON CONFLICT(guild_id) DO UPDATE SET channel_id = excluded.channel_id",
            (guild_id, channel_id),
        )
        await db.commit()


async def get_scheduler_config(guild_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT channel_id, daily_active, intraday_interval_minutes, last_intraday_post "
            "FROM scheduler_config WHERE guild_id = ?",
            (guild_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "channel_id": row[0],
            "daily_active": bool(row[1]),
            "intraday_interval_minutes": row[2],
            "last_intraday_post": row[3],
        }


async def get_scheduler_channel(guild_id: str) -> str | None:
    config = await get_scheduler_config(guild_id)
    return config["channel_id"] if config else None


async def set_intraday_interval(guild_id: str, interval_minutes: int | None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE scheduler_config SET intraday_interval_minutes = ?, daily_active = 1 WHERE guild_id = ?",
            (interval_minutes, guild_id),
        )
        await db.commit()


async def set_daily_active(guild_id: str, active: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE scheduler_config SET daily_active = ? WHERE guild_id = ?",
            (1 if active else 0, guild_id),
        )
        await db.commit()


async def update_last_intraday_post(guild_id: str, timestamp: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE scheduler_config SET last_intraday_post = ? WHERE guild_id = ?",
            (timestamp, guild_id),
        )
        await db.commit()


# --- Posted Links (scroll/duplicate detection) ---

async def check_link_exists(channel_id: str, url: str) -> str | None:
    """Returns the original message_id if the URL was already posted in this channel, else None."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT message_id FROM posted_links WHERE channel_id = ? AND url = ?",
            (channel_id, url),
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def record_link(channel_id: str, url: str, message_id: str):
    """Record a newly posted link. Silently ignores duplicates."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO posted_links (channel_id, url, message_id) VALUES (?, ?, ?)",
            (channel_id, url, message_id),
        )
        await db.commit()


async def get_all_scheduler_configs() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT guild_id, channel_id, daily_active, intraday_interval_minutes, last_intraday_post "
            "FROM scheduler_config"
        )
        rows = await cursor.fetchall()
        return [
            {
                "guild_id": r[0],
                "channel_id": r[1],
                "daily_active": bool(r[2]),
                "intraday_interval_minutes": r[3],
                "last_intraday_post": r[4],
            }
            for r in rows
        ]
