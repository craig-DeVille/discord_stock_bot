import discord
from discord import app_commands
from discord.ext import commands

from database.db import subscribe, unsubscribe, get_subscribers


class Subscriptions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="subscribe", description="Subscribe to daily oil market summaries")
    async def subscribe_cmd(self, interaction: discord.Interaction):
        await subscribe(str(interaction.user.id), str(interaction.guild_id))
        await interaction.response.send_message(
            "Subscribed! You'll get daily open/close summaries via DM.", ephemeral=True
        )

    @app_commands.command(name="unsubscribe", description="Stop receiving daily market summaries")
    async def unsubscribe_cmd(self, interaction: discord.Interaction):
        await unsubscribe(str(interaction.user.id), str(interaction.guild_id))
        await interaction.response.send_message("Unsubscribed. You won't get daily DMs anymore.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Subscriptions(bot))
