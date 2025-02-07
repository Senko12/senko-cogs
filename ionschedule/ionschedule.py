import requests
import xml.etree.ElementTree as ET
from redbot.core import commands
import os

class IonTvSchedule(commands.Cog):
    """Cog to fetch and display ION TV schedule."""

    SCRIPT_URL = "https://raw.githubusercontent.com/daniel-widrick/zap2it-GuideScraping/refs/heads/main/zap2it-GuideScrape.py"
    OUTPUT_FILE = "xmlguide.xmltv"

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ionschedule(self, ctx):
        """Fetches and displays the ION TV schedule for the day."""
        await ctx.send("Fetching ION TV schedule...")
        
        # Download script
        script_path = "zap2it-GuideScrape.py"
        response = requests.get(self.SCRIPT_URL)
        with open(script_path, "w", encoding="utf-8") as script_file:
            script_file.write(response.text)
        
        # Run script
        os.system(f"python {script_path}")
        
        # Parse XMLTV file
        tree = ET.parse(self.OUTPUT_FILE)
        root = tree.getroot()
        schedule = []

        for program in root.findall("programme"):
            channel = program.get("channel")
            if "ION" in channel:
                title = program.find("title").text
                start = program.get("start")
                stop = program.get("stop")
                schedule.append(f"{start} - {stop}: {title}")
        
        if schedule:
            await ctx.send("\n".join(schedule))
        else:
            await ctx.send("No ION TV schedule found.")
