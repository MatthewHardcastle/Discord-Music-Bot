import discord
from discord.ext import commands
import lavalink
from discord import utils
from discord import Embed
import re

#references:
#https://github.com/Devoxin/Lavalink.py/blob/master/examples/music.py
#https://lavalink.readthedocs.io/en/latest/

url_rx = re.compile(r'https?://(?:www\.)?.+')

class Music(commands.Cog):
    def __init__(self, Bot):
        self.Bot = Bot
        self.Bot.music = lavalink.Client(self.Bot.user.id)
        self.Bot.music.add_node('localhost', 2333, 'DiscordBotTest', 'na', 'music-node')
        self.Bot.add_listener(self.Bot.music.voice_update_handler, 'on_socket_response')
        self.Bot.music.add_event_hook(self.track_hook)

    @commands.command(name='Join')
    async def join(self, ctx):
        print('Bot has joined!')
        member = utils.find(lambda m: m.id == ctx.author.id, ctx.guild.members)
        if member is not None and member.voice is not None:
            vc = member.voice.channel
            player = self.Bot.music.player_manager.create(ctx.guild.id, endpoint=str(ctx.guild.region))
            if not player.is_connected:
                player.store('channel', ctx.channel.id)
                await self.connect_to(ctx.guild.id, str(vc.id))

    @commands.command(name='Play')
    async def play(self, ctx, *, query):
        embed = discord.Embed(color=discord.Color.blurple())
        player = self.Bot.music.player_manager.get(ctx.guild.id)
        query = query.strip('<>')
        if not url_rx.match(query):
            i = 0
            query_result = ''
            try:
                player = self.Bot.music.player_manager.get(ctx.guild.id)
                query = f'ytsearch:{query}'
                results = await player.node.get_tracks(query)
                tracks = results['tracks'][0:10]
                for track in tracks:
                    i = i + 1
                    query_result = query_result + f'{i}) {track["info"]["title"]} - {track["info"]["uri"]}\n'
                embed = Embed()
                embed.description = query_result
                await ctx.channel.send(embed=embed)

                def Author_check(message):
                    return message.author.id == ctx.author.id
                response = await self.Bot.wait_for('message', check=Author_check)
                track = tracks[int(response.content) - 1]
                player.add(requester=ctx.author.id, track=track)
                if not player.is_playing:
                    await player.play()
                    print("Bot is playing music")
            except Exception as error:
                print(error)
        else:
            results = await player.node.get_tracks(query)
            if not results or not results['tracks']:
                return await ctx.send('Nothing found!')
            embed = discord.Embed(color=discord.Color.blurple())
            if results['loadType'] == 'PLAYLIST_LOADED':
                tracks = results['tracks']
                for track in tracks:
                    player.add(requester=ctx.author.id, track=track)
                embed.title = 'Playlist added!'
                embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
                await ctx.send(embed=embed)
                if not player.is_playing:
                    await player.play()
                    print("Bot is playing music")

    @commands.command(name='Leave')
    async def disconnect(self, ctx):
        player = self.Bot.music.player_manager.get(ctx.guild.id)
        if not player.is_connected:
            return await ctx.send('Not connected.')
            print("Bot is not in a voice channel!")
        player.queue.clear()
        await player.stop()
        await ctx.guild.change_voice_state(channel=None)
        print("Bot has left!")

    @commands.command(name='Help')
    async def Help(self, ctx):
        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = "HELP"
        embed.description = "!Play-Enter a song name or url and the bot will play the music if it is in your channel" \
                            "\n!Leave-The bot will leave the  channel" \
                            "\n!Join-The bot will join your channel" \
                            "\n!Pause-Pauses the music" \
                            "\n!Resume-Unpauses the music"
        await ctx.send(embed=embed)

    @commands.command(name='Pause')
    async def Pause(self, ctx):
        player = self.Bot.music.player_manager.get(ctx.guild.id)
        await player.set_pause(True)

    @commands.command(name='Resume')
    async def Reusme(self, ctx):
        player = self.Bot.music.player_manager.get(ctx.guild.id)
        await player.set_pause(False)

    async def track_hook(self, event):
        if isinstance(event, lavalink.events.QueueEndEvent):
            guild_id = int(event.player.guild_id)
            await self.connect_to(guild_id, None)

    async def connect_to(self, guild_id: int, channel_id: str):
        ws = self.Bot._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)


def setup(Bot):
    Bot.add_cog(Music(Bot))