import discord
import yt_dlp
import subprocess
import os
import asyncio
from redbot.core import commands

class YouTubeDownloader(commands.Cog):
    """Download and process YouTube videos for Discord"""

    def __init__(self, bot):
        self.bot = bot

    async def download_youtube_video(self, url: str, audio_only: bool = False, filetype: str = "mp4") -> str:
        """Downloads a YouTube video or audio and returns the file path."""
        output_path = "Downloads"
        os.makedirs(output_path, exist_ok=True)

        if audio_only:
            # Download the best audio only (convert to MP3 later)
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{output_path}/%(title)s.%(ext)s",
                "noplaylist": True,  # Ensure single video, not playlist
            }
        else:
            if filetype.lower() == "mp4":
                # Force MP4 format by filtering out non-MP4 formats
                ydl_opts = {
                    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
                    "outtmpl": f"{output_path}/%(title)s.%(ext)s",
                    "noplaylist": True,  # Ensure single video, not playlist
                }
            else:
                # Default to best quality video if not MP4
                ydl_opts = {
                    "format": "bestvideo+bestaudio/best",
                    "outtmpl": f"{output_path}/%(title)s.%(ext)s",
                    "noplaylist": True,  # Ensure single video, not playlist
                }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info_dict)
        except yt_dlp.DownloadError as e:
            print(f"Download error: {e}")
            return None

    async def convert_to_mp3(self, file_path: str) -> str:
        """Convert the downloaded file to MP3 format using FFmpeg and return the new file path."""
        mp3_file = file_path.rsplit('.', 1)[0] + ".mp3"
        try:
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", file_path, "-vn", "-acodec", "libmp3lame", "-q:a", "0", mp3_file,
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
        """Compress the video using FFmpeg and return the new file path."""
        compressed_file = file_path.rsplit('.', 1)[0] + "_compressed.mp4"
        try:
            if os.path.getsize(file_path) <= 10 * 1024 * 1024:
                return file_path

            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", file_path, "-b:a", "90000", "-b:v", "400000", compressed_file,
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

    async def debug_info(self, file_path: str):
        """Prints the debug info: filename, size, and format."""
        try:
            filename = os.path.basename(file_path)
            size = os.path.getsize(file_path)
            size_mb = size / (1024 * 1024)
            file_format = file_path.split('.')[-1].upper()

            return f"Filename: {filename}\nSize: {size_mb:.2f} MB\nFormat: {file_format}"
        except Exception as e:
            print(f"Error getting debug info: {e}")
            return None

    @commands.command()
    async def ytdl(self, ctx, url: str, filetype: str = "mp4", debug: bool = False):
        """Downloads a YouTube video or MP3. If MP4, compresses before sending."""
        audio_only = filetype.lower() == "mp3"

        await ctx.send(f"Downloading {filetype.upper()}...")
        file_path = await self.download_youtube_video(url, audio_only, filetype)

        if not file_path:
            return await ctx.send("Failed to download.")

        try:
            if debug:
                debug_info = await self.debug_info(file_path)
                if debug_info:
                    await ctx.send(f"Debug Info:\n{debug_info}")

            if audio_only:
                if not file_path.endswith(".mp3"):
                    mp3_file = await self.convert_to_mp3(file_path)
                    if not mp3_file:
                        return await ctx.send("Failed to convert to MP3.")
                    await ctx.send("Uploading MP3 file...")
                    await ctx.send(file=discord.File(mp3_file))
                    os.remove(mp3_file)
                else:
                    await ctx.send("Uploading audio file...")
                    await ctx.send(file=discord.File(file_path))
                os.remove(file_path)
                return

            await ctx.send("Checking if compression is needed...")
            compressed_file = await self.compress_video(file_path)

            if not compressed_file or not os.path.exists(compressed_file):
                return await ctx.send("Compression failed.")

            if debug:
                debug_info = await self.debug_info(compressed_file)
                if debug_info:
                    await ctx.send(f"Debug Info:\n{debug_info}")

            await ctx.send("Uploading video...")
            await ctx.send(file=discord.File(compressed_file))

            os.remove(file_path)
            if compressed_file != file_path:
                os.remove(compressed_file)
        except Exception as e:
            await ctx.send("An error occurred during processing.")
            print(e)
            os.remove(file_path)
            if os.path.exists(compressed_file):
                os.remove(compressed_file)

async def setup(bot):
    await bot.add_cog(YouTubeDownloader(bot))
