import discord
import yt_dlp
import subprocess
import os
import asyncio
import requests
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
            # Default: Force MP4 format if video
            ydl_opts = {
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",  # Always prefer MP4
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

    async def upload_to_filebin(self, file_path: str) -> str:
        """Uploads the file to Filebin and returns the filebin URL."""
        try:
            with open(file_path, 'rb') as f:
                response = requests.post("https://filebin.net", files={"file": f})
                if response.status_code == 200:
                    return response.text.strip()  # The URL will be returned as plain text
                else:
                    print("Filebin upload failed:", response.status_code)
                    return None
        except Exception as e:
            print(f"Error uploading to Filebin: {e}")
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
        """Downloads a YouTube video or MP3. If MP4, uploads to Filebin if larger than 10MB."""
        audio_only = filetype.lower() == "mp3"

        await ctx.send(f"Downloading {filetype.upper()}...")

        # Download the video or audio
        file_path = await self.download_youtube_video(url, audio_only, filetype)

        if not file_path:
            return await ctx.send("Failed to download.")

        # Debug: Show debug info if enabled
        if debug:
            debug_info = await self.debug_info(file_path)
            if debug_info:
                await ctx.send(f"Debug Info:\n{debug_info}")
        
        try:
            # Check if file is larger than 10MB
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)

            if file_size_mb > 10:
                # Upload to Filebin if larger than 10MB
                await ctx.send(f"File is {file_size_mb:.2f} MB, uploading to Filebin...")
                filebin_url = await self.upload_to_filebin(file_path)
                if filebin_url:
                    await ctx.send(f"File uploaded successfully! You can download it from here: {filebin_url}")
                else:
                    await ctx.send("Failed to upload to Filebin.")
            else:
                # If it's not too large, send it directly
                if audio_only:
                    await ctx.send("Uploading audio file...")
                    await ctx.send(file=discord.File(file_path))
                else:
                    await ctx.send("Uploading video file...")
                    await ctx.send(file=discord.File(file_path))

            # Clean up downloaded file
            os.remove(file_path)
        except Exception as e:
            await ctx.send("An error occurred during processing.")
            print(e)
            if os.path.exists(file_path):
                os.remove(file_path)

async def setup(bot):
    await bot.add_cog(YouTubeDownloader(bot))
