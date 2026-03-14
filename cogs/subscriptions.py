import discord
from discord import app_commands
from discord.ext import commands

from database.db import (
    get_scheduler_config, set_intraday_interval,
    set_daily_active, update_last_intraday_post,
)

VALID_INTERVALS = {
    "daily": None, "15m": 15, "30m": 30, "1h": 60, "2h": 120, "4h": 240,
}


class Subscriptions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="subscribe", description="Enable scheduled updates for this server")
    @app_commands.guild_only()
    @app_commands.describe(interval="What to enable: daily summaries only, or intraday at a set interval")
    @app_commands.choices(interval=[
        app_commands.Choice(name="Daily open/close only",  value="daily"),
        app_commands.Choice(name="Every 15 minutes",       value="15m"),
        app_commands.Choice(name="Every 30 minutes",       value="30m"),
        app_commands.Choice(name="Every hour",             value="1h"),
        app_commands.Choice(name="Every 2 hours",          value="2h"),
        app_commands.Choice(name="Every 4 hours",          value="4h"),
    ])
    async def subscribe(self, interaction: discord.Interaction, interval: str):
        config = await get_scheduler_config(str(interaction.guild_id))
        if not config:
            await interaction.response.send_message(
                "Set a channel first with `/setchannel`.", ephemeral=True
            )
            return

        minutes = VALID_INTERVALS[interval]
        await set_daily_active(str(interaction.guild_id), True)
        await set_intraday_interval(str(interaction.guild_id), minutes)

        if minutes:
            await update_last_intraday_post(str(interaction.guild_id), "")
            msg = f"Daily open/close summaries and intraday updates every **{interval}** are now active."
        else:
            msg = "Daily open/close summaries are now active. No intraday updates."

        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="unsubscribe", description="Pause scheduled updates")
    @app_commands.guild_only()
    @app_commands.describe(what="What to pause: just intraday updates, or everything")
    @app_commands.choices(what=[
        app_commands.Choice(name="Intraday updates only", value="intraday"),
        app_commands.Choice(name="Everything (intraday + daily)", value="all"),
    ])
    async def unsubscribe(self, interaction: discord.Interaction, what: str):
        config = await get_scheduler_config(str(interaction.guild_id))
        if not config:
            await interaction.response.send_message("No updates were configured.", ephemeral=True)
            return

        if what == "intraday":
            await set_intraday_interval(str(interaction.guild_id), None)
            await interaction.response.send_message(
                "Intraday updates paused. Daily open/close summaries are still active.", ephemeral=True
            )
        else:
            await set_intraday_interval(str(interaction.guild_id), None)
            await set_daily_active(str(interaction.guild_id), False)
            await interaction.response.send_message(
                "All scheduled updates paused. Use `/subscribe` to turn them back on.", ephemeral=True
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(Subscriptions(bot))
