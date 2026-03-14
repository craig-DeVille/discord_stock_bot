import asyncio
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, DEFAULT_WATCHLIST
from database.db import init_db, seed_default_watchlist

COGS = [
    "cogs.prices",
    "cogs.alerts",
    "cogs.subscriptions",
    "cogs.scheduler",
    "cogs.help",
]


class OilBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await init_db()
        for cog in COGS:
            await self.load_extension(cog)
        print("Cogs loaded. Type !sync in Discord to register slash commands.")

    async def on_ready(self):
        print(f"Logged in as {self.user} ({self.user.id})")
        for guild in self.guilds:
            await seed_default_watchlist(str(guild.id), DEFAULT_WATCHLIST)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            print(f"Slash commands synced to {guild.name}")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="oil prices"
            )
        )


bot = OilBot()


@bot.command(name="sync")
@commands.is_owner()
async def sync(ctx):
    await bot.tree.sync()
    await ctx.send("Slash commands synced.")


async def main():
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN not set in .env")
    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
