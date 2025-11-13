import discord
import json
import os
from redbot.core import commands, checks
from aiohttp import web
import socketio

class StreamRelay(commands.Cog):
    """Relay Discord messages to web client and control streams."""

    def __init__(self, bot):
        self.bot = bot
        self.role_id = 1437970660520361984
        self.channels_file = os.path.join(os.path.dirname(__file__), "channels.json")

        # Socket.IO setup
        self.sio = socketio.AsyncServer(async_mode="aiohttp", cors_allowed_origins="*")
        self.app = web.Application()
        self.sio.attach(self.app)

        # Set up web server
        self.runner = web.AppRunner(self.app)
        self.bot.loop.create_task(self._run_server())

        # Register Socket.IO events
        @self.sio.event
        async def connect(sid, environ):
            print(f"Web client connected: {sid}")

        @self.sio.event
        async def disconnect(sid):
            print(f"Web client disconnected: {sid}")

        # Make sure channels file exists
        if not os.path.exists(self.channels_file):
            with open(self.channels_file, "w") as f:
                json.dump({}, f)

    async def _run_server(self):
        await self.bot.wait_until_red_ready()
        await self.runner.setup()
        site = web.TCPSite(self.runner, "0.0.0.0", 8080)
        await site.start()
        print("[StreamRelay] WebSocket server started on port 8080 and ready for connections.")


    def _load_channels(self):
        with open(self.channels_file, "r") as f:
            return json.load(f)

    def _save_channels(self, data):
        with open(self.channels_file, "w") as f:
            json.dump(data, f, indent=2)

    async def _emit_message(self, author, content, avatar=None, system=False):
        await self.sio.emit("newMessage", {
            "author": author,
            "content": content,
            "avatar": avatar or "https://cdn.discordapp.com/avatars/1437966889186754692/8dcb2153f7f60e0c5c30559b708c3ea6.png?size=4096",
            "system": system
        })

    # --- Message relay ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        await self._emit_message(
            author=message.author.display_name,
            content=message.content,
            avatar=str(message.author.display_avatar.url),
            system=False
        )

        if not message.content.startswith("!"):
            return

        channels = self._load_channels()
        content = message.content.strip()

        # --- !chan ---
        if content.startswith("!chan "):
            arg = content.split(" ", 1)[1]
            url = channels.get(arg, arg)
            await self._emit_message(
                message.author.display_name,
                f"is switching the channel to {url}",
                str(message.author.display_avatar.url),
                system=True
            )
            await self.sio.emit("switchChannel", url)

        # --- !stop ---
        if content == "!stop" and any(r.id == self.role_id for r in message.author.roles):
            await self._emit_message(
                message.author.display_name,
                "stopped the stream.",
                str(message.author.display_avatar.url),
                system=True
            )
            await self.sio.emit("stopChannel")

        # --- !add ---
        if content.startswith("!add ") and any(r.id == self.role_id for r in message.author.roles):
            parts = content.split(" ")
            if len(parts) >= 3:
                url, name = parts[1], parts[2]
                channels[name] = url
                self._save_channels(channels)
                await message.reply(f"Added channel **{name}**.")
                await self._emit_message(
                    message.author.display_name,
                    f"added a new channel: {name}",
                    str(message.author.display_avatar.url),
                    system=True
                )

        # --- !guide ---
        if content == "!guide":
            names = list(channels.keys())
            if names:
                await message.reply("Available channels:\n" + "\n".join(names))
            else:
                await message.reply("No channels available.")

async def setup(bot):
    await bot.add_cog(StreamRelay(bot))
