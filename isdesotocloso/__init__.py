from .closorunner import PythonScriptCog

async def setup(bot):
    # Ensure the cog is added properly and await the async method
    await bot.add_cog(PythonScriptCog(bot))
