import discord
from discord import app_commands
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all available bot commands")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛢️ Oil Desk — Commands",
            color=0xF39C12,
        )

        embed.add_field(
            name="📊 Prices",
            value=(
                "`/price <symbol>` — Get current price for any ticker\n"
                "`/watchlist` — Show all tracked symbols with prices\n"
                "`/add <symbol>` — Add a symbol to the group watchlist\n"
                "`/remove <symbol>` — Remove a symbol from the watchlist"
            ),
            inline=False,
        )

        embed.add_field(
            name="🔔 Alerts",
            value=(
                "`/alert <symbol> [floor] [ceiling]` — Ping you in the channel when price breaks a range\n"
                "`/alerts` — List your active alerts\n"
                "`/alert_remove <id>` — Delete an alert\n"
                "`/volconfig <symbol> <threshold%>` — Ping the channel when a symbol moves more than X% in a day"
            ),
            inline=False,
        )

        embed.add_field(
            name="🕐 Scheduled Updates",
            value=(
                "`/subscribe daily` — Enable daily open/close summaries only\n"
                "`/subscribe <interval>` — Enable intraday updates (15m / 30m / 1h / 2h / 4h) + daily\n"
                "`/unsubscribe intraday` — Stop intraday updates, keep daily summaries\n"
                "`/unsubscribe all` — Pause everything until you subscribe again"
            ),
            inline=False,
        )

        embed.add_field(
            name="⚙️ Setup (Admin)",
            value="`/setchannel <channel>` — Set the channel for daily market updates and volatility alerts",
            inline=False,
        )

        embed.add_field(
            name="📈 Default Watchlist",
            value="`USO` · `UCO` · `BNO` · `XOP` · `XLE`",
            inline=False,
        )

        embed.set_footer(text="Not financial advice.")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
