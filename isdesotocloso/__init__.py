from redbot.core import commands

class SchoolClosureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def desoto(self, ctx):
        # Your logic for the desoto command here
        await ctx.send("This is where the school closure info will go.")
