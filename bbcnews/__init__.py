from .bbcnews import BBCNews

async def setup(bot):
    await bot.add_cog(BBCNews(bot))
