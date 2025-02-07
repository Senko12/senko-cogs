import discord
from discord.ext import commands
import feedparser

class BBCNews(commands.Cog):
    """Fetches the latest news from BBC."""

    def __init__(self, bot):
        self.bot = bot
        self.feed_url = "http://feeds.bbci.co.uk/news/rss.xml"

    @commands.command()
    async def bbcnews(self, ctx, count: int = 5):
        """Fetches the latest BBC News headlines (default: 5)."""
        if count < 1 or count > 10:
            await ctx.send("Please request between 1 and 10 headlines.")
            return

        feed = feedparser.parse(self.feed_url)
        if not feed.entries:
            await ctx.send("Could not retrieve BBC News at this time.")
            return

        headlines = "\n".join([f"**{entry.title}**\n{entry.link}" for entry in feed.entries[:count]])
        embed = discord.Embed(title="Latest BBC News", color=discord.Color.blue(), description=headlines)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BBCNews(bot))
