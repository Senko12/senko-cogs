import discord
from redbot.core import commands
import datetime
import pytz

class ChicagoTime(commands.Cog):
    """A cog to get the current time in Chicago."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def time(self, ctx, timezone: str = "America/Chicago", format_24: bool = False, country: str = None):
        """Gets the current time in Chicago."""
                if country:
        from tzwhere import tzwhere
        tz_finder = tzwhere.tzwhere()
        found_timezone = tz_finder.tzNameAt(*pytz.country_timezones(country))
        if found_timezone:
            timezone = found_timezone
    try:
        tz = pytz.timezone(timezone)
    except pytz.UnknownTimeZoneError:
        await ctx.send("Unknown timezone. Please provide a valid timezone.")
        return
            now = datetime.datetime.now(tz)
            if format_24:
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    else:
        formatted_time = now.strftime("%Y-%m-%d %I:%M:%S %p %Z")
        await ctx.send(f"Current time in {timezone}: {formatted_time}")

async def setup(bot):
    await bot.add_cog(ChicagoTime(bot))
