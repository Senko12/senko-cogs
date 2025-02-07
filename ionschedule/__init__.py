from .ion_tv_schedule import IonTvSchedule

async def setup(bot):
    await bot.add_cog(IonTvSchedule(bot))
