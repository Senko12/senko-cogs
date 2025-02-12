import discord
from redbot.core import commands
import aiohttp
import re

TENOR_REGEX = re.compile(r'https://tenor\.com/view/([\w-]+)')

class TenorLinkExtractor(commands.Cog):
    """Cog that extracts direct GIF links from Tenor URLs."""

    def __init__(self, bot):
        self.bot = bot

    async def get_tenor_gif(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    match = re.search(r'"(https://media\.tenor\.com/[^\"]+\.gif)"', html)
                    if match:
                        return match.group(1)
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        match = TENOR_REGEX.search(message.content)
        if match:
            direct_gif_url = await self.get_tenor_gif(message.content)
            if direct_gif_url:
                await message.channel.send(f"Direct GIF link: {direct_gif_url}")

async def setup(bot):
    await bot.add_cog(TenorLinkExtractor(bot))
