import discord
from redbot.core import commands
import aiohttp

BASE_URL = "https://someapi.com"  # Replace with the actual API base URL

class ImageGif(commands.Cog):
    """A cog to fetch GIFs and images from an API."""

    def __init__(self, bot):
        self.bot = bot

    async def fetch_json(self, endpoint):
        """Fetch JSON response from the API."""
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL + endpoint) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None

    @commands.command()
    async def eightball(self, ctx):
        """Get a random 8ball response."""
        data = await self.fetch_json("/8ball")
        if data:
            embed = discord.Embed(description=data["text"], color=discord.Color.blue())
            embed.set_image(url=data["image"])
            await ctx.send(embed=embed)
        else:
            await ctx.send("Couldn't contact the API right now...")

    @commands.command()
    async def img(self, ctx, category: str):
        """Fetch an image or GIF from a specified category."""
        categories = [
            "wallpaper", "ngif", "tickle", "feed", "gecg", "gasm", "slap",
            "avatar", "lizard", "waifu", "pat", "8ball", "kiss", "neko",
            "spank", "cuddle", "fox_girl", "hug", "smug", "goose", "woof"
        ]

        if category.lower() not in categories:
            await ctx.send(f"Invalid category! Available categories: {', '.join(categories)}")
            return

        data = await self.fetch_json(f"/img/{category.lower()}")
        if data:
            await ctx.send(data["url"])
        else:
            await ctx.send("Couldn't fetch an image right now...")

    @commands.command()
    async def owoify(self, ctx, *, text: str):
        """Owoify a given text."""
        data = await self.fetch_json(f"/owoify?text={discord.utils.escape_markdown(text)}")
        if data:
            await ctx.send(data["owo"])
        else:
            await ctx.send("Couldn't owoify the text right now...")

    @commands.command()
    async def cat(self, ctx):
        """Get a random cat image."""
        data = await self.fetch_json("/img/meow")
        if data:
            await ctx.send(data["url"])
        else:
            await ctx.send("Couldn't fetch a cat image right now...")

    @commands.command()
    async def textcat(self, ctx):
        """Get a random cat-related text."""
        data = await self.fetch_json("/cat")
        if data:
            await ctx.send(data["cat"])
        else:
            await ctx.send("Couldn't fetch a cat fact right now...")

    @commands.command()
    async def why(self, ctx):
        """Get a random 'why' question."""
        data = await self.fetch_json("/why")
        if data:
            await ctx.send(data["why"])
        else:
            await ctx.send("Couldn't fetch a 'why' question right now...")

    @commands.command()
    async def fact(self, ctx):
        """Get a random fact."""
        data = await self.fetch_json("/fact")
        if data:
            await ctx.send(data["fact"])
        else:
            await ctx.send("Couldn't fetch a fact right now...")

    @commands.command()
    async def name(self, ctx):
        """Get a random name."""
        data = await self.fetch_json("/name")
        if data:
            await ctx.send(data["name"])
        else:
            await ctx.send("Couldn't fetch a name right now...")

async def setup(bot):
    await bot.add_cog(ImageGif(bot))
