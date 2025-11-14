import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext import tasks
from dataclasses import dataclass

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
from concurrent.futures import ThreadPoolExecutor
from TokensAndKeys import oll_winpc_host, oll_ubupc_local_host


bottalkchannel = 1382296618677571654
bottalkchannelobject = discord.Object(id=bottalkchannel) 

ollamamodel = "DogAI"
oll_host = oll_ubupc_local_host

chat_queue = []
CHATBOT_MEMORY_BUFFER = 200
pathtest = "BotData/bot_talk/chat_history_test"
path = "BotData/chat_history"

# Create a thread pool executor for Ollama calls
executor = ThreadPoolExecutor(max_workers=4)

@dataclass
class dogprofiles:
    name: str
    oll_modelname: str
    keynames: list
    display_name: str = "Jack"
    avatar_url: str = None

barkness = dogprofiles(
    name = "Barkness",
    oll_modelname = "BarknessV1",
    keynames = ["Barkness", "Barky", "Darkness"],
    display_name = "Barkness",
    avatar_url = "https://raw.githubusercontent.com/Relevant-Name/DiscordBot/main/BotData/barkness.png"
)

axiom = dogprofiles(
    name = "Axiom",
    oll_modelname = "AxiomV1",
    keynames = ["Axiom", "Axi"],
    display_name = "Axiom",
    avatar_url = "https://raw.githubusercontent.com/Relevant-Name/DiscordBot/main/BotData/Axiom.png"
)

dogai = dogprofiles(
    name = "DogAI",
    oll_modelname = "DogAI",
    keynames = ["DogAI", "Dagi", "daggi"],
    display_name = "DogAI",
    avatar_url = "https://raw.githubusercontent.com/Relevant-Name/DiscordBot/main/BotData/DogAI.png"
)

jack = dogprofiles(
    name = "Jack",
    oll_modelname = "JackdogV1",
    keynames = ["Jack", "goodboye"],
    display_name = "Jack",
    avatar_url = "https://raw.githubusercontent.com/Relevant-Name/DiscordBot/main/BotData/DogAI.png"
)

dogprofileslist = [barkness, jack, axiom, dogai]


class MessageListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moeid = bot.get_user(98200277580009472)
        jack.avatar_url = self.bot.user.display_avatar.url

        self.chat_queue = []
        self.is_busy = False

        self.random_response_chance = 0.9  # 0.1 = 10% chance to respond randomly
        self.last_webhook_send = 0  # Track last webhook send time
        self.webhook_cooldown = 1.0  # 1 second between webhook sends


    async def stream_ollama_in_thread(self, ollamamodel, personality_history, profile, whm):
        """
        Run the blocking Ollama streaming call in a separate thread.
        Uses an asyncio Queue to pass chunks back to the main async loop for real-time Discord updates.
        """
        chunk_queue = asyncio.Queue()
        loop = asyncio.get_event_loop()  # Get the loop BEFORE starting the thread
        
        def blocking_ollama_stream():
            """This function runs in a separate thread"""
            response_stream = ollama.chat(
                model=ollamamodel, 
                messages=personality_history, 
                stream=True
            )
            
            for chunk in response_stream:
                content = chunk['message']['content']
                print(content, end='', flush=True)  # print to console for debugging
                has_punctuation = any(punct in content for punct in ".!?")
                # Put chunk into queue thread-safely
                asyncio.run_coroutine_threadsafe(
                    chunk_queue.put((content, has_punctuation)), 
                    loop  # Use the loop we captured earlier
                )
            
            # Signal completion
            asyncio.run_coroutine_threadsafe(
                chunk_queue.put(None), 
                loop  # Use the loop we captured earlier
            )
        
        # Start the blocking call in a thread pool (don't await it yet)
        loop.run_in_executor(executor, blocking_ollama_stream)
        
        # Process chunks as they arrive
        response_str = ""
        first_chunk = True
        
        while True:
            item = await chunk_queue.get()
            if item is None:  # Streaming complete
                break
                
            content, has_punctuation = item
            
            if first_chunk and response_str == "":
                await whm.edit(content=f"-# *{profile.name} is typing...*")
                first_chunk = False
            
            response_str += content
            
            if has_punctuation:
                await asyncio.sleep(1)
                await whm.edit(content=response_str + f"\n-# *{profile.name} is typing...*")
        
        return response_str


    async def chat_with_chatbot(self, usr_msg, profile: dogprofiles, whm=None):
        
        if not whm:
            whm = await self.sendwebhookmsg(usr_msg, profile)

        await whm.edit(content="-# *Loading...*")

        # Determine conversation key
        if usr_msg.guild is not None:
            message_origin = str(usr_msg.guild.id)
        else:
            message_origin = str(usr_msg.author.id)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(f"{path}.json"):
            with open(f"{path}.json", 'w') as f:
                json.dump({}, f)
        with open(f"{path}.json", 'r') as f:
            try:
                chat_history_dict = json.load(f)
            except json.JSONDecodeError:
                chat_history_dict = {}

        # Ensure entry for this conversation exists
        if message_origin not in chat_history_dict:
            chat_history_dict[message_origin] = {}

        # Ensure entry for this personality exists
        personality_key = profile.name
        if personality_key not in chat_history_dict[message_origin]:
            chat_history_dict[message_origin][personality_key] = []

        # Prepare messages for this personality only
        personality_history = chat_history_dict[message_origin][personality_key]

        # Call Ollama with this personality's history (NOW IN A SEPARATE THREAD!)
        ollamamodel = profile.oll_modelname
        response_str = await self.stream_ollama_in_thread(ollamamodel, personality_history, profile, whm)
        
        # Append assistant message to the current personality's history
        personality_history.append({
            'role': 'assistant',
            'content': response_str
        })

        # ALSO log it as a user message in all other personalities' histories
        for doggoprofile in dogprofileslist:
            other_personality = doggoprofile.name
            if other_personality == personality_key:
                continue  # skip the current responding personality

            if other_personality not in chat_history_dict[message_origin]:
                chat_history_dict[message_origin][other_personality] = []

            # Prune if needed
            while len(chat_history_dict[message_origin][other_personality]) >= CHATBOT_MEMORY_BUFFER:
                chat_history_dict[message_origin][other_personality].pop(0)

            chat_history_dict[message_origin][other_personality].append({
                'role': 'user',
                'content': f"{profile.display_name} says: {response_str}"
            })

        await whm.edit(content=response_str)

        # Save updated chat history dict
        with open(f"{path}.json", 'w') as f:
            json.dump(chat_history_dict, f, indent=2)

        # Process next message in queue if exists
        try:
            if self.chat_queue:
                next_msg, next_profile, next_whm = self.chat_queue.pop(0)
                print(f"Processing next in queue. Remaining: {len(self.chat_queue)}")
                await self.chat_with_chatbot(next_msg, next_profile, next_whm)
            else:
                print(f"Queue empty, setting is_busy to False")
                self.is_busy = False
        except Exception as e:
            print(f"Error processing queue: {e}")
            self.is_busy = False


    async def log_user_message(self, message: discord.Message):
        if message.guild is not None:
            message_origin = str(message.guild.id)
        else:
            message_origin = str(message.author.id)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(f"{path}.json"):
            with open(f"{path}.json", 'w') as f:
                json.dump({}, f)
        with open(f"{path}.json", 'r') as f:
            try:
                chat_history_dict = json.load(f)
            except json.JSONDecodeError:
                chat_history_dict = {}

        if message_origin not in chat_history_dict:
            chat_history_dict[message_origin] = {}

        for profile in dogprofileslist:
            personality_key = profile.name
            if personality_key not in chat_history_dict[message_origin]:
                chat_history_dict[message_origin][personality_key] = []

            # Prune if needed
            while len(chat_history_dict[message_origin][personality_key]) >= CHATBOT_MEMORY_BUFFER:
                chat_history_dict[message_origin][personality_key].pop(0)

            chat_history_dict[message_origin][personality_key].append({
                'role': 'user',
                'content': f"{message.author.display_name} says: {message.content}"
            })

        with open(f"{path}.json", 'w') as f:
            json.dump(chat_history_dict, f, indent=2)

    async def sendwebhookmsg(self, message, profile:dogprofiles):
        c = self.bot.get_channel(bottalkchannel)
        chatwebhook = await c.webhooks()
        if chatwebhook:
            chatwebhook = chatwebhook[0]
        else:
            chatwebhook = await c.create_webhook(name="ollamaprofiles")

        webhook_message = await chatwebhook.send(
            content=f"-# Loading...",
            username=f"{profile.display_name}",
            avatar_url=profile.avatar_url,
            wait=True
        )
        return webhook_message


    @commands.Cog.listener("on_message")
    async def on_message_doglogic(self, message: discord.Message):

        if message.channel.id != bottalkchannel: 
            return  # only watch bottalkchannel
        if message.author.bot:
            return  # Ignore bot messages

        await self.log_user_message(message)

        messagelower = message.content.lower()
        found_profiles = []
        is_reply_profile = None
        is_reply = False
        
        # Check if message is a reply
        if message.reference and isinstance(message.reference.resolved, discord.Message):
            is_reply = True
            replied_to = message.reference.resolved
            for profile in dogprofileslist:
                for keyname in profile.keynames:
                    if replied_to.author.name == keyname:
                        found_profiles.append((0, profile))
                        is_reply_profile = profile.name

        # Detect which personalities were mentioned in the message
        for profile in dogprofileslist:
            for keyname in profile.keynames:
                if profile.name == is_reply_profile:
                    continue  # skip replied to doggo
                index = messagelower.find(keyname.lower())
                if index != -1:
                    if is_reply:
                        index += 1  # make sure the replied to doggo is first
                    found_profiles.append((index, profile))
                    break  # Don't match multiple keynames for the same profile
                    
        # Sort found profiles by earliest mention in the message
        found_profiles.sort(key=lambda x: x[0])


        # Random response logic
        if not found_profiles:  # Only if no dogs were mentioned
            if random.random() < self.random_response_chance:
                random_dog = random.choice(dogprofileslist)
                found_profiles.append((0, random_dog))
                print(f"{random_dog.name} randomly decided to respond!")

        # If no profiles found, do nothing
        if not found_profiles:
            return


        # Queue ALL profiles first, then start processing
        for i, (index, profile) in enumerate(found_profiles):
            whm = await self.sendwebhookmsg(message, profile)
            # Calculate queue position AFTER webhook is created
            queue_position = len(self.chat_queue) + 1  # This item's position
            if self.is_busy:
                await whm.edit(content=f"-# (Queue position: {queue_position})")
            else:
                await whm.edit(content=f"-# *Loading...*")
            self.chat_queue.append((message, profile, whm))
            print(f"Queued {profile.name} at position {queue_position}. Queue size: {len(self.chat_queue)}")
        
        # Start processing if not already busy
        if not self.is_busy and self.chat_queue:
            self.is_busy = True
            next_msg, next_profile, next_whm = self.chat_queue.pop(0)
            print(f"Starting chat with {next_profile.name}")
            await self.chat_with_chatbot(next_msg, next_profile, next_whm)


async def setup(bot):
    await bot.add_cog(MessageListener(bot))