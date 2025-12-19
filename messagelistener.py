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

import aiohttp
import base64
from io import BytesIO
from PIL import Image

from concurrent.futures import ThreadPoolExecutor
from TokensAndKeys import oll_winpc_host, oll_ubupc_local_host

import dogprompts

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
    dogprompts: str = None
    avatar_url: str = None

barkness = dogprofiles(
    name = "Barkness",
    oll_modelname = "BarknessV1",
    keynames = ["Barkness", "Barky", "Darkness"],
    display_name = "Barkness",
    dogprompts = dogprompts.BARKNESSPROMPT,
    avatar_url = "https://raw.githubusercontent.com/Relevant-Name/DiscordBot/main/BotData/barkness.png"
)

axiom = dogprofiles(
    name = "Axiom",
    oll_modelname = "AxiomV1",
    keynames = ["Axiom", "Axi"],
    display_name = "Axiom",
    dogprompts = dogprompts.AXIOMPROMPT,
    avatar_url = "https://raw.githubusercontent.com/Relevant-Name/DiscordBot/main/BotData/Axiom.png"
)

dogai = dogprofiles(
    name = "DogAI",
    oll_modelname = "DogAI",
    keynames = ["DogAI", "Dagi", "daggi"],
    display_name = "DogAI",
    dogprompts = dogprompts.DOGAIPROMPT,
    avatar_url = "https://raw.githubusercontent.com/Relevant-Name/DiscordBot/main/BotData/DogAI.png"
)

jack = dogprofiles(
    name = "Jack",
    oll_modelname = "JackdogV1",
    keynames = ["Jack", "goodboye"],
    display_name = "Jack",
    dogprompts = dogprompts.JACKPROMPT,
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

        self.random_response_chance = 0.7  # 0.1 = 10% chance to respond randomly
        self.last_webhook_send = 0  # Track last webhook send time
        self.webhook_cooldown = 1.0  # 1 second between webhook sends
        self.session = aiohttp.ClientSession()
    
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
            # Calculate queue position after webhook is created
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

        # Modifying the payload message
        # Check for image in the message
        imgurl = await self.get_image_from_message(usr_msg)
        if imgurl:
            await whm.edit(content="-# loading image description...")
            print(f"Image URL found: {imgurl}")
            description = await self.send_img_to_interrogate(imgurl, usr_msg.content)
            print(f"Image description: {description}\n")
            # Append image description to the last user message 
            personality_history[-1]['content'] += f"\nDescription of image the user posted: {description}"
            await self.log_append_image_description(usr_msg, description)
        # Insert empty assistant message before the last user message (if history exists)
        if len(personality_history) > 0:
            personality_history = personality_history[:-1] + [
                {"role": "assistant", "content": ""}
            ] + personality_history[-1:]
        
        # Call Ollama with this personalities history
        ollamamodel = profile.oll_modelname
        response_str = await self.stream_ollama_in_thread(ollamamodel, personality_history, profile, whm)
        
        # Append assistant message to the current personalities history
        personality_history.append({
            'role': 'assistant',
            'content': response_str
        })

        # log it as a user message in all other personalities histories
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

        description = description.strip("\n")
        await whm.edit(content=f"{response_str} \n\n-# [Image description that is usually terribly wrong] {description}")

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

    async def log_append_image_description(self, message, description):
        if message.guild is not None:
            message_origin = str(message.guild.id)
        else:
            message_origin = str(message.author.id)

        with open(f"{path}.json", "r") as f:
            chat_history_dict = json.load(f)

        for profile in dogprofileslist:
            history = chat_history_dict[message_origin][profile.name]
            if not history:
                continue

            # last message is guaranteed to be the user message you logged
            history[-1]["content"] += (
                f"\nDescription of image the user posted: {description}"
            )

        with open(f"{path}.json", "w") as f:
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


    async def send_img_to_interrogate(self, image_url, msg):
        try:
            image_base64 = await self.url_to_base64(image_url)

            async with self.session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "bakllava",
                    "prompt": "describe this image in detail ",
                    "images": [image_base64],
                    "stream": False
                }
            ) as resp:
                result = await resp.json()
                return result.get("response", "Could Not Describe Image")

        except Exception as e:
            print(f"Error in interrogation: {e}")
            return f"Error: {e}"


    async def url_to_base64(self, url):
        async with self.session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"Failed to download image: {resp.status}")
            image_bytes = await resp.read()
            return base64.b64encode(image_bytes).decode("utf-8")


    async def get_image_from_message(self, message):
        """
        Gets an image URL from a Discord message.
        Returns the URL as a string, or None if no image found.
        """
        # Check attachments first (uploaded files)
        if message.attachments:
            for attachment in message.attachments:
                # Check if it's an image by file extension or content type
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    return attachment.url
        
        # Check embeds (like when someone posts a link and it auto-embeds)
        if message.embeds:
            for embed in message.embeds:
                if embed.image:
                    return embed.image.url
                if embed.thumbnail:
                    return embed.thumbnail.url
        
        # Check for direct image URLs in the message content
        import re
        url_pattern = r'(https?://\S+\.(?:png|jpe?g|gif|webp)(?:\?\S*)?)'
        urls = re.findall(url_pattern, message.content, re.IGNORECASE)
        if urls:
            return urls[0]
        
        return None


    async def cog_unload(self):
        await self.session.close()

async def setup(bot):
    await bot.add_cog(MessageListener(bot))