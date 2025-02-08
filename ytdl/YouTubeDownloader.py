import discord
import yt_dlp
import subprocess
import os
import asyncio
from redbot.core import commands

class YouTubeDownloader(commands.Cog):
    """Download YouTube videos and convert to MP3 or MP4"""

    def __init__(self, bot):
        self.bot = bot

    async def download_youtube_video(self, url: str, audio_only: bool = False) -> str:
        """Downloads a YouTube video or audio and returns the file path."""
        output_path = "Downloads"
        os.makedirs(output_path, exist_ok=True)

        if audio_only:
            # Download only audio in the best quality
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{output_path}/%(title)s.%(ext)s",
            }
        else:
            # Download video as MP4
            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "outtmpl": f"{output_path}/%(title)s.%(ext)s",
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info_dict)

    async def convert_to_mp3(self, file_path: str) -> str:
        """Convert the downloaded file to MP3 format using FFmpeg and returns the new file path."""
        mp3_file = file_path.rsplit('.', 1)[0] + ".mp3"  # Change the extension to .mp3
        try:
            print(f"Converting {file_path} to {mp3_file}")

            # Ensure the paths are absolute
            file_path = os.path.abspath(file_path)
            mp3_file = os.path.abspath(mp3_file)

            # Run FFmpeg to convert audio file
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", file_path, "-vn", "-acodec", "libmp3lame", mp3_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(stderr.decode())
                return None

            return mp3_file
        except Exception as e:
            print(f"Error converting to MP3: {e}")
            return None

    @commands.command()
    async def ytdl(self, ctx, url: str, filetype: str = "mp4"):
        """Downloads a YouTube video or MP3. Converts video to MP4 with audio and h264 encoding."""
        audio_only = filetype.lower() == "mp3"

        await ctx.send(f"Downloading {filetype.upper()}...")

        file_path = await self.download_youtube_video(url, audio_only)

        if not file_path:
            return await ctx.send("Failed to download.")

        if audio_only:
            # If it's an MP3 download, convert if needed
            if not file_path.endswith(".mp3"):
                mp3_file = await self.convert_to_mp3(file_path)
                if not mp3_file:
                    return await ctx.send("Failed to convert to MP3.")
                await ctx.send("Uploading MP3 file...")
                await ctx.send(file=discord.File(mp3_file))
                os.remove(mp3_file)  # Delete the MP3 after sending
            else:
                await ctx.send("Uploading audio file...")
                await ctx.send(file=discord.File(file_path))
            
            # Delete the original file after MP3 is uploaded
            os.remove(file_path)
            return

        # Convert video to MP4 with h264 video codec and MP3 audio codec
        mp4_file = file_path.rsplit('.', 1)[0] + "_converted.mp4"
        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-i", file_path, "-vcodec", "h264", "-acodec", "mp3", mp4_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(stderr.decode())
            return await ctx.send("Failed to convert video.")

        await ctx.send("Uploading converted video...")
        await ctx.send(file=discord.File(mp4_file))

        os.remove(file_path)  # Delete the original file after sending
        os.remove(mp4_file)   # Delete the converted file after sending

async def setup(bot):
    await bot.add_cog(YouTubeDownloader(bot))
