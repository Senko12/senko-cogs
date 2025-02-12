import discord
from redbot.core import commands
import aiohttp
import re

TENOR_REGEX = re.compile(r'https://tenor\.com/view/\w+')

class TenorLinkExtractor(commands.Cog):
    """Cog that extracts direct GIF links from Tenor URLs."""

    def __init__(self, bot):
        self.bot = bot

    async def get_tenor_gif(self, url):
        api_key = "YOUR_TENOR_API_KEY"  # Replace with a valid API key
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://g.tenor.com/v1/oembed?url={url}&key={api_key}") as resp:
                if resp.status == 200:
                    json_data = await resp.json()
                    gif_url = json_data.get("thumbnail_url")
                    if gif_url and gif_url.endswith(".gif"):
                        return gif_url
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        match = TENOR_REGEX.search(message.content)
        if match:
            tenor_url = match.group(0)
            direct_gif_url = await self.get_tenor_gif(tenor_url)
            if direct_gif_url:
                await message.channel.send(f"Direct GIF link: {direct_gif_url}")

async def setup(bot):
    await bot.add_cog(TenorLinkExtractor(bot))
