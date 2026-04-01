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
import io

import aiohttp
import base64
from io import BytesIO
from PIL import Image

from concurrent.futures import ThreadPoolExecutor

import src.dogprompts as dogprompts
from src.botfilepaths import LOCALDATA_DIR
LD_DIR_DOGCHATHISTORY = os.path.join(LOCALDATA_DIR, "dog_chat_history")
print(f"[PATH] Saving chat history to: {LD_DIR_DOGCHATHISTORY}.json")

bottalkchannel = 1382296618677571654
bottalkchannelobject = discord.Object(id=bottalkchannel) 

ollamamodel = "DogAI"

chat_queue = []
CHATBOT_MEMORY_BUFFER = 200



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



dogcommand_settings_group = app_commands.Group(name="dogchat", description="Configure settings")


class MessageListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.moeid = bot.get_user(98200277580009472)
        jack.avatar_url = self.bot.user.display_avatar.url
        self.oll_modelname = "llamatest"

        self.chat_queue = []
        self.is_busy = False

        self.random_response_chance = 0  # 0.1 = 10% chance to respond randomly 
        #TODO ADD RANDOM TO COMMAND SO INDIVIDUAL CHANNELS CAN HAVE THEIR OWN RANDOM RESPONSE CHANCES

        self.last_webhook_send = 0  # Track last webhook send time
        self.webhook_cooldown = 1.0  # 1 second between webhook sends
        self.session = aiohttp.ClientSession()

        bot.tree.add_command(dogcommand_settings_group)
    
    @commands.Cog.listener("on_message")
    async def on_message_doglogic(self, message: discord.Message):

        #TODO add a command to turn the webhooky bots on
        #TODO add a command to set the random response chance per channel
        # the history works as per server, not per channel

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


        # Random response logic #TODO random logic per channel
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
            whm = await self.sendwebhookmsg(profile, message)

            if whm is None:
                print(f"[on_dog_logic] Failed to create webhook message - Guild: {message.guild.id}, Channel: {message.channel.id}, Skipping.")
                await self.bot.get_channel(message.channel.id).send(content=f"-# Webhook creation error. Please have your administrator contact Bot Creator.")
                break

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

    async def chat_with_chatbot(self, message: discord.Message, profile: dogprofiles, whm=None):
        if not whm:
            whm = await self.sendwebhookmsg(profile, message)
        await whm.edit(content="-# *Loading...*")

        # Determine conversation key (guild or DM)
        message_origin = str(message.guild.id) if message.guild else str(message.author.id)

        # Load chat history
        os.makedirs(os.path.dirname(LD_DIR_DOGCHATHISTORY), exist_ok=True)
        if not os.path.exists(f"{LD_DIR_DOGCHATHISTORY}.json"):
            with open(f"{LD_DIR_DOGCHATHISTORY}.json", 'w') as f:
                json.dump({}, f)

        with open(f"{LD_DIR_DOGCHATHISTORY}.json", 'r') as f:
            try:
                chat_history_dict = json.load(f)
            except json.JSONDecodeError:
                chat_history_dict = {}

        # Ensure entries exist for this origin and personality
        personality_history = chat_history_dict \
            .setdefault(message_origin, {}) \
            .setdefault(profile.name, [])

        # If the user attached an image, describe it and append the description to the history
        imgurl = await self.get_image_from_message(message)
        if imgurl:
            await whm.edit(content="-# loading image description...")
            print(f"Image URL found: {imgurl}")
            img_description = await self.send_img_to_interrogate(imgurl, message.content)
            print(f"Image description: {img_description}\n")
            personality_history[-1]['content'] += f"\nDescription of image the user posted: {img_description}"
            await self.log_append_image_description(message, img_description)

        # Insert an empty assistant message before the last user message to guide the model
        if personality_history:
            personality_history.insert(-1, {"role": "assistant", "content": ""})

        # Build full history with system prompt, send to Ollama, and post response
        full_history = [{"role": "system", "content": profile.dogprompts}] + personality_history

        try:
            response_str = await self.stream_ollama_in_thread(self.oll_modelname, full_history, profile, whm,
                                                            imgurl=imgurl, img_description=img_description if imgurl else None
                                                            )

            # Save the assistant's response to this personality's history
            personality_history.append({"role": "assistant", "content": response_str})

            # Log this response as a user message in all other personalities' histories
            for other_profile in dogprofileslist:
                if other_profile.name == profile.name:
                    continue

                other_history = chat_history_dict[message_origin].setdefault(other_profile.name, [])

                while len(other_history) >= CHATBOT_MEMORY_BUFFER:
                    other_history.pop(0)

                other_history.append({
                    "role": "user",
                    "content": f"{profile.display_name} says: {response_str}"
                })

            # Remove the empty assistant placeholder before saving
            personality_history = [msg for msg in personality_history if not (msg["role"] == "assistant" and msg["content"] == "")]
            chat_history_dict[message_origin][profile.name] = personality_history

            # Save updated history to disk
            with open(f"{LD_DIR_DOGCHATHISTORY}.json", 'w') as f:
                json.dump(chat_history_dict, f, indent=2)

        except Exception as e:
            print(f"[Chat_With_Chatbot] Error processing ollama response, response not saved: {e}")


        # Process the next queued message if one exists
        try:
            if self.chat_queue:
                next_msg, next_profile, next_whm = self.chat_queue.pop(0)
                print(f"Processing next in queue. Remaining: {len(self.chat_queue)}")
                await self.chat_with_chatbot(next_msg, next_profile, next_whm)
            else:
                print("Queue empty, setting is_busy to False")
                self.is_busy = False
        except Exception as e:
            print(f"Error processing queue: {e}")
            self.is_busy = False


    async def log_user_message(self, message: discord.Message):
        if message.guild is not None:
            message_origin = str(message.guild.id)
        else:
            message_origin = str(message.author.id)

        os.makedirs(os.path.dirname(LD_DIR_DOGCHATHISTORY), exist_ok=True)
        if not os.path.exists(f"{LD_DIR_DOGCHATHISTORY}.json"):
            with open(f"{LD_DIR_DOGCHATHISTORY}.json", 'w') as f:
                json.dump({}, f)
        with open(f"{LD_DIR_DOGCHATHISTORY}.json", 'r') as f:
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

        with open(f"{LD_DIR_DOGCHATHISTORY}.json", 'w') as f:
            json.dump(chat_history_dict, f, indent=2)
        print(f"[SAVE] {message_origin} saved.")

    async def log_append_image_description(self, message: discord.Message, description):
        if message.guild is not None:
            message_origin = str(message.guild.id)
        else:
            message_origin = str(message.author.id)

        with open(f"{LD_DIR_DOGCHATHISTORY}.json", "r") as f:
            chat_history_dict = json.load(f)

        for profile in dogprofileslist:
            history = chat_history_dict[message_origin][profile.name]
            if not history:
                continue

            # last message is guaranteed to be the user message you logged
            history[-1]["content"] += (
                f"\nDescription of image the user posted: {description}"
            )

        with open(f"{LD_DIR_DOGCHATHISTORY}.json", "w") as f:
            json.dump(chat_history_dict, f, indent=2)

    async def sendwebhookmsg(self, profile:dogprofiles, message: discord.Message):
        c = self.bot.get_channel(message.channel.id)
        #c = self.bot.get_channel(bottalkchannel) 
        try:
            chatwebhook = await c.webhooks()
            if chatwebhook:
                chatwebhook = chatwebhook[0]
            else:
                chatwebhook = await c.create_webhook(name="ollamaprofiles")
        except Exception as e:
            print(f"[Sendwebhookmsg] Error creating/getting webhook: {e}")
            #TODO idk what to do exactly 
            #TODO fallback to sending normal message if webhook fails
            print(f"[Sendwebhookmsg] Failed to create webhook message - Guild: {message.guild.id}, Channel: {message.channel.id}")
            #await self.bot.get_channel(message.channel.id).send(content=f"-# Webhook creation error. Please have your administrator contact Bot Creator.")

            return None

        webhook_message = await chatwebhook.send(
            content=f"-# Loading...",
            username=f"{profile.display_name}",
            avatar_url=profile.avatar_url,
            wait=True
        )
        return webhook_message

    async def stream_ollama_in_thread(self, ollamamodel, personality_history, profile, whm, imgurl=None, img_description=None):
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
        
        # Start the blocking call in a thread pool (don't await)
        loop.run_in_executor(executor, blocking_ollama_stream)
        
        # Process chunks as they arrive
        response_str = ""
        first_chunk = True
        #istyping_suffix = f"\n-# *{profile.name} is typing...*"
        MAX_LEN = 2000
        current_message = whm

        counter = 0
        while True:
            item = await chunk_queue.get()
            if item is None:  # Streaming complete
                break
                
            content, has_punctuation = item
            
            if first_chunk and response_str == "":
                await current_message.edit(content=f"-# *{profile.name} is typing...*")
                first_chunk = False
            
            # Check if adding this chunk would overflow the current message
            if len(response_str) + len(content) > MAX_LEN:
                print("Max message length reached, sending new webhook msg.")
                # Finalize the current message (remove the typing suffix)
                await current_message.edit(content=response_str)
                # Start a new message
                current_message = await self.sendwebhookmsg(profile)
                response_str = ""


            response_str += content
            
            if has_punctuation:
                await asyncio.sleep(1)
                await current_message.edit(content=response_str + f"\n-# *{profile.name} is typing...*")

        # send last update without the typing suffix
        if imgurl:
            description_inline = img_description.replace("\n", " ")
            debug_suffix = f"\n\n-# {description_inline}"
            # Truncate response_str if the suffix would push it over the limit
            max_response_len = 2000 - len(debug_suffix)
            await current_message.edit(content=f"{response_str[:max_response_len]}{debug_suffix}")
        else:
            await current_message.edit(content=response_str)

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


            with Image.open(io.BytesIO(image_bytes)) as img:
                img = img.convert("RGB")  # bakllava prefers RGB
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                png_bytes = buf.getvalue()

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


    @app_commands.command(name="toggle", description="enable dog chat")
    async def dogchattoggle(self, interaction: discord.Interaction, place: str,  time: str = None):

        await interaction.response.defer()#wait longer than 3 seconds ty
        await interaction.followup.send("Dog chat enabled! (not really, this command is a placeholder)")

    @app_commands.command(name="random", description="set random dog response chance (0-1)")
    async def dogchattogglerandom(self, interaction: discord.Interaction, place: str,  time: str = None):

        await interaction.response.defer()#wait longer than 3 seconds ty
        await interaction.followup.send(f"Dogs will randomly respond at a rate of %")

    async def cog_unload(self):
        await self.session.close()

async def setup(bot):
    await bot.add_cog(MessageListener(bot))