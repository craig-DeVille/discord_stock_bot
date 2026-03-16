import re

import discord
from discord.ext import commands

from database.db import check_link_exists, record_link

URL_PATTERN = re.compile(r"https?://[^\s<>\"']+")
SCROLL_EMOJI = "\U0001f4dc"  # 📜


def _normalize(url: str) -> str:
    return url.rstrip("/")


class Scroll(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        urls = [_normalize(u) for u in URL_PATTERN.findall(message.content)]
        if not urls:
            return

        channel_id = str(message.channel.id)
        duplicate_of = None

        for url in urls:
            original_msg_id = await check_link_exists(channel_id, url)
            if original_msg_id and duplicate_of is None:
                duplicate_of = original_msg_id

        # Record all new URLs (only inserts if not already there)
        for url in urls:
            await record_link(channel_id, url, str(message.id))

        if duplicate_of:
            try:
                await message.add_reaction(SCROLL_EMOJI)
            except discord.HTTPException:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Scroll(bot))
