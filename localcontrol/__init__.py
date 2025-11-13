from .streamrelay import StreamRelay

async def setup(bot):
    await bot.add_cog(StreamRelay(bot))
self.bot.loop.create_task(self._run_server())
