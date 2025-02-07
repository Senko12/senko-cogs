import discord
from redbot.core import commands
import mss
import os

class Screenshot(commands.Cog):
    """A cog to take a screenshot and send it."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def screenshot(self, ctx):
        """Takes a screenshot and sends it."""
        screenshot_path = "screenshot.png"

        try:
            with mss.mss() as sct:
                sct.shot(output=screenshot_path)

            # Send the screenshot as an attachment
            file = discord.File(screenshot_path)
            await ctx.send("Here is the screenshot:", file=file)

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

        finally:
            # Cleanup
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)

async def setup(bot):
    await bot.add_cog(Screenshot(bot))
