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
from TokensAndKeys import oll_winpc_host, oll_ubupc_local_host


bottalkchannel = 1382296618677571654
bottalkchannelobject = discord.Object(id=bottalkchannel) 

ollamamodel = "DogAI"
oll_host = oll_ubupc_local_host

chat_queue = []
CHATBOT_MEMORY_BUFFER = 200
pathtest = "BotData/bot_talk/chat_history_test"
path = "BotData/chat_history"

is_busy = False

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
    keynames = ["DogAI", "Dagi"],
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

        # Call Ollama with this personality's history
        response_str = ""
        ollamamodel = profile.oll_modelname
        response_stream = ollama.chat(model=ollamamodel, messages=personality_history, stream=True)

        for chunk in response_stream:
            if chunk and response_str == "":
                await whm.edit(content=f"-# *{profile.name} is typing...*")
            print(chunk['message']['content'], end='', flush=True)      # print message to console for debugging

            response_str += chunk['message']['content']
            if any(punct in chunk['message']['content'] for punct in ".!?"):
                await asyncio.sleep(1)
                await whm.edit(content=response_str + f"\n-# *{profile.name} is typing...*")
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
        global chat_queue
        global is_busy
        try:
            if chat_queue:
                next_msg, next_profile, next_whm = chat_queue.pop(0)
                print(f"Queue size after processing: {len(chat_queue)}")
                await self.chat_with_chatbot(next_msg, next_profile, next_whm)
            else:
                print(f" \n\n\n now not busy!!!\n\n\n")
                is_busy = False
        except Exception as e:
            print(f"Error processing queue: {e}")
            is_busy = False

        #if chat_queue:
        #    next_msg, next_profile, next_whm = chat_queue.pop(0)
        #    await self.chat_with_chatbot(next_msg, next_profile, next_whm)
        #else:
        #    print(f" \n\n\n now not busy!!!\n\n\n")
        #    is_busy = False



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
            chatwebhook = await bottalkchannel.create_webhook(name="ollamaprofiles")

        webhook_message = await chatwebhook.send(
            content=f"-# Loading...",
            username=f"{profile.display_name}",
            avatar_url=profile.avatar_url,
            wait=True
        )
        return webhook_message



    @commands.Cog.listener("on_message")
    async def on_message2(self, message: discord.Message):

        if message.channel.id != bottalkchannel: 
            return  # only watch bottalkchannel
        if message.author.bot:
            return  # Ignore bot messages

        await self.log_user_message(message)

        messagelower = message.content.lower()
        found_profiles = []
        is_reply_profile = None
        is_reply = False
        #client.user in message.mentions #if the bot gets mentioned
        if message.reference and isinstance(message.reference.resolved, discord.Message): # add bot profile of who is being replied to
            is_reply = True
            replied_to = message.reference.resolved # regular discord.message obj
            for profile in dogprofileslist:
                for keyname in profile.keynames:
                    if replied_to.author.name == keyname:
                        found_profiles.append((0, profile))
                        is_reply_profile = profile.name
                        #await self.chat_with_chatbot(replied_to, profile)
            # Get the displayed webhook username (if this was a webhook message)
            #print(f"User replied to message from: {replied_to.author.name}")
            #print(f"Content of replied-to message: {replied_to.content}")

        # Detect which personalities were mentioned in the message
        for profile in dogprofileslist:
            for keyname in profile.keynames:
                if profile.name == is_reply_profile:
                    continue #skip replied to doggo
                index = messagelower.find(keyname.lower())
                if index != -1:
                    if is_reply:
                        index += 1 # make sure the replied to doggo is first
                    found_profiles.append((index, profile))
                    break  # Don't match multiple keynames for the same profile
                    
        # Sort found profiles by earliest mention in the message
        found_profiles.sort(key=lambda x: x[0])

        # add messages to queue if it is handling other messages
        #global is_busy
        #if is_busy:
        #    print("bot is busy, chat queue:")
        #    print(f"{chat_queue}")
        #    # send the webhook msg and queue it up
        #    whm = await self.sendwebhookmsg(message, profile)
        #    await whm.edit(content=f"-# (Queue: {len(chat_queue) + 1})")
        #    chat_queue.append((message, profile, whm))
        #    print("\nAFTER APPEND:")
        #    print(chat_queue)
        #    return
        #is_busy = True


        for index, profile in found_profiles:
            await self.chat_with_chatbot(message, profile)

#~~~~


async def setup(bot):
    await bot.add_cog(MessageListener(bot))