import discord
from discord import app_commands
from discord.ext import commands

from database.db import (
    get_scheduler_config, set_intraday_interval,
    set_daily_active, update_last_intraday_post,
)

VALID_INTERVALS = {
    "15m": 15, "30m": 30, "1h": 60, "2h": 120, "4h": 240,
}


class Subscriptions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="subscribe", description="Set how often the bot posts intraday price updates")
    @app_commands.guild_only()
    @app_commands.describe(interval="How often to post: 15m, 30m, 1h, 2h, 4h")
    @app_commands.choices(interval=[
        app_commands.Choice(name="Every 15 minutes", value="15m"),
        app_commands.Choice(name="Every 30 minutes", value="30m"),
        app_commands.Choice(name="Every hour",       value="1h"),
        app_commands.Choice(name="Every 2 hours",    value="2h"),
        app_commands.Choice(name="Every 4 hours",    value="4h"),
    ])
    async def subscribe(self, interaction: discord.Interaction, interval: str):
        config = await get_scheduler_config(str(interaction.guild_id))
        if not config:
            await interaction.response.send_message(
                "Set a channel first with `/setchannel`.", ephemeral=True
            )
            return

        minutes = VALID_INTERVALS[interval]
        await set_intraday_interval(str(interaction.guild_id), minutes)
        await update_last_intraday_post(str(interaction.guild_id), "")  # reset timer
        await interaction.response.send_message(
            f"Intraday updates set to every **{interval}** in <#{config['channel_id']}>. "
            f"Daily open/close summaries are also active.",
            ephemeral=True,
        )

    @app_commands.command(name="unsubscribe", description="Pause all scheduled updates (intraday and daily)")
    @app_commands.guild_only()
    async def unsubscribe(self, interaction: discord.Interaction):
        config = await get_scheduler_config(str(interaction.guild_id))
        if not config:
            await interaction.response.send_message("No updates were configured.", ephemeral=True)
            return

        await set_intraday_interval(str(interaction.guild_id), None)
        await set_daily_active(str(interaction.guild_id), False)
        await interaction.response.send_message(
            "All scheduled updates paused. Use `/subscribe` to turn them back on.", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Subscriptions(bot))
