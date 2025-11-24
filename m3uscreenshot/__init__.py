from .screenshot import Screenshot

async def setup(bot):
    await bot.add_cog(Screenshot(bot))
