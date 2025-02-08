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
        await self.fetch_news(ctx, count)

    @app_commands.command(name="bbcnews")
    async def slash_bbcnews(self, interaction: discord.Interaction, count: int = 5):
        """Fetches the latest BBC News headlines (default: 5)."""
        await self.fetch_news(interaction, count, slash=True)

    async def fetch_news(self, ctx_or_interaction, count: int, slash: bool = False):
        if count < 1 or count > 10:
            msg = "Please request between 1 and 10 headlines."
            if slash:
                await ctx_or_interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx_or_interaction.send(msg)
            return

        feed = feedparser.parse(self.feed_url)
        if not feed.entries:
            msg = "Could not retrieve BBC News at this time."
            if slash:
                await ctx_or_interaction.response.send_message(msg, ephemeral=True)
            else:
                await ctx_or_interaction.send(msg)
            return

        headlines = "\n".join([f"**{entry.title}**\n{entry.link}" for entry in feed.entries[:count]])
        embed = discord.Embed(title="Latest BBC News", color=discord.Color.blue(), description=headlines)

        if slash:
            await ctx_or_interaction.response.send_message(embed=embed)
        else:
            await ctx_or_interaction.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BBCNews(bot))
