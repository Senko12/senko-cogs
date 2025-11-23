import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path

import discord
from redbot.core import commands, checks

log = logging.getLogger("red.screenshot")


class Screenshot(commands.Cog):
    """Take a screenshot from configured M3U8 livestreams."""

    def __init__(self, bot):
        self.bot = bot
        self.streams = {}
        self.streams_file = Path(__file__).parent / "streams.json"
        self._load_streams()

    def _load_streams(self):
        """Load streams from streams.json in the same directory as this cog."""
        if not self.streams_file.exists():
            log.warning("streams.json not found at %s", self.streams_file)
            self.streams = {}
            return

        try:
            with self.streams_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            log.error("Failed to load streams.json: %s", e)
            self.streams = {}
            return

        # Expecting a flat name -> url mapping
        if isinstance(data, dict):
            self.streams = {str(k): str(v) for k, v in data.items()}
        else:
            log.error("streams.json should be a JSON object (name: url).")
            self.streams = {}

    @commands.command(name="scrn")
    async def scrn(self, ctx: commands.Context, nameofstream: str):
        """
        Take a screenshot from a configured M3U8 livestream.

        Usage: [p]scrn <nameofstream>
        Name must exist in streams.json (same folder as this cog).
        """
        name = nameofstream.strip()

        if not self.streams:
            await ctx.send(
                "I don't have any streams configured. "
                "Make sure `streams.json` exists and is valid."
            )
            return

        url = self.streams.get(name)
        if not url:
            # Try reloading in case the JSON was just edited
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
        await ctx.send(f"Grabbing a screenshot from `{name}`…")

        # Use ffmpeg to grab a single frame
        # Requires `ffmpeg` installed and available in PATH
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            tmp_path = tmp.name
            tmp.close()
        except Exception as e:
            log.error("Failed to create temporary file: %s", e)
            await ctx.send("I couldn't create a temporary file for the screenshot.")
            return

        try:
            # ffmpeg command:
            # ffmpeg -y -i <url> -frames:v 1 -q:v 2 <outfile>
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg",
                "-y",
                "-i",
                url,
                "-frames:v",
                "1",
                "-q:v",
                "2",
                tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            except asyncio.TimeoutError:
                proc.kill()
                await ctx.send("ffmpeg took too long to grab the screenshot (timed out).")
                return

            if proc.returncode != 0 or not os.path.exists(tmp_path):
                log.warning(
                    "ffmpeg failed (code %s). stderr: %s",
                    proc.returncode,
                    stderr.decode(errors="ignore") if stderr else "none",
                )
                await ctx.send(
                    "I couldn't grab a screenshot from that stream.\n"
                    "Make sure the URL is valid and reachable."
                )
                return

            file = discord.File(tmp_path, filename=f"{name}.jpg")
            await ctx.send(
                content=f"Here’s the screenshot for `{name}`:",
                file=file,
            )

        except FileNotFoundError:
            # ffmpeg not installed / not in PATH
            await ctx.send(
                "I couldn't run `ffmpeg`. Make sure it is installed "
                "and available in the system PATH."
            )
        except Exception as e:
            log.exception("Unexpected error while grabbing screenshot: %s", e)
            await ctx.send("Something went wrong while trying to grab the screenshot.")
        finally:
            # Clean up temp file
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass


async def setup(bot):
    await bot.add_cog(Screenshot(bot))
