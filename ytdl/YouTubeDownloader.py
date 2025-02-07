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
        format_type = "mp3" if audio_only else "mp4"
        ydl_opts = {
            "format": "bestaudio" if audio_only else "mp4",
            "outtmpl": f"{output_path}/%(title)s.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }] if audio_only else []
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info_dict).replace(".webm", f".{format_type}")

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

            if not os.path.exists(compressed_file) or os.stat(compressed_file).st_size == 0:
                print("Error: Output file not created or is empty.")
                return None

            return compressed_file
        except Exception as e:
            print(f"Compression error: {e}")
            return None

    @commands.command()
    async def ytdl(self, ctx, url: str, option: str = None):
        """Downloads, optionally compresses, and sends a YouTube video or audio."""
        audio_only = option == "-mp3"
        compress = option == "-compress"
        
        await ctx.send("Downloading...")
        file_path = await self.download_youtube_video(url, audio_only)

        if not file_path:
            return await ctx.send("Failed to download.")

        if audio_only:
            await ctx.send("Uploading audio file...")
            await ctx.send(file=discord.File(file_path))
        else:
            file_size = os.stat(file_path).st_size / (1024 * 1024)  # Convert bytes to MB
            if file_size > 10 and not compress:
                return await ctx.send("File is over 10MB. Run the command again with `-compress` to compress it.")
            
            if compress:
                await ctx.send("Compressing video... (this takes a while)")
                compressed_file = await self.compress_video(file_path)
                if not compressed_file or not os.path.exists(compressed_file):
                    return await ctx.send("Compression failed.")
                await ctx.send("Uploading compressed video...")
                await ctx.send(file=discord.File(compressed_file))
                os.remove(compressed_file)
            else:
                await ctx.send("Uploading video file...")
                await ctx.send(file=discord.File(file_path))
        
        os.remove(file_path)

async def setup(bot):
    await bot.add_cog(YouTubeDownloader(bot))
