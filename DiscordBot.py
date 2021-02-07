import discord
from discord.ext import commands


bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    print("Bot is running!")
    bot.load_extension('cogs.MusicCommands')
###############################################################


bot.run("BOT_TOKEN")