# __init__.py

from .pymyweather import SchoolClosureCog

def setup(bot):
    # Remove 'await' from bot.add_cog() since it's not a coroutine
    bot.add_cog(SchoolClosureCog(bot))
