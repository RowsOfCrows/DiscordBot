import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import tasks
import datetime
import os

#~~~~~~~~~~~~~
# Calendar Images
#~~

async def get_day_suffix(day):
    """Return the appropriate suffix for a given day."""
    if 10 <= day % 100 <= 20:  # Handle 11th, 12th, 13th
        return 'th'
    else:
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

async def save_last_posted_date(date_str):
    with open('BotData/last_posted_cal_img_date.txt', 'w') as file:
        file.write(date_str)

async def load_last_posted_date():
    if os.path.exists('BotData/last_posted_cal_img_date.txt'):
        with open('BotData/last_posted_cal_img_date.txt', 'r') as file:
            return file.read().strip()
    return None

#~~ Progress Bars

def progress_bar(percentage, bar_length=20):
    filled_length = int(bar_length * percentage)
    bar = '▓' * filled_length + '░' * (bar_length - filled_length)
    return f'{bar} {percentage * 100:.0f}%'

def year_progress(date=None):
    if date is None:
        date = datetime.datetime.now()
    start_of_year = datetime.datetime(date.year, 1, 1)
    end_of_year = datetime.datetime(date.year + 1, 1, 1)
    progress = (date - start_of_year) / (end_of_year - start_of_year)
    return progress

def month_progress(date=None):
    if date is None:
        date = datetime.datetime.now()
    start_of_month = datetime.datetime(date.year, date.month, 1)
    if date.month == 12:
        next_month = datetime.datetime(date.year + 1, 1, 1)
    else:
        next_month = datetime.datetime(date.year, date.month + 1, 1)
    progress = (date - start_of_month) / (next_month - start_of_month)
    return progress

#~~ Cog

class CogCalendar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.calendar_image_folder = "BotData/anime_calendar_images"
        self.last_posted_cal_img_date = None
        self.checkcalendardaychange.start()  # start the loop when the cog loads
        print("CalendarExt loaded!")  

    def cog_unload(self):
        self.checkcalendardaychange.cancel()  # clean up when cog is unloaded
        print("CalendarExt unloaded!")


    @app_commands.command(name="calendar_search", description="Search for a calendar image by month and day.")
    @app_commands.describe(month="Month Name", day="Day of the month (e.g. 15)")
    @app_commands.choices(month=[
            app_commands.Choice(name="January", value="January"),
            app_commands.Choice(name="February", value="February"),
            app_commands.Choice(name="March", value="March"),
            app_commands.Choice(name="April", value="April"),
            app_commands.Choice(name="May", value="May"),
            app_commands.Choice(name="June", value="June"),
            app_commands.Choice(name="July", value="July"),
            app_commands.Choice(name="August", value="August"),
            app_commands.Choice(name="September", value="September"),
            app_commands.Choice(name="October", value="October"),
            app_commands.Choice(name="November", value="November"),
            app_commands.Choice(name="December", value="December")
        ])
    async def calendarsearch(self, interaction: discord.Interaction, month: str, day: int):
        await interaction.response.defer()  # Optional: useful if searching takes time

        # Format the filename to search
        #search_date = f"{month.capitalize()} {day}"
        suffix = await get_day_suffix(day)
        search_date = f"{month} {day}{suffix}"
        found = False

        # Search for matching file
        for file in os.listdir(self.calendar_image_folder):
            if file.startswith(search_date):
                file_path = os.path.join(self.calendar_image_folder, file)
                await interaction.followup.send(content=f"**# {search_date}**",
                                                file=discord.File(file_path))
                found = True
                break

        if not found:
            await interaction.followup.send(f"No calendar image found for **{search_date}**.")


    @tasks.loop(seconds=735) #12 minutes 15 seconds
    async def checkcalendardaychange(self):
        #await self.bot.wait_until_ready() #need beforeloop now
        cal_channel = self.bot.get_channel(1382619573890842755)

        current_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=-5)
        current_day = current_time.day
        current_month = current_time.strftime("%B")
        current_date_str = f"{current_month} {current_day}"
        suffix = await get_day_suffix(current_day)

        print(f"Calendar Check... Current date: {current_date_str} | Last posted: {self.last_posted_cal_img_date}")

        if current_date_str != self.last_posted_cal_img_date:
            filename = f"{current_date_str}{suffix}"
            for file in os.listdir(self.calendar_image_folder):
                if file.startswith(f"{filename}"):
                    file_path = os.path.join(self.calendar_image_folder, file)
                    await cal_channel.send( content=f"**# {current_date_str}{suffix}**"
                                                    f"Year Progress: `  {progress_bar(year_progress())}`\n"
                                                    f"Month Progress: `{progress_bar(month_progress())}`",
                                            file=discord.File(file_path))
                    self.last_posted_cal_img_date = current_date_str
                    await save_last_posted_date(current_date_str)
        
    @checkcalendardaychange.before_loop
    async def before_check(self):
        print("Waiting for bot to be ready before starting calendar check...")
        await self.bot.wait_until_ready()
        print("Bot is ready. Starting calendar check loop.")
        self.last_posted_cal_img_date = await load_last_posted_date()
        print(f"Loaded last calendar date on startup: {self.last_posted_cal_img_date}")

async def setup(bot):
    await bot.add_cog(CogCalendar(bot))