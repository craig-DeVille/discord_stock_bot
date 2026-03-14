import asyncio
import discord
from discord.ext import commands

from config import DISCORD_TOKEN, DEFAULT_WATCHLIST, ALLOWED_GUILDS
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

    async def on_ready(self):
        print(f"Logged in as {self.user} ({self.user.id})")
        for guild in self.guilds:
            if guild.id not in ALLOWED_GUILDS:
                print(f"Leaving unauthorized guild: {guild.name} ({guild.id})")
                await guild.leave()
                continue
            await self._sync_guild(guild)
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="oil prices"
            )
        )

    async def on_guild_join(self, guild: discord.Guild):
        if guild.id not in ALLOWED_GUILDS:
            print(f"Leaving unauthorized guild: {guild.name} ({guild.id})")
            await guild.leave()
            return
        await self._sync_guild(guild)

    async def _sync_guild(self, guild: discord.Guild):
        if guild.id not in ALLOWED_GUILDS:
            return
        await seed_default_watchlist(str(guild.id), DEFAULT_WATCHLIST)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print(f"Synced commands to {guild.name}")


async def main():
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN not set in .env")
    bot = OilBot()
    async with bot:
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
