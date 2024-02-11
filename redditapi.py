import praw
from TokensAndKeys import reddit
import asyncio
import discord
import random
import datetime



#print("Title:", newest_post.title)
#print("Self-Text:", newest_post.selftext)
#print("URL:", newest_post.url)
#print("Author:", newest_post.author)
#print("Created UTC:", newest_post.created_utc)


async def monitor_submissions():
    subreddit = reddit.subreddit('animecalendar')
    # Create a submission stream for the subreddit
    submission_stream = subreddit.stream.submissions()

    # Monitor new submissions with an asynchronous delay to avoid rate-limiting
    for submission in submission_stream:
        print(f"New submission: {submission.title} by {submission.author}")


async def postnewest(desiredsubreddit):
    subreddit = reddit.subreddit(desiredsubreddit) 
    newest_post = next(x for x in subreddit.new(limit=3) if not x.stickied)
    return await createredditembed(newest_post)

async def posthot(desiredsubreddit):
    subreddit = reddit.subreddit(desiredsubreddit) 
    hot_post = next(x for x in subreddit.hot(limit=3) if not x.stickied)
    return await createredditembed(hot_post)


async def calendardm(theuser):
    calendarsubreddit = reddit.subreddit('animecalendar')
    submission_stream = calendarsubreddit.stream.submissions()

    async for submission in submission_stream:
        channel = await theuser.create_dm()
        await channel.send(embed=await createredditembed(submission))
        #await interaction.response.send_message("done",ephemeral=True)

async def testdmme(theuser):
    calendarsubreddit = reddit.subreddit('animecalendar')
    newestpost = calendarsubreddit.new(limit=1).__next__()

    channel = await theuser.create_dm()
    await channel.send(embed=await createredditembed(newestpost))

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
