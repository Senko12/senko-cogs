from .pymyweather import SchoolClosureCog

def setup(bot):
    bot.add_cog(SchoolClosureCog(bot))
