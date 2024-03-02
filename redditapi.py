import asyncpraw
from TokensAndKeys import redditapicreds
import asyncio
import discord
import random
import datetime
import asyncprawcore

#===================


calandardayimage = None



#=========================#
# Setup the async session # 
# you need to set it up in an async function, that took way too long to find on google
#==========
async def get_reddit_instance():
    async with asyncpraw.Reddit(
        client_id = redditapicreds["client_id"],
        client_secret = redditapicreds["client_secret"],
        user_agent = redditapicreds["user_agent"],
    ) as reddit:
        yield reddit # only returns one session and closes it :)

#========================================
#Post Newest and hot
#===================
async def postnewest(desiredsubreddit):
    async for reddit in get_reddit_instance():
        subreddit = await reddit.subreddit(desiredsubreddit)
        async for x in subreddit.new(limit=3):
            if not x.stickied:
                newest_post = x
                return await createredditembed(newest_post)

async def posthot(desiredsubreddit):
    async for reddit in get_reddit_instance():
        subreddit = await reddit.subreddit(desiredsubreddit)
        async for x in subreddit.hot(limit=3):
            if not x.stickied:
                newest_post = x
                return await createredditembed(newest_post)

#========================
# Testing Debug
#==============

async def test_subreddit_info_name(subreddit_name):
    async for reddit in get_reddit_instance():
        subreddit = await reddit.subreddit(subreddit_name, fetch=True)
        print(subreddit.display_name)


async def test_print5titles():
    async for reddit in get_reddit_instance():
        subreddit = await reddit.subreddit("programming")
        async for submission in subreddit.new(limit=5):
            print(submission.title)


async def testdmme(theuser):
    async for reddit in get_reddit_instance():
        calendarsubreddit = await reddit.subreddit('animecalendar')
        newestpost = calendarsubreddit.new(limit=1).__next__()

        channel = await theuser.create_dm()
        await channel.send(embed=await createredditembed(newestpost))

async def calendardm(theuser): #test submission stream
    async for reddit in get_reddit_instance():
        calendarsubreddit = await reddit.subreddit('animecalendar')
        submission_stream = calendarsubreddit.stream.submissions()

        async for submission in submission_stream:
            channel = await theuser.create_dm()
            await channel.send(embed=await createredditembed(submission))

#========================

async def monitor_calendar_submissions():
    global calandardayimage
    async for reddit in get_reddit_instance():
        subreddit = await reddit.subreddit('all')
        # Create a submission stream for the subreddit
        submission_stream = subreddit.stream.submissions()

        # Monitor new submissions 
        async for submission in submission_stream:
            calandardayimage = submission
            print(f"New submission: {calandardayimage.title} by {calandardayimage.author}")


#====================================
# Create Discord Embed
#=====================
async def createredditembed(redditpost): #the most clear name in the history of me naming anything
    
    #randomhexcolor = int("%06x" % random.randint(0, 0xFFFFFF), 16)

    dt_object = datetime.datetime.utcfromtimestamp(redditpost.created_utc)
    formatted_time = dt_object.strftime('%#m/%#d/%Y %#I:%M%p')

    embedthis = discord.Embed(title=f"{redditpost.title}",
                              url=f"{redditpost.url}",
                              #description="description",
                              color=0xff782b)
    if redditpost.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
        embedthis.set_image(url=redditpost.url)
    else:
        embedthis.add_field(name="",value=f"{redditpost.selftext}", inline=False)
    
    embedthis.set_footer(text=f"{formatted_time} UTC • Author: {redditpost.author}")
    return embedthis


#embedthis.add_field(name="Field 1 Title", value=f"{newest_post.url}", inline=False)



#print("Title:", newest_post.title)
#print("Self-Text:", newest_post.selftext)
#print("URL:", newest_post.url)
#print("Author:", newest_post.author)
#print("Created UTC:", newest_post.created_utc)