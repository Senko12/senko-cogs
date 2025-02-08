import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

class BBCNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Function to fetch the latest BBC News
    async def fetch_bbc_news(self):
        url = 'https://newsapi.org/v2/top-headlines'
        params = {
            'apiKey': 'YOUR_NEWSAPI_KEY',  # You'll need to get a NewsAPI key
            'sources': 'bbc-news',
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = data['articles']
                    return articles
                else:
                    return None

    # Slash command to get the latest BBC news
    @app_commands.command(name="bbc_news", description="Get the latest news from BBC")
    async def bbc_news(self, interaction: discord.Interaction):
        articles = await self.fetch_bbc_news()
        if articles:
            embed = discord.Embed(
                title="Latest BBC News",
                description="Here are the top stories from BBC News:",
                color=discord.Color.blue()
            )

            for article in articles[:5]:  # Get top 5 latest articles
                embed.add_field(
                    name=article['title'],
                    value=f"[Read more]({article['url']})",
                    inline=False
                )

            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Sorry, I couldn't fetch the news at the moment.")

# Setup the cog
async def setup(bot):
    await bot.add_cog(BBCNews(bot))
