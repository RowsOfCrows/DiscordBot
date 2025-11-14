
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
import ollama
import json
import os
import re
import datetime

#===== Other Files ======   
import youtubestuff
import TokensAndKeys
import redditapi
import locationinfo
from messagelistener import oll_host, oll_winpc_host, oll_ubupc_local_host

logging.basicConfig(level=logging.DEBUG)


import socket
socket.getaddrinfo = lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))]



chat_queue = []     # bot AI prompt queue in the form of [{discord.message, reference to bot's reply}, ... ]
is_busy = False     # Is bot busy chatting to another prompt
CHATBOT_MEMORY_BUFFER = 200  # number of messages to keep in memory from both user and chatbot
ollama_client = ollama.Client(host=f"http://{oll_host}:11434")
CURRENT_OLLAMA_MODEL = "jackwhims" 

if not os.path.exists("BotData"):
    os.makedirs("BotData")


guildjackid = 875349586141675582
guildobject = discord.Object(id=guildjackid) 
voice_channel_list = []
#=============================================
# Set up client 
#========================

class MyClient(commands.Bot):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(command_prefix="zz",
                         intents=intents,
                         owner_id=98200277580009472
                         )

    async def setup_hook(self):
        # load cogs
        await self.load_extension('cogs.calendarcog')
        await self.load_extension('cogs.devtools')
        await self.load_extension('messagelistener')
        #await self.load_extension('cogs.imagey')

intents = discord.Intents.all()
intents.message_content = True
#client = commands.Bot(command_prefix='!', intents=intents)
client = MyClient(intents=intents)
client.owner_id = 98200277580009472
client.command_prefix="zz"

#=============================================
moeid = client.get_user(98200277580009472)
moeidnum = 98200277580009472
muteChat = client.get_channel(1382153701439049769)


@client.event
async def on_ready():    
    print('=========================================================')
    print(f'Bot connected as {client.user} (ID: {client.user.id})')
    await client.change_presence(activity=discord.Game('Very good boy'))
    print('------')

    jackguild = client.get_guild(875349586141675582)
    for channel in jackguild.channels: #Get list of voice channels in jack server
        if str(channel.type) == 'voice':
            voice_channel_list.append(channel.id)
    print(f"appended vc: {voice_channel_list}")
    print('=========================================================')



#===========================================================
# loop tasks
#===================
#@tasks.loop(seconds=7)
#async def sevensecloop():
#    print("==== 7 second loop ====")

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
    #eee = await locations.getTimeString(location)
    eee = await locationinfo.gettime(location)
    print(eee)
    await interaction.response.send_message(eee)

@client.tree.command(name='sync', description='Owner only')
async def sync(interaction: discord.Interaction):
    if interaction.user.id == moeid:
        await client.tree.sync()
        print('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')

#===========================================================
# Weather
#========
@client.tree.command(name="weather", description="your local weather, right now")
async def weather(interaction: discord.Interaction, place: str,  time: str = None):

    await interaction.response.defer()#wait longer than 3 seconds ty



    #if layout is None:
    #    weathermsg = await locations.createweatherembedboxes(place)
    #else:
    #    weathermsg = await locations.createweatherembedline(place)
#
    #if isinstance(weathermsg, discord.Embed):
    #    await interaction.followup.send(embed=weathermsg)
    #elif weathermsg == 1: #error with search query
    #    await interaction.followup.send(f"**{place}** could not be found in the search.\n"
    #                                    "\nThis message will now self descruct")
    #    await asyncio.sleep(5)
    #    await interaction.delete_original_response()
    #elif weathermsg == 2: #error with retrieving data
    #    await interaction.followup.send(f"Unable to retrieve weather data. The weather service might be down.\n"
    #                                     "\nThis message will now self descruct")
    #    await asyncio.sleep(5)
    #    await interaction.delete_original_response()
            
#===========================================================
# dm testing
#===========
#@client.tree.command(name="semddmnewtest", description="will dm you like a good boye")
#async def senddmtest(interaction:discord.Interaction):
#
#    user_id = interaction.user
#    messageid = interaction.id
#    #user = client.get_user(user_id)
#
#    channel = await user_id.create_dm()
#    await channel.send("woof")
#    await interaction.response.send_message("done",ephemeral=True)




#===========================================================
# Reddit new and hot
#===================
@app_commands.command(name="reddithotpost", description="will post a hot post from the desired subreddit")
async def reddithot(interaction:discord.Interaction, subreddit: str):
    embedthis = await redditapi.posthot(subreddit)
    await interaction.response.send_message(embed=embedthis)

@app_commands.command(name="redditnewpost", description="will post the newest post from the desired subreddit")
async def redditnew(interaction:discord.Interaction, subreddit: str):
    embedthis = await redditapi.postnewest(subreddit)
    await interaction.response.send_message(embed=embedthis)



#============================
# Get Avatar Embeded
#===========
@client.tree.command(name="avatar", description="Get the avatar of a user in the server")
@app_commands.describe(user="The user to get the avatar of (optional)")
async def avatar(interaction: discord.Interaction, user: discord.Member = None):
    if user is None:
        user = interaction.user

    avatar_url = user.display_avatar.url

    embed = discord.Embed(
        title="Avatar Link",
        url=f"{avatar_url}",
    )
    embed.set_author(name=f"{user.display_name}", icon_url=avatar_url)
    embed.set_image(url=avatar_url)
    embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

    await interaction.response.send_message(embed=embed)


#===========================================================
# Ollama
#===================


@client.tree.command(name="reset_ai", description="Reset chatbot's message queue and response status")
async def reset_queue(interaction: discord.Interaction):
    cog = client.get_cog("MessageListener")
    
    if cog is None:
        await interaction.response.send_message("❌ MessageListener cog not found!", ephemeral=True)
        return
    
    queue_size = len(cog.chat_queue)
    was_busy = cog.is_busy
    
    cog.chat_queue.clear()
    cog.is_busy = False
    
    await interaction.response.send_message(f"✅ Cleared {queue_size} queued message(s)\n")


@client.tree.command(name="clear_history", description="Clear the chatbot's entire conversation history")
async def reset_history(interaction: discord.Interaction):
    try:
        # Open the file and overwrite it with an empty dictionary
        with open("BotData/chat_history.json", 'w') as f:
            json.dump({}, f, indent=4)

        await interaction.response.send_message("✅ Chat history has been cleared.")

    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to clear chat history. Error: {e}")

#===========================================================
# 
#===================

async def forwardvoicetext(message):
    muteChat = client.get_channel(1382153701439049769)

    display_name = message.author.display_name
    avatar_url = message.author.avatar.url if message.author.avatar else message.author.default_avatar.url

    mcwebhooks = await muteChat.webhooks()
    if mcwebhooks:
        mcwebhooks = mcwebhooks[0]
    else:
        mcwebhooks = await muteChat.create_webhook(name="Message Forwarding")

    await mcwebhooks.send(
        content=f"{message.content}",
        username=f"{display_name} [{message.channel.name}]",
        avatar_url=avatar_url
    )


#============================================================
# Regular Text
#==============
@client.event
async def on_message(message: discord.Message):
    if message.author == client.user: # if message is from bot, ignore all other if statements
        return
    
    #message.content = message.content.lower() #make everything lowercase
    
    # hello
    if message.content.startswith('hi bot'):
        await message.channel.send(f"Woof! <@{message.author.id}>! :heart:")

#~~~ 

    # time in <place>
    if message.content.startswith(".time ") :
        await message.channel.send(await locationinfo.gettime(message.content[6:]))
    if message.content.startswith("time in") :
        await message.channel.send(await locationinfo.gettime(message.content[7:]))

        #placeholder = await message.channel.send("-# Fetching local time 🌍...")
        #result = await locationinfo.gettime(message.content[6:])
        #await placeholder.edit(content=result)
        # or delete last message instead of edit
        #await placeholder.delete()
        #await message.channel.send(result)

    # weather in <place>
    if message.content.startswith('.weather') :
        await message.channel.send(await locationinfo.get_weather(message.content[9:]))

#~~~ 

    # Forward all text messages in voice channels to a single text channel
    if message.channel.id in voice_channel_list:
        await forwardvoicetext(message)

#~~~

    #global ollama_client
    #global oll_host
    #if message.content.startswith('ch host') and (message.author.id == moeidnum):
    #    if oll_host == oll_winpc_host:
    #        oll_host = oll_ubupc_local_host
    #        print("✅ changed to ubuntu 🐧")
    #        await message.channel.send("✅ 🐧 host changed to Ubuntu!") #, ephemeral=True
    #    else:
    #        oll_host = oll_winpc_host
    #        print("✅ changed to windows")
    #        await message.channel.send("✅ 🪟 host changed to Windows!") #, ephemeral=True
    #    #ollama_client = ollama.Client(host=f"http://{oll_host}:11434")


    if message.channel.id == 1382296618677571654:
        return # please ignore other testing chanel for now 


#============================================================


client.run(TokensAndKeys.discotoken) 