import requests
import xml.etree.ElementTree as ET
from redbot.core import commands
import os
import subprocess

class IonTvSchedule(commands.Cog):
    """Cog to fetch and display ION TV schedule."""

    SCRIPT_URL = "https://raw.githubusercontent.com/daniel-widrick/zap2it-GuideScraping/main/zap2it-GuideScrape.py"
    OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "xmlguide.xmltv")
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), "zap2itconfig.ini")
    DEFAULT_CONFIG = os.path.join(os.path.dirname(__file__), "config.ini.dist")

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ionschedule(self, ctx):
        """Fetches and displays the ION TV schedule for the day."""
        await ctx.send("Fetching ION TV schedule...")

        # Download script
        script_path = os.path.join(os.path.dirname(__file__), "zap2it-GuideScrape.py")
        try:
            response = requests.get(self.SCRIPT_URL, timeout=10)
            response.raise_for_status()  # Raise an error if the request failed
            with open(script_path, "w", encoding="utf-8") as script_file:
                script_file.write(response.text)
        except requests.exceptions.RequestException as e:
            await ctx.send(f"Error downloading the guide scraper script: {e}")
            return

        # Ensure config file exists in the same directory as the script
        if not os.path.exists(self.CONFIG_FILE):
            if os.path.exists(self.DEFAULT_CONFIG):
                os.system(f'cp "{self.DEFAULT_CONFIG}" "{self.CONFIG_FILE}"')  # Copy default config
            else:
                await ctx.send("Error: Missing zap2itconfig.ini and config.ini.dist. Please provide these files.")
                return

        # Run script using subprocess
        try:
            subprocess.run(["python", script_path], check=True)
        except subprocess.CalledProcessError:
            await ctx.send("Error running the guide scraper script.")
            return

        # Check if XML file was created
        if not os.path.exists(self.OUTPUT_FILE):
            await ctx.send("Error: XML guide file not found. The script may have failed.")
            return

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
