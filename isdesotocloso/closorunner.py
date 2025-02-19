import discord
from discord.ext import commands
import subprocess

class PythonScriptCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="desoto", help="Checks DeSoto's website for closure announcements")
    async def run_closocode(self, ctx):
        try:
            # Run the Python script using subprocess
            result = subprocess.run(["python", "theclosocode.py"], capture_output=True, text=True)
            
            # Check if the script ran successfully
            if result.returncode == 0:
                await ctx.send(f"\n{result.stdout}")
            else:
                await ctx.send(f"Error:\n{result.stderr}")
        except Exception as e:
            await ctx.send(f"An error occurred while running the script: {e}")

def setup(bot):
    bot.add_cog(PythonScriptCog(bot))
