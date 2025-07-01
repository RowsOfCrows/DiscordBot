import discord
from discord.ext import commands
from discord import app_commands
import redditapi

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


def setup(bot):
    bot.add_command(reddithot)
    bot.add_command(redditnew)