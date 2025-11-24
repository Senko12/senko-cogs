import json
import logging
import subprocess
import tempfile
from pathlib import Path

import discord
import cv2
import numpy as np

from redbot.core import commands

log = logging.getLogger("red.screenshot")


class Screenshot(commands.Cog):
    """Take a screenshot from M3U8 livestreams without ffmpeg."""

    def __init__(self, bot):
        self.bot = bot
        self.streams = {}
        self.streams_file = Path(__file__).parent / "streams.json"
        self._load_streams()

    def _load_streams(self):
        """Load streams from streams.json."""
        if not self.streams_file.exists():
            log.warning("streams.json not found.")
            self.streams = {}
            return

        try:
            with self.streams_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.streams = {str(k): str(v) for k, v in data.items()}
        except Exception as e:
            log.error("Failed to load streams.json: %s", e)
            self.streams = {}

    @commands.command(name="scrn")
    async def scrn(self, ctx: commands.Context, nameofstream: str):
        """
        Take a screenshot from a configured M3U8 stream using Streamlink + OpenCV.

        Usage:
          [p]scrn <name>
        """
        name = nameofstream.strip()

        if not self.streams:
            await ctx.send("No streams configured in streams.json.")
            return

        url = self.streams.get(name)
        if not url:
            self._load_streams()
            url = self.streams.get(name)

        if not url:
            available = ", ".join(self.streams.keys()) or "None"
            await ctx.send(f"`{name}` not found. Available: {available}")
            return

        await ctx.send(f"Capturing screenshot from `{name}`…")
        await ctx.typing()

        try:
            # Use streamlink to pipe video to stdout
            cmd = [
                "streamlink",
                "--stdout",
                url,
                "best"
            ]

            # Open Streamlink process
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL
            )

            # OpenCV VideoCapture from pipe
            cap = cv2.VideoCapture(proc.stdout)

            if not cap.isOpened():
                proc.kill()
                await ctx.send("Failed to open stream — Streamlink returned no video.")
                return

            # Read ONE frame
            ret, frame = cap.read()
            cap.release()
            proc.kill()

            if not ret:
                await ctx.send("Could not read a frame from the stream.")
                return

            # Save JPEG to temp file
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            img_path = tmp.name
            tmp.close()

            cv2.imwrite(img_path, frame)

            file = discord.File(img_path, filename=f"{name}.jpg")
            await ctx.send(f"Screenshot from `{name}`:", file=file)

        except FileNotFoundError:
            await ctx.send("Streamlink is not installed or not in PATH.")
        except Exception as e:
            log.exception("Screenshot error: %s", e)
            await ctx.send("Something went wrong capturing the screenshot.")
