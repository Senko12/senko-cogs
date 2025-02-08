import discord
import yt_dlp
import os
import asyncio
from redbot.core import commands
from os import remove
from tempfile import NamedTemporaryFile
import ffmpeg  # This will now be ffmpeg-python

class YouTubeDownloader(commands.Cog):
    """Download and compress YouTube videos for Discord"""

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

    async def convert_to_webm(self, file_path: str) -> str:
        """Convert the downloaded file to WebM format and returns the new file path."""
        webm_file = file_path.rsplit('.', 1)[0] + ".webm"  # Change the extension to .webm
        try:
            print(f"Converting {file_path} to {webm_file}")

            # Ensure the paths are absolute
            file_path = os.path.abspath(file_path)
            webm_file = os.path.abspath(webm_file)

            # Probe the input file for its information using ffmpeg-python
            info = ffmpeg.probe(file_path)  # Now using ffmpeg.probe from ffmpeg-python
            duration = int(float(info["format"]["duration"]))
            video_bitrate = 60_000_000 / duration * 60 / 100
            audio_bitrate = 4_000_000 / duration * 75 / 100

            # Run FFmpeg to convert video to WebM format
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", file_path, "-c:v", "libvpx-vp9", "-b:v", str(video_bitrate),
                "-vf", "scale=1280:720", "-c:a", "libopus", "-b:a", str(audio_bitrate), webm_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(stderr.decode())
                return None

            return webm_file
        except Exception as e:
            print(f"Error converting to WebM: {e}")
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
            # If it's an MP3 download, send the audio file directly
            await ctx.send("Uploading audio file...")
            await ctx.send(file=discord.File(file_path))
            os.remove(file_path)  # Delete the original file after sending
            return

        # Convert video to WebM format
        await ctx.send("Converting to WebM...")
        webm_file = await self.convert_to_webm(file_path)

        if not webm_file or not os.path.exists(webm_file):
            return await ctx.send("Conversion to WebM failed.")

        await ctx.send("Uploading converted video...")
        await ctx.send(file=discord.File(webm_file))

        os.remove(file_path)  # Delete the original file after sending
        os.remove(webm_file)

async def setup(bot):
    await bot.add_cog(YouTubeDownloader(bot))
