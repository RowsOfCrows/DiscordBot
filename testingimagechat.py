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
from concurrent.futures import ThreadPoolExecutor
from TokensAndKeys import oll_winpc_host, oll_ubupc_local_host
from PIL import Image

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

jack = dogprofiles(
    name = "Jack",
    oll_modelname = "JackdogV1",
    keynames = ["Jack", "goodboye"],
    display_name = "Jack",
    avatar_url = "https://raw.githubusercontent.com/Relevant-Name/DiscordBot/main/BotData/DogAI.png"
)




class supercoolawesome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.imagetestchannel = 1439435399054360596
    @commands.Cog.listener("on_message")
    async def on_message(self, message):
        #imagetestchannelobject = discord.Object(id=imagetestchannel) 

        if message.channel.id != self.imagetestchannel: 
            return
        if message.author.bot:
            return  # Ignore bot messages
        


        imgurl = await self.get_image_from_message(message)
        if not imgurl:
            return  # No image found in the message
        whm = await self.sendwebhookmsg(message, barkness)
        await whm.edit(content="-# loading")
        print(f"Image URL found: {imgurl}")
        description = await self.send_img_to_interrogate(imgurl, message.content)
        print(f"\n\nImage description: {description}\n\n")
        #send image to barky he's so cute
        mylist = []
        messagecontext = (f"{message.author.display_name} says: {message.content}\nRespond to this image the user posted: {description}")
        mylist.append({"role": "user", "content": messagecontext})
        response_str = await self.stream_ollama_in_thread("BarknessV1", mylist, whm)

        #result = await self.send_image_description_to_llm(description, message.content, whm)
        description = description.strip("\n")
        await whm.edit(content=(f"{response_str}\n\n-# [Debug Image Description] {description}"))
        #await message.channel.send(f"Image description: {description}")


    async def send_img_to_interrogate(self, image_url, msg):
        try:
            # Download the image and convert to base64
            image_base64 = await self.url_to_base64(image_url)
            
            async with aiohttp.ClientSession() as session:
                print("[DEBUG] Sending image to interrogation model...")
                async with session.post(
                    'http://localhost:11434/api/generate',
                    json={
                        'model': 'bakllava', 
                        'prompt': "describe this image in detail ",
                        'images': [image_base64],
                        'stream': False
                    }
                ) as resp:
                    result = await resp.json()
                    return result.get('response', 'Could Not Describe Image')
        except Exception as e:
            print(f"Error in interrogation: {e}")
            return f"Error: {str(e)}"

    async def url_to_base64(self, url):
        """
        Downloads an image from a URL and converts it to base64.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()
                    return base64.b64encode(image_bytes).decode('utf-8')
                else:
                    raise Exception(f"Failed to download image: {resp.status}")


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

        

    async def stream_ollama_in_thread(self, ollamamodel, personality_history, whm):
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
                await whm.edit(content=f"-# *typing...*")
                first_chunk = False
            
            response_str += content
            
            if has_punctuation:
                await asyncio.sleep(1)
                await whm.edit(content=response_str + f"\n-# *typing...*")
        
        return response_str

    async def sendwebhookmsg(self, message, profile:dogprofiles):
        c = self.bot.get_channel(self.imagetestchannel)
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






async def setup(bot):
    await bot.add_cog(supercoolawesome(bot))