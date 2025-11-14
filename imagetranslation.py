#===== Discord.py imports ======
import discord, logging
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext import tasks

#===== Python libraries ======
import random
import requests
import asyncio
import json
import os
import re
import datetime
import ollama
from PIL import Image

#===== Other Files ======
import TokensAndKeys


logging.basicConfig(level=logging.DEBUG)
oll_IMG_MODEL = "gemma3:4b"



class imagey(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def interrogation(self):


        # Load image
        image = Image.open("BotData/barkness.png").convert("RGB")


        ## Call Ollama
        #response_str = ""
        #global ollamamodel
        #response_stream = ollama.chat(model=ollamamodel, messages=personality_history)

        #for chunk in response_stream:
        #    if chunk and response_str == "":
        #        pass
        #print(chunk['message']['content'], end='', flush=True)      # print message to console for debugging

        #response_str += chunk['message']['content']

        pass


import base64

def interrogation():


    # Load image and encode it as base64
    with open("BotData/barkness.png", "rb") as img_file:
        image_bytes = img_file.read()
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    # Send image + prompt to Ollama (LLaVA)
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": oll_IMG_MODEL,
        "prompt": "Describe this image in vivid detail, including the setting, characters (if any), objects, actions, and overall mood.",
        "images": [image_base64],
        "stream": False
    })

    print(response.json()["response"])

interrogation()