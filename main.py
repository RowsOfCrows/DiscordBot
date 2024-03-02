
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
import asyncpraw
import asyncprawcore


#===== Other Files ======   
import youtubestuff
import locations
import redditapi
import TokensAndKeys

logging.basicConfig(level=logging.DEBUG)

guildjackid = 1201960481162530846
guildobject = discord.Object(id=guildjackid) 


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

moeid = client.get_user(98200277580009472)

voice_channel_list = []
muteChat = client.get_channel(1201960482534346824)




@client.event
async def on_ready():
    print(f'Bot connected as {client.user} (ID: {client.user.id})')
    await client.change_presence(activity=discord.Game('Very good boy'))
    print('------')

    #for guild in client.guilds: #print all the guilds and channels the bot is in
    #    print("=========")
    #    print(f"Guild: {guild}")#{(str(guildobject))}
    #    for catagory in guild.categories:
    #        print(f"___{str(catagory)}___ ")
    #        for channel in catagory.channels:
    #            print(f"{str(channel.type)} - {channel.name}")


    for channel in client.get_all_channels(): #Get list of voice channels in jack server
        if channel.guild.id == guildjackid:
            if str(channel.type) == 'voice':
                voice_channel_list.append(channel.id)


    #asyncio.create_task(redditapi.monitor_calendar_submissions())
    #redditapi.calendardm(moeid)
    #dmtest.start()
                


#===========================================================
# loop tasks
#===================
#@tasks.loop


#============================================================
# Channel events
#==============

  
@client.event
async def on_guild_channel_create(channel):
    if channel.guild.id == guildjackid and str(channel.type) == 'voice':
        voice_channel_list.append(channel.id)
        #print(f"Channel created in {channel.guild.name}: {channel.name} {channel.id}")
        #print(voice_channel_list)

@client.event
async def on_guild_channel_delete(channel):
    for guild in client.guilds:
        if guild.id == guildjackid and str(channel.type) == 'voice': 
            voice_channel_list.remove(channel.id)
            #print(f"Channel deleted in {channel.guild.name}: {channel.name} {channel.id}")
            #print(voice_channel_list)          



#===========================================================
# new tree stuff main
#====================
@client.tree.command(name="ping", description="return bot latency")
async def ping(interaction):
    bot_latency = round(client.latency * 1000)
    await interaction.response.send_message(f"Response time: {bot_latency}ms.")


@client.tree.command(name="time", description="the local time of any place!")
async def time(interaction: discord.Interaction, location: str):
    eee = await locations.getTimeString(location)
    print(eee)
    await interaction.response.send_message(eee)

#===========================================================
# Weather
#========
@client.tree.command(name="weather", description="your local weather, right now")
async def weather(interaction: discord.Interaction, place: str,  layout: str = None):

    await interaction.response.defer()#wait longer than 3 seconds ty

    if layout is None:
        weathermsg = await locations.createweatherembedboxes(place)
    else:
        weathermsg = await locations.createweatherembedline(place)

    if isinstance(weathermsg, discord.Embed):
        await interaction.followup.send(embed=weathermsg)
    elif weathermsg == 1: #error with search query
        await interaction.followup.send(f"**{place}** could not be found in the search.\n"
                                        "\nThis message will now self descruct")
        await asyncio.sleep(5)
        await interaction.delete_original_response()
    elif weathermsg == 2: #error with retrieving data
        await interaction.followup.send(f"Unable to retrieve weather data. The weather service might be down.\n"
                                         "\nThis message will now self descruct")
        await asyncio.sleep(5)
        await interaction.delete_original_response()
            
#===========================================================
# dm testing
#===========
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


#===========================================================
# Reddit new and hot
#===================
@client.tree.command(name="reddithotpost", description="will post a hot post from the desired subreddit")
async def reddithot(interaction:discord.Interaction, subreddit: str):
    embedthis = await redditapi.posthot(subreddit)
    await interaction.response.send_message(embed=embedthis)

@client.tree.command(name="redditnewpost", description="will post the newest post from the desired subreddit")
async def redditnew(interaction:discord.Interaction, subreddit: str):
    embedthis = await redditapi.postnewest(subreddit)
    await interaction.response.send_message(embed=embedthis)

#============================================================
# Regular Text
#==============
@client.event
async def on_message(message):
    if message.author == client.user: # if message is from bot, ignore all other if statements
        return

    # hello
    if message.content.startswith('hi bot'):
        await message.channel.send(f"Woof! <@{message.author.id}>! :heart:")



#~~~
        


    # Forward all text messages in voice channels to a single text channel
    if message.channel.id in voice_channel_list:
        # embed message
        embed_message = discord.Embed(color=message.author.accent_color, timestamp=message.created_at)
        embed_message.set_author(name=f"{message.author.display_name} - {message.channel.name}", url=message.jump_url,
                                 icon_url=message.author.avatar)
        # If message has any attachments, attach the first one to embed
        if message.attachments:
            embed_message.set_image(url=message.attachments[0])
        # If has content, send content
        if message.content:
            embed_message.add_field(name="", value=message.content, inline=False)
        await muteChat.send(embed=embed_message)

#============================================================

client.run(TokensAndKeys.discotoken)



# old commands, this wont work because for some reason the slash commands 
# dont sync with guild when you use client.command stuff
#@client.command(brief="syntax .time place", description="very cool")
#async def time(ctx, *place):
#    eee = locations.stringtime(place)
#    await ctx.send(eee)

 