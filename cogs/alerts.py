import discord
from discord import app_commands
from discord.ext import commands, tasks

from services.market import get_quote
from database.db import (
    add_alert, get_user_alerts, get_all_active_alerts,
    mark_alert_triggered, remove_alert,
    get_vol_configs, set_vol_config, get_watchlist,
)
from config import ALERT_CHECK_INTERVAL, DEFAULT_VOL_THRESHOLD


class Alerts(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.alert_checker.start()

    def cog_unload(self):
        self.alert_checker.cancel()

    # --- Slash commands ---

    @app_commands.command(name="alert", description="Set a price floor/ceiling alert for a symbol")
    @app_commands.describe(
        symbol="Ticker symbol, e.g. USO",
        floor="Alert when price drops below this value (optional)",
        ceiling="Alert when price rises above this value (optional)",
    )
    async def alert(
        self,
        interaction: discord.Interaction,
        symbol: str,
        floor: float | None = None,
        ceiling: float | None = None,
    ):
        if floor is None and ceiling is None:
            await interaction.response.send_message(
                "Provide at least a `floor` or `ceiling` value.", ephemeral=True
            )
            return

        symbol = symbol.upper()
        data = await get_quote(symbol)
        if not data:
            await interaction.response.send_message(
                f"Could not find **{symbol}**. Check the ticker.", ephemeral=True
            )
            return

        alert_id = await add_alert(
            str(interaction.user.id),
            str(interaction.guild_id),
            symbol,
            floor,
            ceiling,
        )

        parts = []
        if floor is not None:
            parts.append(f"floor **${floor:.2f}**")
        if ceiling is not None:
            parts.append(f"ceiling **${ceiling:.2f}**")

        await interaction.response.send_message(
            f"Alert #{alert_id} set for **{symbol}** — {' and '.join(parts)}. "
            f"Current price: **${data['price']:.2f}**",
            ephemeral=True,
        )

    @app_commands.command(name="alerts", description="List your active price alerts")
    async def alerts(self, interaction: discord.Interaction):
        user_alerts = await get_user_alerts(str(interaction.user.id), str(interaction.guild_id))

        if not user_alerts:
            await interaction.response.send_message("You have no active alerts.", ephemeral=True)
            return

        lines = []
        for a in user_alerts:
            parts = []
            if a["floor"] is not None:
                parts.append(f"floor ${a['floor']:.2f}")
            if a["ceiling"] is not None:
                parts.append(f"ceiling ${a['ceiling']:.2f}")
            lines.append(f"**#{a['id']}** {a['symbol']} — {', '.join(parts)}")

        await interaction.response.send_message(
            "**Your active alerts:**\n" + "\n".join(lines),
            ephemeral=True,
        )

    @app_commands.command(name="alert_remove", description="Remove one of your price alerts")
    @app_commands.describe(alert_id="The alert ID (from /alerts)")
    async def alert_remove(self, interaction: discord.Interaction, alert_id: int):
        removed = await remove_alert(alert_id, str(interaction.user.id))
        if removed:
            await interaction.response.send_message(f"Alert #{alert_id} removed.", ephemeral=True)
        else:
            await interaction.response.send_message(
                f"Alert #{alert_id} not found or doesn't belong to you.", ephemeral=True
            )

    @app_commands.command(name="volconfig", description="Alert the chat when a symbol moves more than X% in a day")
    @app_commands.describe(
        symbol="Ticker symbol to watch for volatility",
        threshold="Percent move to trigger alert, e.g. 5 for 5%",
    )
    async def volconfig(self, interaction: discord.Interaction, symbol: str, threshold: float = DEFAULT_VOL_THRESHOLD):
        symbol = symbol.upper()
        await set_vol_config(str(interaction.guild_id), symbol, threshold)
        await interaction.response.send_message(
            f"Volatility alert set: will ping this channel when **{symbol}** moves ±**{threshold:.1f}%** or more in a day.",
            ephemeral=True,
        )

    # --- Background task ---

    @tasks.loop(seconds=ALERT_CHECK_INTERVAL)
    async def alert_checker(self):
        await self._check_price_alerts()
        await self._check_vol_alerts()

    @alert_checker.before_loop
    async def before_alert_checker(self):
        await self.bot.wait_until_ready()

    async def _check_price_alerts(self):
        active_alerts = await get_all_active_alerts()
        if not active_alerts:
            return

        # Batch fetch unique symbols
        symbols = list({a["symbol"] for a in active_alerts})
        quotes = {}
        for sym in symbols:
            q = await get_quote(sym)
            if q:
                quotes[sym] = q

        for alert in active_alerts:
            q = quotes.get(alert["symbol"])
            if not q:
                continue

            price = q["price"]
            triggered = False
            reason = ""

            if alert["floor"] is not None and price <= alert["floor"]:
                triggered = True
                reason = f"dropped below floor **${alert['floor']:.2f}**"
            elif alert["ceiling"] is not None and price >= alert["ceiling"]:
                triggered = True
                reason = f"hit ceiling **${alert['ceiling']:.2f}**"

            if triggered:
                await mark_alert_triggered(alert["id"])
                try:
                    user = await self.bot.fetch_user(int(alert["user_id"]))
                    await user.send(
                        f"🚨 **{alert['symbol']}** has {reason}! "
                        f"Current price: **${price:.2f}** (Alert #{alert['id']})"
                    )
                except discord.Forbidden:
                    pass  # User has DMs closed

    async def _check_vol_alerts(self):
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            configs = await get_vol_configs(guild_id)
            if not configs:
                continue

            from database.db import get_scheduler_channel
            channel_id = await get_scheduler_channel(guild_id)
            if not channel_id:
                continue

            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                continue

            for cfg in configs:
                q = await get_quote(cfg["symbol"])
                if not q:
                    continue

                move = abs(q["change_pct"])
                if move >= cfg["threshold_pct"]:
                    direction = "up" if q["change_pct"] > 0 else "down"
                    await channel.send(
                        f"🔥 **Volatility Alert** — **{cfg['symbol']}** is {direction} "
                        f"**{move:.2f}%** today! (threshold: {cfg['threshold_pct']:.1f}%) "
                        f"Current: **${q['price']:.2f}**"
                    )


async def setup(bot: commands.Bot):
    await bot.add_cog(Alerts(bot))
