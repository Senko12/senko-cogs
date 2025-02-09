from .huggif import HugGif

async def setup(bot):
    await bot.add_cog(HugGif(bot))
