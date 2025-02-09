import discord
from redbot.core import commands
import aiohttp

class HugGif(commands.Cog):
    """Sends a hug GIF from nekos.life API"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def nekohug(self, ctx, user: discord.Member = None):
        """Send a random hug GIF. Optionally mention a user."""
        url = "https://nekos.life/api/v2/img/hug"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await ctx.send("Couldn't fetch a hug GIF right now. Try again later.")
                    return
                data = await resp.json()
                gif_url = data.get("url")
                if not gif_url:
                    await ctx.send("API returned an invalid response.")
                    return

        embed = discord.Embed(color=discord.Color.pink())
        if user:
            embed.description = f"{ctx.author.mention} hugs {user.mention}!"
        else:
            embed.description = f"{ctx.author.mention} sends a virtual hug!"
        embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HugGif(bot))
