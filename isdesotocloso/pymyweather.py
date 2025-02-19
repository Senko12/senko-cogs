import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup
import re
import html

class SchoolClosureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def desoto(self, ctx):
        """
        Command to fetch the latest school closure notice from DeSoto County Schools website.
        """
        url = "https://www.desotocountyschools.org/"
        response = requests.get(url)
        
        if response.status_code != 200:
            await ctx.send("Failed to fetch the webpage.")
            return
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Search for the specific school closure message pattern
        closure_message_pattern = re.compile(r'<h3><strong>Due.*?</strong></h3>', re.IGNORECASE)
        
        # Look for all instances that match the pattern
        matches = closure_message_pattern.findall(str(soup))
        
        if matches:
            for match in matches:
                # Remove HTML tags and decode HTML entities
                clean_message = re.sub(r'<.*?>', '', match)
                clean_message = html.unescape(clean_message)
                await ctx.send(f"**School Closure Notice**: {clean_message}")
        else:
            await ctx.send("No school closure announcements found.")

def setup(bot):
    bot.add_cog(SchoolClosureCog(bot))
