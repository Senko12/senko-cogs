from .bbc_news_cog import BBCNews

async def setup(bot):
    await bot.add_cog(BBCNews(bot))
