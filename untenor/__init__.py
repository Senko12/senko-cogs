from .untenor import TenorLinkExtractor

async def setup(bot):
    await bot.add_cog(TenorLinkExtractor(bot))
