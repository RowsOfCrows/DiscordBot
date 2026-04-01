import asyncpraw
from TokensAndKeys import REDDIT_API_CREDS
import asyncio
import random
from datetime import datetime, timezone
import asyncprawcore

import discord
from discord.ext import commands
from discord import app_commands
import re
#===================
#===================================

REDDIT_POST_PATTERN = re.compile(
    r"https?://(?:www\.)?reddit\.com/r/([^/]+)/comments/([a-zA-Z0-9_]+)(?:/[^/\s]+)?(?:/([a-zA-Z0-9_]+))?"
)

class redditAPIstuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.reddit = asyncpraw.Reddit(
            client_id = REDDIT_API_CREDS["client_id"],
            client_secret = REDDIT_API_CREDS["client_secret"],
            user_agent = REDDIT_API_CREDS["user_agent"],
        )

    @commands.Cog.listener("on_message")
    async def on_message_redditapimsg(self, message: discord.Message):
        if message.author.bot:
            return

        matches = REDDIT_POST_PATTERN.search(message.content) # finds first only, .findall for all
        if not matches:
            return

        try:
            submission = await self.reddit.submission(url=matches.group(0))

            the_embed = await self.createredditembed(submission)
            the_embed2 = await self.createredditembed(submission)
            the_embed3 = await self.createredditembed(submission)
            the_embed4 = await self.createredditembed(submission)

            #await message.channel.send(embed=the_embed)
            await message.channel.send(content="hellochat", embeds=[the_embed]) #

        except Exception as e:
            print(f"Failed to fetch Reddit post: {e}")


#====================================
# Create Discord Embed
#=====================
    async def createredditembed(self, submission):
        
        #randomhexcolor = int("%06x" % random.randint(0, 0xFFFFFF), 16)
        formatted_time = await self.time_ago(submission.created_utc)
        author = submission.author.name if submission.author else "[deleted]"

        def truncate(text: str, limit: int) -> str:
            return text if len(text) <= limit else text[:limit - 3] + "..."

        selftext = ""
        if submission.selftext:
            selftext = truncate(submission.selftext, 4096)

        embedthis = discord.Embed(title=f"{submission.title}",
                                url=f"{submission.url}",
                                description=f"{selftext}",
                                color=0xff782b)
        
        if submission.is_self == False: 
            if submission.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                embedthis.set_image(url=submission.url)

        #TODO possible add selftext truncated text to another field
        #if moreselftext:
        #    embedthis.add_field(name="",
        #                        value=truncate(moreselftext, 1024) if moreselftext else "",
        #                        inline=False
        #                        )

        footer_text = (f"r/{submission.subreddit} • ⬆️{submission.score} • 💬{submission.num_comments} • Author: {author} • {formatted_time}")
        embedthis.set_footer(text=truncate(footer_text, 2048))
        return embedthis
    
    async def time_ago(self, utc_timestamp):
        now = datetime.now(timezone.utc)
        dt_object = datetime.fromtimestamp(utc_timestamp, timezone.utc)
        diff = now - dt_object

        seconds = int(diff.total_seconds())
        minutes = seconds // 60
        hours   = minutes // 60
        days    = seconds // 86400
        weeks   = days // 7
        months  = days // 30
        years   = days // 365

        if seconds < 60:
            return "just now"
        elif minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif hours < 24:
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif days < 7:
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif weeks < 4:
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif months < 12:
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            remaining_months = months % 12
            if remaining_months == 0:
                return f"{years} year{'s' if years != 1 else ''} ago"
            return f"{years} year{'s' if years != 1 else ''} {remaining_months} month{'s' if remaining_months != 1 else ''} ago"

    def cog_unload(self):
        # Clean up the aiohttp session asyncpraw uses internally
        self.bot.loop.create_task(self.reddit.close())

async def setup(bot):
    await bot.add_cog(redditAPIstuff(bot))
