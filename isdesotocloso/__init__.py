from .pymyweather import SchoolClosureCog

async def setup(bot):
    # Ensure the cog is added properly as a coroutine
    await bot.add_cog(SchoolClosureCog(bot))
