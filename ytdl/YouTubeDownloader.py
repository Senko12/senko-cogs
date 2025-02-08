from redbot.core import commands

class YouTubeDownloader(commands.Cog):
    """Download and compress YouTube videos for Discord"""

    def __init__(self, bot):
        self.bot = bot
@@ -17,13 +17,11 @@ async def download_youtube_video(self, url: str, audio_only: bool = False) -> st
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
@@ -33,69 +31,68 @@ async def download_youtube_video(self, url: str, audio_only: bool = False) -> st
            info_dict = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info_dict)

    async def compress_video(self, file_path: str) -> str:
        """Compress the video using FFmpeg with specific parameters and returns the new file path."""
        compressed_file = file_path.rsplit('.', 1)[0] + "_compressed.mp4"
        try:
            # Run FFmpeg with the given compression command
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", file_path, "-n", "-fs", "7950000", "-fpsmax", "60", 
                "-s", "676x380", "-b:a", "90000", "-b:v", "400000", compressed_file,
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
