import datetime
import os
import discord

calendar_image_folder = "BotData\\anime_calendar_images"
month_map = {
    'jan': 'january',
    'feb': 'february',
    'mar': 'march',
    'apr': 'april',
    'may': 'may',
    'jun': 'june',
    'jul': 'july',
    'aug': 'august',
    'sep': 'september',
    'oct': 'october',
    'nov': 'november',
    'dec': 'december'
}

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

def day_progress():
    now = datetime.datetime.now()
    start_of_day = datetime.datetime(now.year, now.month, now.day)
    end_of_day = start_of_day + datetime.timedelta(days=1)
    progress = (now - start_of_day) / (end_of_day - start_of_day)
    return progress

# Display the progress bars
#print("Year Progress:  ", progress_bar(year_progress()))
#print("Month Progress: ", progress_bar(month_progress()))
#print("Day Progress:   ", progress_bar(day_progress()))



#================================
# Testing
#===========

async def dayformatted():
    #if date is None:
    #    date = datetime.datetime.now()
    current_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=-5)
    current_day = current_time.day
    current_month = current_time.strftime("%B")  # Full month name
    #suffix = await get_day_suffix(current_day)
    current_date_str = f"{current_month} {current_day}"#{suffix}  # Format: "May 2nd"
    return current_date_str


async def save_last_posted_date(date_str):
    with open('BotData\\last_posted_cal_img_date.txt', 'w') as file:
        file.write(date_str)

async def load_last_posted_date():
    if os.path.exists('BotData\\last_posted_cal_img_date.txt'):
        with open('BotData\\last_posted_cal_img_date.txt', 'r') as file:
            return file.read().strip()
    return None

async def get_day_suffix(day):
    """Return the appropriate suffix for a given day."""
    if 10 <= day % 100 <= 20:  # Handle 11th, 12th, 13th
        return 'th'
    else:
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

async def find_calendar_file(date):
    for file in os.listdir(calendar_image_folder):
        if file.startswith(date):
            return os.path.join(calendar_image_folder, file)
    return None


async def retrieve_cal_img(date):
    for file in os.listdir(calendar_image_folder):
        if file.startswith(date):
            file_path = os.path.join(calendar_image_folder, file)
            return file_path








