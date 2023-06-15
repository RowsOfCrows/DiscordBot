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
bot = commands.Bot(command_prefix=",")
client = discord.Client()


@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    await bot.change_presence(activity=discord.Game('Very good boy'))

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

bot.run(TokensAndKeys.discotoken)
