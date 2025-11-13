from .streamrelay import StreamRelay

async def setup(bot):
    await bot.add_cog(StreamRelay(bot))
