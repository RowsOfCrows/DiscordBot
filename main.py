from discord.ext import commands
import discord, logging
from discord.ext.commands import Bot
import random
import requests
import asyncio
import feedparser
from discord.ext import tasks
import youtubestuff
import locations
import TokensAndKeys

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True

#client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix=",", intents=intents)
#tree = discord.app_commands.CommandTree(bot)
#client = discord.Client()
moeid = 98200277580009472
guildid = 1201960481162530846 #jack server

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    await bot.tree.sync()
    await bot.tree.sync(guild=discord.Object(id=guildid))

    #dmtest.start()
    await bot.change_presence(activity=discord.Game('Very good boy'))

#@tasks.loop(seconds=15)
#async def dmtest():
#    await bot.get_user(moeid).send("woof")
#

@bot.command(brief="syntax: .weather place")
async def weather(ctx, *place):
    temp = locations.getweatherembed(place)
    await ctx.send(embed=temp)


@bot.command(brief="syntax .time place", description="very cool")
async def time(ctx, *place):
    eee = locations.stringtime(place)
    await ctx.send(eee)

@bot.command(brief="searches youtube",description="not very cool")
async def yt(ctx, *search):
    cool = youtubestuff.yt_search(search)
    await ctx.send(cool)

@bot.command(brief="rss test")
async def heck(ctx):
    cool = youtubestuff.rsstest()
    await ctx.send(cool)

@bot.tree.command(name="time", description="time!")
async def ping(interaction):
    bot_latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Response time: {bot_latency}ms.")

@bot.tree.command(name="ping", description="return bot latency")
async def ping(interaction):
    bot_latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Response time: {bot_latency}ms.")

#@tasks.loop()
#async def dmtest(member: discord.Member, *, content):
#    channel = await member.create_dm()
#    await channel.send("cool")



bot.run(TokensAndKeys.discotoken)

#@client.command()
#async def senddm(ctx):
#    user_id = ctx.author.id
#    user = bot.get_user(user_id)
#    channel = await user.create_dm()
#    await channel.send("woof")
#
#@client.command()
#async def deletestupidhistory(ctx):
#    print("something")
#    user_id = ctx.author.id
#    user = client.get_user(user_id)
#    if user:
#        channel = await user.create_dm()
#        async for message in channel.history(limit=None):
#            if message.author.bot:
#                await message.delete()
#