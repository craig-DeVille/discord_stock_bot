import discord
from discord import app_commands
from discord.ext import commands

from services.market import get_quote, get_quotes, format_change, embed_color
from database.db import get_watchlist, add_to_watchlist, remove_from_watchlist, seed_default_watchlist
from config import DEFAULT_WATCHLIST


class Prices(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="price", description="Get the current price for a ticker symbol")
    @app_commands.describe(symbol="Ticker symbol, e.g. USO, UCO, XLE")
    async def price(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer()
        data = await get_quote(symbol)

        if not data:
            await interaction.followup.send(f"Could not find data for **{symbol.upper()}**. Check the ticker and try again.")
            return

        color = embed_color(data["change_pct"])
        label = "" if data["market_hours"] else " *(last close)*"

        embed = discord.Embed(
            title=f"{data['symbol']}{label}",
            color=color,
        )
        embed.add_field(name="Price", value=f"**${data['price']:.2f}**", inline=True)
        embed.add_field(name="Change", value=format_change(data["change_pct"]), inline=True)
        embed.add_field(name="Prev Close", value=f"${data['prev_close']:.2f}", inline=True)

        if data["day_high"] and data["day_low"]:
            embed.add_field(name="Day High", value=f"${data['day_high']:.2f}", inline=True)
            embed.add_field(name="Day Low", value=f"${data['day_low']:.2f}", inline=True)

        if data["volume"]:
            embed.add_field(name="Volume", value=f"{data['volume']:,}", inline=True)

        embed.set_footer(text="Not financial advice.")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="watchlist", description="Show all tracked symbols and their current prices")
    async def watchlist(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = str(interaction.guild_id)
        symbols = await get_watchlist(guild_id)

        if not symbols:
            await interaction.followup.send("Watchlist is empty. Use `/add <symbol>` to add something.")
            return

        quotes = await get_quotes(symbols)

        embed = discord.Embed(title="Oil Desk Watchlist", color=0xF39C12)
        lines = []
        for sym in symbols:
            q = quotes.get(sym)
            if q:
                lines.append(
                    f"**{sym}** — ${q['price']:.2f}  {format_change(q['change_pct'])}"
                )
            else:
                lines.append(f"**{sym}** — N/A")

        embed.description = "\n".join(lines)
        market_note = "" if any(q and q["market_hours"] for q in quotes.values() if q) else "\n*Market closed — showing last close prices.*"
        embed.set_footer(text=f"Not financial advice.{market_note}")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="add", description="Add a symbol to the group watchlist")
    @app_commands.describe(symbol="Ticker symbol to add, e.g. VOO")
    async def add(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer(ephemeral=True)
        symbol = symbol.upper()
        guild_id = str(interaction.guild_id)

        # Validate the symbol exists
        data = await get_quote(symbol)
        if not data:
            await interaction.followup.send(f"Could not find **{symbol}** — double-check the ticker.", ephemeral=True)
            return

        added = await add_to_watchlist(guild_id, symbol, str(interaction.user.id))
        if added:
            await interaction.followup.send(f"Added **{symbol}** to the watchlist.", ephemeral=True)
        else:
            await interaction.followup.send(f"**{symbol}** is already on the watchlist.", ephemeral=True)

    @app_commands.command(name="remove", description="Remove a symbol from the group watchlist")
    @app_commands.describe(symbol="Ticker symbol to remove")
    async def remove(self, interaction: discord.Interaction, symbol: str):
        await interaction.response.defer(ephemeral=True)
        symbol = symbol.upper()
        guild_id = str(interaction.guild_id)

        removed = await remove_from_watchlist(guild_id, symbol)
        if removed:
            await interaction.followup.send(f"Removed **{symbol}** from the watchlist.", ephemeral=True)
        else:
            await interaction.followup.send(f"**{symbol}** wasn't on the watchlist.", ephemeral=True)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await seed_default_watchlist(str(guild.id), DEFAULT_WATCHLIST)


async def setup(bot: commands.Bot):
    await bot.add_cog(Prices(bot))
