import discord
import yt_dlp
import subprocess
import os
import asyncio
import requests
from redbot.core import commands

# Filebin API details
BASE_URL = "https://filebin.net/api/v2"

# Function to upload the file to Filebin
def upload_file(bin_name, file_path, filename, custom_id=None):
    url = f"{BASE_URL}/{bin_name}/{filename}"
    headers = {}
    if custom_id:
        headers["cid"] = custom_id
    
    with open(file_path, 'rb') as file:
        response = requests.post(url, headers=headers, files={filename: file})
    
    if response.status_code == 201:
        return response.json().get('url')  # Returning the Filebin URL if the upload was successful
    else:
        print(f"Filebin upload failed: {response.status_code}, {response.text}")
        return None

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
            file_name = os.path.basename(file_path)
            bin_name = "your_bin_name"  # You can change this to a dynamic bin name if needed
            filebin_url = upload_file(bin_name, file_path, file_name)
            return filebin_url
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
        """Downloads a YouTube video or MP3. If MP4, uploads to Filebin if over 10MB."""
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

            await ctx.send("Checking if upload is needed...")
            file_size = os.path.getsize(file_path)

            if file_size > 10 * 1024 * 1024:  # If file is larger than 10MB, upload to Filebin
                filebin_url = await self.upload_to_filebin(file_path)
                if filebin_url:
                    await ctx.send(f"File uploaded to Filebin: {filebin_url}")
                    os.remove(file_path)  # Clean up the original file after upload
                else:
                    await ctx.send("Upload to Filebin failed.")
            else:
                # If file is smaller than 10MB, just send it
                await ctx.send("Uploading video...")
                await ctx.send(file=discord.File(file_path))
                os.remove(file_path)

        except Exception as e:
            await ctx.send("An error occurred during processing.")
            print(e)
            os.remove(file_path)
