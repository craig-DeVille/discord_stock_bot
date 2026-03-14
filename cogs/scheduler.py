import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, time, date
import pytz

from services.market import get_quotes, format_change
from database.db import (
    get_watchlist,
    get_scheduler_config,
    set_scheduler_channel,
    get_all_scheduler_configs,
    update_last_intraday_post,
    set_daily_active,
)
from config import (
    MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE,
    MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE,
    TIMEZONE,
)

ET = pytz.timezone(TIMEZONE)
UTC = pytz.utc


def _et_time_to_utc(hour: int, minute: int) -> time:
    """Convert a wall-clock ET time to UTC, respecting DST on today's date."""
    today = date.today()
    naive = datetime(today.year, today.month, today.day, hour, minute)
    et_dt = ET.localize(naive)
    utc_dt = et_dt.astimezone(UTC)
    return utc_dt.time().replace(tzinfo=UTC)


OPEN_TIME  = _et_time_to_utc(MARKET_OPEN_HOUR,  MARKET_OPEN_MINUTE)
CLOSE_TIME = _et_time_to_utc(MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE)


class Scheduler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_open.start()
        self.daily_close.start()
        self.intraday_tick.start()

    def cog_unload(self):
        self.daily_open.cancel()
        self.daily_close.cancel()
        self.intraday_tick.cancel()

    # --- Admin command ---

    @app_commands.command(name="setchannel", description="Set the channel for all market updates (admin only)")
    @app_commands.guild_only()
    @app_commands.describe(channel="Channel to post daily summaries, intraday updates, and alerts in")
    async def setchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await set_scheduler_channel(str(interaction.guild_id), str(channel.id))
        await interaction.response.send_message(
            f"All market updates will be posted in {channel.mention}.\n"
            f"Daily open/close summaries are on by default. "
            f"Use `/subscribe` to add intraday updates.",
            ephemeral=True,
        )

    # --- Scheduled tasks ---

    @tasks.loop(time=OPEN_TIME)
    async def daily_open(self):
        for guild in self.bot.guilds:
            await self._post_summary(guild, label="Morning Oil Report")

    @tasks.loop(time=CLOSE_TIME)
    async def daily_close(self):
        for guild in self.bot.guilds:
            await self._post_summary(guild, label="EOD Oil Report")

    @tasks.loop(minutes=5)
    async def intraday_tick(self):
        now = datetime.now(ET)
        configs = await get_all_scheduler_configs()

        for cfg in configs:
            if not cfg["daily_active"]:
                continue
            if not cfg["intraday_interval_minutes"]:
                continue

            # Check if enough time has passed since last post
            last = cfg["last_intraday_post"]
            if last:
                try:
                    last_dt = datetime.fromisoformat(last).astimezone(ET)
                    elapsed = (now - last_dt).total_seconds() / 60
                    if elapsed < cfg["intraday_interval_minutes"]:
                        continue
                except ValueError:
                    pass

            guild = self.bot.get_guild(int(cfg["guild_id"]))
            if not guild:
                continue

            await self._post_summary(guild, label="Oil Update")
            await update_last_intraday_post(cfg["guild_id"], now.isoformat())

    @daily_open.before_loop
    @daily_close.before_loop
    @intraday_tick.before_loop
    async def before_loops(self):
        await self.bot.wait_until_ready()

    # --- Shared summary builder ---

    async def _post_summary(self, guild: discord.Guild, label: str):
        guild_id = str(guild.id)
        config = await get_scheduler_config(guild_id)
        if not config or not config["daily_active"]:
            return

        channel = self.bot.get_channel(int(config["channel_id"]))
        if not channel:
            return

        symbols = await get_watchlist(guild_id)
        if not symbols:
            return

        quotes = await get_quotes(symbols)

        embed = discord.Embed(
            title=f"📈 {label}",
            description=datetime.now(ET).strftime("%A, %B %d %Y · %I:%M %p ET"),
            color=0xF39C12,
        )

        for sym in symbols:
            q = quotes.get(sym)
            if q:
                embed.add_field(
                    name=sym,
                    value=f"${q['price']:.2f}  {format_change(q['change_pct'])}",
                    inline=True,
                )
            else:
                embed.add_field(name=sym, value="N/A", inline=True)

        embed.set_footer(text="Not financial advice.")
        await channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Scheduler(bot))
