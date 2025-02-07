"""YouTube Downloader Cog for Red - Discord Bot"""

from .YouTubeDownloader import YouTubeDownloader

async def setup(bot):
    await bot.add_cog(YouTubeDownloader(bot))
