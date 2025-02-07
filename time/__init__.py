from .chicago_time_cog import ChicagoTime

async def setup(bot):
    await bot.add_cog(ChicagoTime(bot))
