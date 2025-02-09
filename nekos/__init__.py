from redbot.core.bot import Red
from .nekos import ImageGif

async def setup(bot: Red):
    await bot.add_cog(ImageGif(bot))
