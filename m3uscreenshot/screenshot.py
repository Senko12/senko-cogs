import asyncio
import json
import logging
import os
import shutil
import tempfile
from glob import glob
from pathlib import Path

import discord
from redbot.core import commands

log = logging.getLogger("red.screenshot")


class Screenshot(commands.Cog):
    """Take a screenshot from configured M3U8 livestreams using VLC."""

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

        if isinstance(data, dict):
            self.streams = {str(k): str(v) for k, v in data.items()}
        else:
            log.error("streams.json should be a simple JSON object: {name: url}.")
            self.streams = {}

    @staticmethod
    def _pick_vlc_binary() -> str | None:
        """Try to find a VLC binary (cvlc preferred, then vlc)."""
        from shutil import which

        for candidate in ("cvlc", "vlc"):
            if which(candidate):
                return candidate
        return None

    async def _capture_with_vlc(self, url: str, name: str) -> str | None:
        """
        Use VLC to capture a single screenshot from the given URL.

        Returns path to the screenshot file, or None on failure.
        """
        vlc_bin = self._pick_vlc_binary()
        if not vlc_bin:
            raise FileNotFoundError("No VLC binary (cvlc or vlc) found in PATH.")

        # Temporary directory for VLC snapshots
        tmpdir = tempfile.mkdtemp(prefix="vlcshot_")
        prefix = f"{name}_"

        # VLC scene filter settings:
        # -I dummy            : no UI
        # --video-filter=scene: enable snapshotting
        # --scene-format=png  : PNG output
        # --scene-prefix=...  : filename prefix
        # --scene-path=...    : output directory
        # --scene-ratio=1     : take a frame every 1 frame (first available)
        # --scene-replace     : overwrite instead of accumulating
        # --run-time=3        : run a few seconds
        # --play-and-exit     : quit when done
        cmd = [
            vlc_bin,
            "-I",
            "dummy",
            url,
            "--video-filter=scene",
            "--scene-format=png",
            f"--scene-prefix={prefix}",
            f"--scene-path={tmpdir}",
            "--scene-ratio=1",
            "--scene-replace",
            "--no-audio",
            "--no-video-title-show",
            "--run-time=3",
            "--play-and-exit",
        ]

        log.debug("Running VLC command: %s", " ".join(cmd))

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            except asyncio.TimeoutError:
                proc.kill()
                log.warning("VLC process timed out.")
                shutil.rmtree(tmpdir, ignore_errors=True)
                return None

            if proc.returncode != 0:
                log.warning(
                    "VLC exited with code %s. stderr: %s",
                    proc.returncode,
                    (stderr or b"").decode(errors="ignore"),
                )
                shutil.rmtree(tmpdir, ignore_errors=True)
                return None

            # Look for snapshot files
            pattern = os.path.join(tmpdir, f"{prefix}*.png")
            files = glob(pattern)

            if not files:
                log.warning("VLC did not produce any snapshot files in %s", tmpdir)
                shutil.rmtree(tmpdir, ignore_errors=True)
                return None

            # Pick the newest file (just in case)
            shot_path = max(files, key=os.path.getmtime)

            # Move to a more stable temp file (so we can delete tmpdir safely)
            final_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            final_path = final_tmp.name
            final_tmp.close()

            shutil.move(shot_path, final_path)
            shutil.rmtree(tmpdir, ignore_errors=True)

            return final_path

        except FileNotFoundError:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise
        except Exception:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise

    @commands.command(name="scrn")
    async def scrn(self, ctx: commands.Context, nameofstream: str):
        """
        Take a screenshot from a configured M3U8 livestream using VLC.

        Usage:
          [p]scrn <nameofstream>
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
            # Try reloading in case user just edited the JSON
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
        await ctx.send(f"Grabbing a screenshot from `{name}` using VLC…")

        try:
            shot_path = await self._capture_with_vlc(url, name)
            if not shot_path or not os.path.exists(shot_path):
                await ctx.send(
                    "I couldn't capture a screenshot from that stream.\n"
                    "Make sure VLC is installed and the URL is reachable."
                )
                return

            file = discord.File(shot_path, filename=f"{name}.png")
            await ctx.send(
                content=f"Here’s the screenshot for `{name}`:",
                file=file,
            )

        except FileNotFoundError:
            await ctx.send(
                "I couldn't run VLC. Make sure `cvlc` or `vlc` is installed "
                "and available in the system PATH."
            )
        except Exception as e:
            log.exception("Unexpected error while grabbing screenshot: %s", e)
            await ctx.send("Something went wrong while trying to grab the screenshot.")
        finally:
            # shot_path is already in a NamedTemporaryFile; clean it if it exists
            try:
                if "shot_path" in locals() and shot_path and os.path.exists(shot_path):
                    os.remove(shot_path)
            except Exception:
                pass
