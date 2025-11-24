import asyncio
import json
import logging
import os
from pathlib import Path

import discord
from redbot.core import commands

log = logging.getLogger("red.screenshot")


class Screenshot(commands.Cog):
    """Take a screenshot from M3U8 livestreams using VLC."""

    def __init__(self, bot):
        self.bot = bot
        self.streams = {}
        self.streams_file = Path(__file__).parent / "streams.json"
        self.save_dir = Path("/Users/konata/Pictures")
        self._ensure_save_dir()
        self._load_streams()

    def _ensure_save_dir(self):
        try:
            self.save_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            log.error("Could not create save directory %s: %s", self.save_dir, e)

    def _load_streams(self):
        """Load streams from streams.json."""
        if not self.streams_file.exists():
            log.warning("streams.json not found at %s", self.streams_file)
            self.streams = {}
            return

        try:
            with self.streams_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.streams = {str(k): str(v) for k, v in data.items()}
            else:
                log.error("streams.json must be a simple object of {name: url}.")
                self.streams = {}
        except Exception as e:
            log.error("Failed to load streams.json: %s", e)
            self.streams = {}

    async def _run_vlc_capture(self, url: str, prefix: str) -> Path | None:
        """
        Run VLC to capture a single frame to self.save_dir with given prefix.
        Returns the Path of the created file, or None on failure.
        """

        # Clean up any previous files with the same prefix
        for f in self.save_dir.glob(prefix + "*"):
            try:
                f.unlink()
            except Exception:
                pass

        # Build VLC command:
        # - headless, quiet, use scene video filter, dump 1 frame, quit
        cmd = [
            "vlc",
            url,
            "--intf", "dummy",
            "--quiet",
            "--no-video-title-show",
            "--video-filter=scene",
            "--vout", "dummy",
            "--scene-path", str(self.save_dir),
            "--scene-prefix", prefix,
            "--scene-format", "png",
            "--scene-ratio", "1",
            "--scene-replace",
            "--run-time", "5",
            "vlc://quit",
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

            try:
                await asyncio.wait_for(proc.communicate(), timeout=25)
            except asyncio.TimeoutError:
                proc.kill()
                log.warning("VLC timed out while capturing frame.")
                return None

            # Look for any file created with that prefix
            files = sorted(self.save_dir.glob(prefix + "*"))
            if not files:
                log.warning("VLC finished but no screenshot file was found.")
                return None

            return files[0]

        except FileNotFoundError:
            # VLC not installed / not in PATH
            log.error("vlc executable not found in PATH.")
            raise
        except Exception as e:
            log.exception("Error running VLC: %s", e)
            return None

    @commands.command(name="scrn")
    async def scrn(self, ctx: commands.Context, nameofstream: str):
        """
        Take a screenshot from a configured M3U8 stream using VLC.

        Usage:
          [p]scrn <nameofstream>
        """
        name = nameofstream.strip()

        if not self.streams:
            await ctx.send("No streams configured. Make sure `streams.json` exists and is valid.")
            return

        url = self.streams.get(name)
        if not url:
            # Try reloading in case file was edited
            self._load_streams()
            url = self.streams.get(name)

        if not url:
            available = ", ".join(sorted(self.streams.keys())) or "None"
            await ctx.send(
                f"I couldn't find a stream named `{name}` in `streams.json`.\n"
                f"Available names: `{available}`"
            )
            return

        await ctx.typing()
        await ctx.send(f"Capturing screenshot from `{name}` via VLC…")

        prefix = f"scrn_{name}_"

        try:
            img_path = await self._run_vlc_capture(url, prefix)
        except FileNotFoundError:
            await ctx.send(
                "I couldn't run `vlc`. Make sure VLC is installed and `vlc` is available in your system PATH."
            )
            return

        if img_path is None or not img_path.exists():
            await ctx.send("I couldn't capture a screenshot from that stream.")
            return

        # Send the screenshot
        try:
            file = discord.File(str(img_path), filename=img_path.name)
            await ctx.send(f"Screenshot from `{name}`:", file=file)
        finally:
            # Delete file after sending
            try:
                img_path.unlink()
            except Exception as e:
                log.warning("Could not delete screenshot file %s: %s", img_path, e)
