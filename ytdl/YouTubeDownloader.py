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

    async def convert_to_mp3(self, file_path: str) -> str:
        """Converts the downloaded file to MP3 format using FFmpeg and returns the new file path."""
        mp3_file = file_path.rsplit('.', 1)[0] + ".mp3"  # Change extension to .mp3
        try:
            # Log the file paths for debugging
            print(f"Converting {file_path} to {mp3_file}")

            # Ensure the paths are absolute
            file_path = os.path.abspath(file_path)
            mp3_file = os.path.abspath(mp3_file)

            # Run FFmpeg conversion with quoted paths to handle spaces
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", f'"{file_path}"', f'"{mp3_file}"',
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

    async def compress_video(self, file_path: str) -> str:
        """Compresses the video using FFmpeg and returns the new file path."""
        compressed_file = file_path + ".crushed.mp4"

        try:
            # Ensure paths are absolute and quoted
            file_path = os.path.abspath(file_path)
            compressed_file = os.path.abspath(compressed_file)

            process = await asyncio.create_subprocess_exec(
                "python3", "compress.py", f'"{file_path}"',
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

        await ctx.send("Compressing video...")
        compressed_file = await self.compress_video(file_path)

        if not compressed_file or not os.path.exists(compressed_file):
            return await ctx.send("Compression failed.")

        await ctx.send("Uploading compressed video...")
        await ctx.send(file=discord.File(compressed_file))

        os.remove(file_path)  # Delete the original file after sending
        os.remove(compressed_file)

async def setup(bot):
    await bot.add_cog(YouTubeDownloader(bot))
