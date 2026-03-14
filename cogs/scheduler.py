import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, time
import pytz

from services.market import get_quotes, format_change, embed_color
from database.db import (
    get_watchlist, get_subscribers,
    get_scheduler_channel, set_scheduler_channel,
)
from config import (
    MARKET_OPEN_HOUR, MARKET_OPEN_MINUTE,
    MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE,
    TIMEZONE,
)

ET = pytz.timezone(TIMEZONE)

OPEN_TIME = time(hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MINUTE, tzinfo=ET)
CLOSE_TIME = time(hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MINUTE, tzinfo=ET)


class Scheduler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_open.start()
        self.daily_close.start()

    def cog_unload(self):
        self.daily_open.cancel()
        self.daily_close.cancel()

    @app_commands.command(name="setchannel", description="Set the channel for scheduled market updates (admin only)")
    @app_commands.describe(channel="The channel to post daily summaries in")
    @app_commands.checks.has_permissions(administrator=True)
    async def setchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await set_scheduler_channel(str(interaction.guild_id), str(channel.id))
        await interaction.response.send_message(
            f"Daily market summaries will be posted in {channel.mention}.", ephemeral=True
        )

    @tasks.loop(time=OPEN_TIME)
    async def daily_open(self):
        for guild in self.bot.guilds:
            await self._post_summary(guild, label="Morning Oil Report")

    @tasks.loop(time=CLOSE_TIME)
    async def daily_close(self):
        for guild in self.bot.guilds:
            await self._post_summary(guild, label="EOD Oil Report")

    @daily_open.before_loop
    async def before_open(self):
        await self.bot.wait_until_ready()

    @daily_close.before_loop
    async def before_close(self):
        await self.bot.wait_until_ready()

    async def _post_summary(self, guild: discord.Guild, label: str):
        guild_id = str(guild.id)
        channel_id = await get_scheduler_channel(guild_id)
        if not channel_id:
            return

        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            return

        symbols = await get_watchlist(guild_id)
        if not symbols:
            return

        quotes = await get_quotes(symbols)

        embed = discord.Embed(
            title=f"📈 {label}",
            description=f"{datetime.now(ET).strftime('%A, %B %d %Y')}",
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

        # DM subscribers
        subscribers = await get_subscribers(guild_id)
        for user_id in subscribers:
            try:
                user = await self.bot.fetch_user(int(user_id))
                await user.send(embed=embed)
            except discord.Forbidden:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Scheduler(bot))
