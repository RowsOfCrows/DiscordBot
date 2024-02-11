
#===== Discord.py imports ======
import discord, logging
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext import tasks

#===== Python libraries ======
import random
import requests
import feedparser
import asyncio


#===== Other Files ======   
import youtubestuff
import locations
import redditapi
import TokensAndKeys

logging.basicConfig(level=logging.DEBUG)

class MyClient(discord.Client): #bot initalization


    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=guildobject)
        await self.tree.sync(guild=guildobject)

intents = discord.Intents.default()
intents.message_content = True
client = MyClient(intents=intents)
#client = commands.Bot(command_prefix = '.', intents=intents)
#client.remove_command('help')

guildobject = discord.Object(id=1201960481162530846) #jack server
moeid = client.get_user(98200277580009472)





@client.event
async def on_ready():
    print(f'Bot connected as {client.user} (ID: {client.user.id})')
    await client.change_presence(activity=discord.Game('Very good boy'))
    print('------')
    #asyncio.create_task(redditapi.monitor_submissions())
    #redditapi.calendardm(moeid)
    #dmtest.start()
 

#===================
#-------new tree stuff
#===================
@client.tree.command(name="ping", description="return bot latency")
async def ping(interaction):
    bot_latency = round(client.latency * 1000)
    await interaction.response.send_message(f"Response time: {bot_latency}ms.")


@client.tree.command(name="time", description="the local time of any place!")
async def time(interaction: discord.Interaction, location: str):
    eee = locations.getTimeString(location)
    await interaction.response.send_message(eee)

#========= Weather
@client.tree.command(name="weather", description="your local weather, right now")
async def weather(interaction: discord.Interaction, place: str):

    await interaction.response.defer()#wait longer than 3 seconds ty
    #weathermsg = "frick1"
    

    weathermsg = await locations.createweatherembed(place)

        #await interaction.followup.send(f"**{place}** couldn't be found in the search.\n",
        #                                f"Maybe it's not a real place? or maybe you typo'd it so badly that you're getting this error")
    
    #if weathermsg == type(discord.Embed()):
    #    await interaction.followup.send(embed=weathermsg)
    #else:
    #    await interaction.followup.send(weathermsg)
    await interaction.followup.send(embed=weathermsg)


    

#========dm testing
@client.tree.command(name="semddmnewtest", description="will dm you like a good boye")
async def senddmtest(interaction:discord.Interaction):

    user_id = interaction.user
    messageid = interaction.id
    #user = client.get_user(user_id)

    channel = await user_id.create_dm()
    await channel.send("woof")
    await interaction.response.send_message("done",ephemeral=True)

#========Reddit dm test
@client.tree.command(name="calendar", description="dms you todays day picture")
async def reddittest(interaction:discord.Interaction):
    await redditapi.testdmme(interaction.user)
    await interaction.response.send_message("done", ephemeral=True)




@client.tree.command(name="weatherdepreciated", description="weather but only in america because the api said so")
async def weather(interaction: discord.Interaction, place: str):

    await interaction.response.defer()#wait longer than 3 seconds ty
    #thingo = await locations.getweatherembed2(place)
    try:
        embe = await locations.getweatherembed(place)
    except:
        await interaction.followup.send(f"> **{place}** couldn't be found in the search. "
                                        f"The Weather module can only do locations in America because that's what the weather man tells me")
        return
    await interaction.followup.send(embed=embe)



@client.tree.command(name="weathertestdataget", description="g")
async def weathergfdg(interaction: discord.Interaction, place: str):
    thing = await locations.getWeatherapidotcomData(place)
    print(thing)
    await interaction.response.send_message("done", ephemeral=True)




#========Reddit new and hot
@client.tree.command(name="reddithotpost", description="will post a hot post from the desired subreddit")
async def reddithot(interaction:discord.Interaction, subreddit: str):
    embedthis = await redditapi.posthot(subreddit)
    await interaction.response.send_message(embed=embedthis)

@client.tree.command(name="redditnewpost", description="will post the newest post from the desired subreddit")
async def redditnew(interaction:discord.Interaction, subreddit: str):
    embedthis = await redditapi.postnewest(subreddit)
    await interaction.response.send_message(embed=embedthis)

#==========


client.run(TokensAndKeys.discotoken)



# old commands, this wont work because for some reason the slash commands 
# dont sync with guild when you use client.command stuff
#@client.command(brief="syntax .time place", description="very cool")
#async def time(ctx, *place):
#    eee = locations.stringtime(place)
#    await ctx.send(eee)

 