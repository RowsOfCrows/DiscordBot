
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
import ollama
import json
import os
import re
import datetime

#===== Other Files ======   
import youtubestuff
import locations
import TokensAndKeys
import redditapi
from messagelistener import oll_host, oll_winpc_host, oll_ubupc_host

logging.basicConfig(level=logging.DEBUG)

chat_queue = []     # bot AI prompt queue in the form of [{discord.message, reference to bot's reply}, ... ]
is_busy = False     # Is bot busy chatting to another prompt
CHATBOT_MEMORY_BUFFER = 200  # number of messages to keep in memory from both user and baidbot
host = oll_host
ollama_client = ollama.Client(host=f"http://{host}:11434")
CURRENT_OLLAMA_MODEL = "jackwhims" # Model name used by ollama
MODEL_OPTIONS = {
    "Whimsical": "jackwhims",   
    "Axiom": "AxiomV1",
    "Depressed":"BarknessV1",
    "DogAI":"DogAI"
}
llm_names = ["jack", "axi", "axiom", "barkness", "dagi", "dogai"]
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



        #print(f"App commands registered in tree: {[cmd.name for cmd in self.tree.get_commands()]}")

        # remove stale commands
#        self.tree.clear_commands(guild=guildobject)
#        print("✅ Cleared guild commands.")
#
#        self.tree.clear_commands(guild=None)
#        print("✅ Cleared global commands.")
#
#        # Sync global commands (commands without @guilds)
#        #synced_global = await self.tree.sync()
#        #print(f"✅ {len(synced_global)} commands synced globally 🌍.")
#
#        # Sync guild commands (commands with @guilds)
#        synced_in_guild = await self.tree.sync(guild=guildobject)
#        print(f"✅ {len(synced_in_guild)} commands synced to guild {guildobject.id}.")
#
#
#        print(f"App commands registered in tree: {[cmd.name for cmd in self.tree.get_commands()]}")


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
    #global last_posted_cal_img_date
    #last_posted_cal_img_date = await load_last_posted_date()
    #print(f"Loaded last posted calendar date1: {last_posted_cal_img_date}")


    #await client.tree.sync()
    #gsync = await client.tree.sync(guild=discord.Object(id=guildjackid))
    #print(f"✅ {len(gsync)} commands synced to guild {guildobject.id}.")
    ##client.tree.clear_commands(guild=None)
    #await client.tree.sync()

    #for guild in client.guilds: #print all the guilds and channels the bot is in
    #    print("=========")
    #    print(f"Guild: {guild}")#{(str(guildobject))}
    #    for catagory in guild.categories:
    #        print(f"___{str(catagory)}___ ")
    #        for channel in catagory.channels:
    #            print(f"{str(channel.type)} - {channel.name}")

    #checkcalendardaychange.start()

    #client.tree.clear_commands(guild=guildobject)
    #guid_synced = await client.tree.sync(guild=guildobject)
    #print(f"Synced {len(guid_synced)} commands.")


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

@commands.hybrid_command(name="ping2", description="return bot latency")
async def ping2(ctx):
    bot_latency = round(client.latency * 1000)
    print(f"BOT LAENTNTNTOENEO {bot_latency}")
    await ctx.send(f"Response time: {bot_latency}ms.")


@client.tree.command(name="time", description="the local time of any place!")
async def time(interaction: discord.Interaction, location: str):
    eee = await locations.getTimeString(location)
    print(eee)
    await interaction.response.send_message(eee)

@client.tree.command(name='sync', description='Owner only')
async def sync(interaction: discord.Interaction):
    if interaction.user.id == moeid:
        await client.tree.sync()
        print('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')

#@client.tree.command(name="fake", description="fake webhook messages as yourself")
#async def fake(interaction: discord.Interaction, message: str):
#    user = interaction.user
#    display_name = user.display_name  # This works in guilds (it's the nickname if set)
#    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
#
#    # Check for existing webhook in this channel
#    if interaction.channel.id not in webhook_cache:
#        webhook = await interaction.channel.create_webhook(name="Webhook")
#        webhook_cache[interaction.channel.id] = webhook.url
#    else:
#        webhook = discord.Webhook.from_url(
#            webhook_cache[interaction.channel.id], 
#            adapter=discord.AsyncWebhookAdapter(bot.http._HTTPClient__session)
#        )
#
#    await webhook.send(
#        message,
#        username=display_name,
#        avatar_url=avatar_url
#    )
#
#    await interaction.response.send_message("Message sent!", ephemeral=True)
#

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

@client.tree.command(name="set_model", description="Change the AI model the bot uses")
@app_commands.describe(model_name="Select a model to use")
@app_commands.choices(model_name=[
    app_commands.Choice(name="Whimsical", value="Whimsical"),
    app_commands.Choice(name="Axiom", value="Axiom"),
    app_commands.Choice(name="Depressed", value="Depressed"),
])
async def setmodel(interaction: discord.Interaction, model_name: app_commands.Choice[str]):
    global CURRENT_OLLAMA_MODEL
    global current_model

    # Check if the model exists in your predefined options
    if model_name.value in MODEL_OPTIONS:
        CURRENT_OLLAMA_MODEL = MODEL_OPTIONS[model_name.value]
        current_model = model_name.value
        await interaction.response.send_message(f"✅ Model changed to {current_model}.✅\n") #❗It might take a while to load the first message.❗"
    else:
        await interaction.response.send_message(f"❌ Model '{model_name.value}' not found.", ephemeral=True)



@client.tree.command(name="reset_ai", description="Reset chatbot's message queue and response status")
async def reset_queue(interaction: discord.Interaction):
    global is_busy
    for chat in chat_queue:
        await chat[1].edit(content="-# (Cancelled)")
    chat_queue.clear()     # Reset chat queue
    is_busy = False     # Reset chatbot's responding status
    await interaction.response.send_message("Reset queue and status")



@client.tree.command(name="clear_history", description="Clear the chatbot's entire conversation history")
async def reset_history(interaction: discord.Interaction):
    try:
        # Open the file and overwrite it with an empty dictionary
        with open("BotData/chat_history.json", 'w') as f:
            json.dump({}, f, indent=4)

        await interaction.response.send_message("✅ Chat history has been cleared.")

    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to clear chat history. Error: {e}")



# Handle Ollama requests
async def chat_with_chatbot(message, msg_response):
    await msg_response.edit(content="-# *Jack is thinking...*")
    response_str = ""

    # Check if message is in DM
    if message.guild is not None:
        message_origin = str(message.guild.id)
    else:
        message_origin = str(message.author.id)


    # Load chat history from file
    chat_history_dict = {}
    if not os.path.exists("BotData/chat_history.json"):
        with open("BotData/chat_history.json", 'w') as f:
            json.dump({}, f)
    with open("BotData/chat_history.json", 'r') as f:
        chat_history_dict = json.load(f)

    # Create chat history for channel if it does not alzxready exist
    if message_origin not in chat_history_dict.keys():
        chat_history_dict[message_origin] = []
        print(f"Creating new chat history for {message_origin}")

    # If history is full, then remove the oldest memory (first message in list)
    while len(chat_history_dict[message_origin]) >= CHATBOT_MEMORY_BUFFER:
        chat_history_dict[message_origin].pop(0)
    
    # Add message to the end of the history message list
    chat_history_dict.get(message_origin).append({'role': 'user', 'content': message.author.display_name + " says: " + message.content})

    # print message to console for debugging
    print(f"{chat_history_dict[message_origin][-1]['content']} - (guildid / authorid (DM): {message_origin}, history length: {len(chat_history_dict[message_origin])})")  
    
    # prompt model
    response_stream = ollama.chat(model=CURRENT_OLLAMA_MODEL, 
                                  messages=chat_history_dict[message_origin], 
                                  stream=True)

    # Process response
    for chunk in response_stream:
        if chunk != "" and response_str == "":
            await msg_response.edit(content="-# *Jack is typing...*")
        print(chunk['message']['content'], end='', flush=True)      # print message to console for debugging

        #response_str += re.sub(r'\n\n+', '\n\n', chunk['message']['content'])       # remove extra newlines
        response_str += chunk['message']['content']      # add message to response string

        # Everytime there is a new chunk with ('.', '!', or '?'), update the discord message (update message on new sentence)
        if '.' in chunk['message']['content'] or '!' in chunk['message']['content'] or '?' in chunk['message']['content']:
            await msg_response.edit(content=response_str + "\n-# *chatbot is typing...*")
    
    # Add chatbot's response to chat history
    chat_history_dict.get(message_origin).append({'role': 'assistant', 'content': response_str})
    print('\n')

    # Send finalized chatbot message
    await msg_response.edit(content=response_str)

    with open("BotData/chat_history.json", 'w') as f:
        json.dump(chat_history_dict, f, indent=4)

    # Check if there is messages in queue
    if len(chat_queue) > 0:
        # Update queue positions for messages in queue
        for i in range(0, len(chat_queue)):
            await chat_queue[i][1].edit(content=f"-# (Queue: {i})")
        # Remove first message in queue and process
        temp = chat_queue.pop(0)
        await chat_with_chatbot(temp[0], temp[1])
    else:
        # If messages queue is empty, set chatbot to not be busy (Allow immediate processing of new message)
        global is_busy 
        is_busy = False

#==============================================================


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

    # Forward all text messages in voice channels to a single text channel
    if message.channel.id in voice_channel_list:
        await forwardvoicetext(message)

#~~~


    global oll_host
    if message.content.startswith('ch host') and (message.author.id == moeidnum):
        if oll_host == oll_winpc_host:
            oll_host = oll_ubupc_host
            print("✅ changed to ubuntu 🐧")
            await message.channel.send("✅ 🐧 host changed to Ubuntu!") #, ephemeral=True
        else:
            oll_host = oll_winpc_host
            print("✅ changed to windows")
            await message.channel.send("✅ 🪟 host changed to Windows!") #, ephemeral=True




    if message.channel.id == 1382296618677571654:
        return # please ignore other testing chanel for now 
    
    # Prompt LLM
    if (any(name in message.content.lower() for name in llm_names)  #regular words
        or client.user in message.mentions                          #discord reply
        or isinstance(message.channel, discord.DMChannel)           #dm message
        ):
        pass


        global is_busy
        # Immediately respond with queue position if chat is busy
        if is_busy:
            chat_response = await message.reply(content=f"-# (Queue: {len(chat_queue) + 1})", silent=True)
        else:
            # This message gets immediately overwritten so it doesnt really matter whats in it, it just needs to have a response for chatbot to edit
            chat_response = await message.reply(content=f"-# *...*", silent=True) 
        # Add message to chat queue
        chat_queue.append((message, chat_response))

        # If chatbot is not busy then remove and process first message in queue
        if not is_busy:
            is_busy = True
            temp = chat_queue.pop(0)
            await chat_with_chatbot(temp[0], temp[1])
        return
#~~~


#============================================================


client.run(TokensAndKeys.discotoken) 