
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
import redditapi
import TokensAndKeys
import calendarprog

logging.basicConfig(level=logging.DEBUG)


chat_queue = []     # bot AI prompt queue in the form of [{discord.message, reference to bot's reply}, ... ]
is_busy = False     # Is bot busy chatting to another prompt
CHATBOT_MEMORY_BUFFER = 200  # number of messages to keep in memory from both user and baidbot
ollama_client = ollama.Client()
CURRENT_OLLAMA_MODEL = "jackwhimsllama3.2uncensored" # Model name used by ollama
MODEL_OPTIONS = {
    "Whimsical": "jackwhimsllama3.2uncensored",   
    "Axiom": "AxiomV1",
    "Depressed":"BarknessV1"
}
llm_names = ["jack", "axi", "axiom", "barkness"]
if not os.path.exists("BotData"):
    os.makedirs("BotData")

guildjackid = 875349586141675582
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
moeidnum = 98200277580009472
muteChat = client.get_channel(1382153701439049769)
voice_channel_list = []
webhook_cache = {}
calendar_image_folder = "BotData\\anime_calendar_images"
last_posted_cal_img_date = None

@client.event
async def on_ready():    
    print(f'Bot connected as {client.user} (ID: {client.user.id})')
    await client.change_presence(activity=discord.Game('Very good boy'))
    print('------')

    for channel in client.get_all_channels(): #Get list of voice channels in jack server
        if channel.guild.id == guildjackid:
            if str(channel.type) == 'voice':
                voice_channel_list.append(channel.id)
    #print(f"appended voice channels : {voice_channel_list}")


    global last_posted_cal_img_date
    last_posted_cal_img_date = await load_last_posted_date()
    print(f"Loaded last posted calendar date: {last_posted_cal_img_date}")

    client.tree.clear_commands(guild=guildobject)
    guid_synced = await client.tree.sync(guild=guildobject)
    print(f"Synced {len(guid_synced)} commands.")

    #for guild in client.guilds: #print all the guilds and channels the bot is in
    #    print("=========")
    #    print(f"Guild: {guild}")#{(str(guildobject))}
    #    for catagory in guild.categories:
    #        print(f"___{str(catagory)}___ ")
    #        for channel in catagory.channels:
    #            print(f"{str(channel.type)} - {channel.name}")

    checkcalendardaychange.start()

    #channel = await moeid.id.create_dm()
    #await channel.send("woof")               



#===========================================================
# loop tasks
#===================
@tasks.loop(seconds=7)
async def sevensecloop():
    print("==== 7 second loop ====")

#~~~~~~~~~~~~~
# Calendar Images
#~~

async def save_last_posted_date(date_str):
    with open('BotData\\last_posted_cal_img_date.txt', 'w') as file:
        file.write(date_str)

async def load_last_posted_date():
    if os.path.exists('BotData\\last_posted_cal_img_date.txt'):
        with open('BotData\\last_posted_cal_img_date.txt', 'r') as file:
            return file.read().strip()
    return None

async def get_day_suffix(day):
    """Return the appropriate suffix for a given day."""
    if 10 <= day % 100 <= 20:  # Handle 11th, 12th, 13th
        return 'th'
    else:
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')


@tasks.loop(seconds=735) #12 minutes 15 seconds
async def checkcalendardaychange():
    await client.wait_until_ready()
    global last_posted_cal_img_date    
    cal_channel = client.get_channel(1382619573890842755)

    current_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=-5)
    current_day = current_time.day
    current_month = current_time.strftime("%B")
    current_date_str = f"{current_month} {current_day}"
    suffix = await get_day_suffix(current_day)

    print(f"Calendar Check... Current date: {current_date_str} | Last posted: {last_posted_cal_img_date}")

    if current_date_str != last_posted_cal_img_date:
        filename = f"{current_date_str}"
        for file in os.listdir(calendar_image_folder):
            if file.startswith(filename):
                file_path = os.path.join(calendar_image_folder, file)
                await cal_channel.send( content=f"**# {current_date_str}{suffix}**"
                                                f"Year Progress: ` {calendarprog.progress_bar(calendarprog.year_progress())}`"
                                                f"Month Progress: `{calendarprog.progress_bar(calendarprog.year_progress())}`",
                                        file=discord.File(file_path))
                last_posted_cal_img_date = current_date_str
                await save_last_posted_date(current_date_str)    #await client.wait_until_ready()


@client.tree.command(name="calendar_search", description="Search for a calendar image by month and day.")
@app_commands.describe(month="Month Name", day="Day of the month (e.g. 15)")
@app_commands.choices(month=[
        app_commands.Choice(name="January", value="January"),
        app_commands.Choice(name="February", value="February"),
        app_commands.Choice(name="March", value="March"),
        app_commands.Choice(name="April", value="April"),
        app_commands.Choice(name="May", value="May"),
        app_commands.Choice(name="June", value="June"),
        app_commands.Choice(name="July", value="July"),
        app_commands.Choice(name="August", value="August"),
        app_commands.Choice(name="September", value="September"),
        app_commands.Choice(name="October", value="October"),
        app_commands.Choice(name="November", value="November"),
        app_commands.Choice(name="December", value="December")
    ])
async def calendarsearch(interaction: discord.Interaction, month: str, day: int):
    await interaction.response.defer()  # Optional: useful if searching takes time

    # Format the filename to search
    #search_date = f"{month.capitalize()} {day}"
    suffix = await get_day_suffix(day)
    search_date = f"{month} {day}{suffix}"
    found = False

    # Search for matching file
    for file in os.listdir(calendar_image_folder):
        if file.startswith(search_date):
            file_path = os.path.join(calendar_image_folder, file)
            await interaction.followup.send(content=f"**# {search_date}{suffix}**",
                                            file=discord.File(file_path))
            found = True
            break

    if not found:
        await interaction.followup.send(f"No calendar image found for **{search_date}**.")


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
@client.tree.command(name="reddithotpost", description="will post a hot post from the desired subreddit")
async def reddithot(interaction:discord.Interaction, subreddit: str):
    embedthis = await redditapi.posthot(subreddit)
    await interaction.response.send_message(embed=embedthis)

@client.tree.command(name="redditnewpost", description="will post the newest post from the desired subreddit")
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
        with open("BotData\\chat_history.json", 'w') as f:
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
    if not os.path.exists("BotData\\chat_history.json"):
        with open("BotData\\chat_history.json", 'w') as f:
            json.dump({}, f)
    with open("BotData\chat_history.json", 'r') as f:
        chat_history_dict = json.load(f)

    # Create chat history for channel if it does not already exist
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

    with open("BotData\chat_history.json", 'w') as f:
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

    # Check for existing webhook in the destination channel
    if muteChat.id not in webhook_cache:
        webhook = await muteChat.create_webhook(name="Forwarder")
        webhook_cache[muteChat.id] = webhook.url
    else:
        webhook = discord.Webhook.from_url(
            webhook_cache[muteChat.id],
            session=client.http._session  # Updated for discord.py v2.x
        )
    await webhook.send(
        content=f"{message.content}",
        username=f"{display_name} [{message.channel.name}]",
        avatar_url=avatar_url
    )
    
    #embed_message = discord.Embed(color=message.author.accent_color, timestamp=message.created_at)
    #embed_message.set_author(name=f"{message.author.display_name} - {message.channel.name}", url=message.jump_url,
    #                            icon_url=message.author.avatar)
    ## If message has any attachments, attach the first one to embed
    #if message.attachments:
    #    embed_message.set_image(url=message.attachments[0])
    ## If has content, send content
    #if message.content:
    #    embed_message.add_field(name="", value=message.content, inline=False)
    #return await muteChat.send(embed=embed_message)



#============================================================
# Regular Text
#==============
@client.event
async def on_message(message):
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

    # Prompt LLM
    if (any(name in message.content.lower() for name in llm_names)  #regular words
        or client.user in message.mentions                          #discord reply
        or isinstance(message.channel, discord.DMChannel)           #dm message
        ):

        global is_busy
        # Immediately respond with queue position if chatbot is busy
        if is_busy:
            chat_response = await message.reply(content=f"-# (Queue: {len(chat_queue) + 1})", silent=True)
        else:
            # This message gets immediately overwritten so it doesnt really matter whats in it, it just needs to have a response for baidbot to edit
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



# old commands, this wont work because for some reason the slash commands 
# dont sync with guild when you use client.command stuff
#@client.command(brief="syntax .time place", description="very cool")
#async def time(ctx, *place):
#    eee = locations.stringtime(place)
#    await ctx.send(eee)

 