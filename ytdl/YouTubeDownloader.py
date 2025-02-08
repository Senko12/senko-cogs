import discord
import yt_dlp
import subprocess
import os
import asyncio
from redbot.core import commands

class YouTubeDownloader(commands.Cog):
    """Download and compress YouTube videos for Discord"""

    def __init__(self, bot):
        self.bot = bot

    async def download_youtube_video(self, url: str, audio_only: bool = False) -> str:
        """Downloads a YouTube video or audio and returns the file path."""
        output_path = "downloads"
        os.makedirs(output_path, exist_ok=True)

        # yt-dlp options to download audio or video
        ydl_opts = {
            "format": "bestaudio/best" if audio_only else "mp4",  # Download best audio if audio_only is True
            "outtmpl": f"{output_path}/%(title)s-%(uploader)s.%(ext)s",  # Let yt-dlp decide the extension
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}] if audio_only else []  # Explicitly convert audio to mp3
        }
        
        # Download the video or audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info_dict)

    async def compress_video(self, file_path: str) -> str:
        """Compresses the video using FFmpeg and returns the new file path."""
        compressed_file = file_path + ".crushed.mp4"

        try:
            process = await asyncio.create_subprocess_exec(
                "python3", "compress.py", file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(stderr.decode())
                return None

            return compressed_file
        except Exception as e:
            print(f"Compression error: {e}")
            return None

    @commands.command()
    async def ytdl(self, ctx, url: str, filetype: str = "mp4"):
        """Downloads a YouTube video or MP3. If MP4, compresses before sending."""
        audio_only = filetype.lower() == "mp3"

        await ctx.send(f"Downloading {filetype.upper()}...")

        file_path = await self.download_youtube_video(url, audio_only)

        if not file_path:
            return await ctx.send("Failed to download.")

        if audio_only:
            await ctx.send("Uploading audio file...")
            await ctx.send(file=discord.File(file_path))
            os.remove(file_path)
            return

        await ctx.send("Compressing video...")
        compressed_file = await self.compress_video(file_path)

        if not compressed_file or not os.path.exists(compressed_file):
            return await ctx.send("Compression failed.")

        await ctx.send("Uploading compressed video...")
        await ctx.send(file=discord.File(compressed_file))

        os.remove(file_path)
        os.remove(compressed_file)

async def setup(bot):
    await bot.add_cog(YouTubeDownloader(bot))
