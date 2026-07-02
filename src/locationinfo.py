"""
Local Time and Weather Commands
"""

import requests
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo 
import json
from TokensAndKeys import MYEMAIL
from datetime import datetime, timedelta, timezone
from discord.ext import commands
import discord
import asyncio
from discord import app_commands
from dataclasses import dataclass, fields

#import weather_temp_graph
#import weather_sun_graph

import astral
from astral.sun import sun

@dataclass
class Place:
    name: str
    lat: float
    lon: float
    tz: ZoneInfo


@dataclass
class CurrentWeather:
    time: str | None = None
    temp: float | None = None
    date: str | None = None
    temp_low: float | None = None
    temp_high: float | None = None
    temp_apparent: float | None = None

    wind_speed: float | None = None
    wind_direction: int | None = None
    wind_gusts: float | None = None
    precipitation: float | None = None
    rain: float | None = None
    showers: float | None = None
    snowfall: float | None = None
    weather_code: int | None = None

@dataclass
class DailyWeather:
    time: str
    temp: float | None = None
    temp_low: float | None = None
    temp_high: float | None = None
    rain: float | None = None
    showers: float | None = None
    snowfall: float | None = None
    wind_speed: float | None = None
    wind_direction: int | None = None
    precipitation_probability: int | None = None
    precipitation_probability_max: int | None = None
    precipitation: float | None = None
    sunshine_duration: float | None = None
    sunrise: float | None = None
    sunset: float | None = None
    weather_code: int | None = None

@dataclass
class HourlyWeather:
    time: str | None = None
    temp: float | None = None
    temp_apparent: float | None = None
    rain: float | None = None 
    showers: float | None = None
    snowfall: float | None = None
    wind_speed: float | None = None
    wind_direction: int | None = None
    precipitation_probability: int | None = None
    precipitation: float | None = None
    sunshine_duration: float | None = None
    weather_code: int | None = None

@dataclass
class Minutely15Weather:
    time: str | None = None
    temp: float | None = None
    temp_apparent: float | None = None
    precipitation: float | None = None

    rain: float | None = None 
    showers: float | None = None
    snowfall: float | None = None
    wind_speed: float | None = None
    wind_direction: int | None = None
    wind_gusts: float | None = None
    lightning_potential: float | None = None
    weather_code: int | None = None

@dataclass
class WeatherData:
    place_name: str
    lat: float
    lon: float
    tz: ZoneInfo
    current: CurrentWeather
    hourly: list[HourlyWeather]
    daily: list[DailyWeather]
    minutely15: list[Minutely15Weather]


FIELD_ALIASES = {
    "temperature_2m": "temp",
    "apparent_temperature": "temp_apparent",
    "temperature_2m_max": "temp_high",
    "temperature_2m_min": "temp_low",
    "wind_speed_10m": "wind_speed",
    "wind_direction_10m": "wind_direction",
    "wind_gusts_10m":"wind_gusts",
}



# https://github.com/schlpbch/open-meteo-mcp-py/blob/main/docs/WEATHER_CODES.md
WEATHERCODE_DESCRIPTIONS = { 
      # Clear Conditions
    0:  "Clear sky",
    1:  "Mainly clear",
      # Cloudy Conditions
    2:  "Partly cloudy",
    3:  "Overcast",
    5:  "Haze",
    10: "Mist",
      # Fog codes
    45: "Fog",
    48: "Depositing rime fog",
      # Rain
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
      # Snow 
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    79: "Ice Pellets/Sleet",
      # Rain Showers
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
      # Snow Showers
    85: "Slight snow showers",
    86: "Heavy snow showers",
      # Thunderstorms
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    97: "Heavy Thunderstorm",
    99: "Thunderstorm with heavy hail"
}
# Rain is steady and covers a larger area for a longer duration, 
# Showers are short-lived, scattered, and can vary in intensity, affecting only certain areas.

# ───── Edit data saving ───────────────────────────────────────

def remap_keys(d: dict) -> dict:
    return {FIELD_ALIASES.get(k, k): v for k, v in d.items()}

def zip_weather_data(resp: dict, model: type) -> list:
    valid = {f.name for f in fields(model)}
    result = []
    for i in range(len(resp.get("time", []))):
        row = {k: resp.get(k, [None] * len(resp["time"]))[i] for k in resp}
        remapped = remap_keys(row)
        result.append(model(**{k: v for k, v in remapped.items() if k in valid}))
    return result

# ───── Retrieve data ───────────────────────────────────────

async def lookup_location(place_name):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": place_name,
        "format": "json",
        "limit": 1,        
        "accept-language":"en",
        "addressdetails": 1,
        #"namedetails": 1,
        #"extratags": 1
    }
    headers = {
        "User-Agent": f"silly_python_project_im_new_i_hope_this_header_is_ok/1.0 ({MYEMAIL})"  # required
    }

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    results_list = response.json()

    if not results_list:
        return ("Unknown location", 0.0, 0.0)#: {place_name}

    results = results_list[0]


    address = results.get("address", {})
    name = results.get("name")
    country = address.get("country")
    #print(f"lookupplace address: {address}")
    #print(f"lookupplace    name: {name}")
    placename = (f"{name}, {country}")
    if results.get("addresstype") == "country":
        placename = country
    lat = float(results.get("lat", 0.0))
    lon = float(results.get("lon", 0.0))

    #print("📍 Place:", placename)
    #print("lookupplace =========\n")
    #print(json.dumps(results, indent=2)) #, sort_keys=True
    #print("=========\n")
    tf = TimezoneFinder()
    tz_str = tf.timezone_at(lat=lat, lng=lon)
    tz = ZoneInfo(tz_str)

    return Place(name=placename, lat=lat, lon=lon, tz=tz)

async def get_time(place: Place):
    #print(f"📍 Place: {str(placename)}")

    now = datetime.now(place.tz)

    # Formatted time
    timeformatted = now.strftime("%-I:%M%p").lower() # e.g., 4:38pm
    abbrev = now.strftime("%Z")                      # e.g., EDT

    # GMT offset in hours
    offset_hours = now.utcoffset().total_seconds() / 3600
    offset_sign = "+" if offset_hours >= 0 else "-"
    gmt_offset = f"{offset_sign}{abs(int(offset_hours))}"

    dst_info = ""
    dst_active = bool(now.dst()) #dst_active = now.dst() != timedelta(0)

    next_change = None
    current_dst = now.dst()
    date_iter = now
    for _ in range(365):  # check next year max
        date_iter += timedelta(days=1) # Tomorrow
        if date_iter.dst() != current_dst:
            # handle Windows vs Unix strftime day format
            #day_format = "%-d" if os.name != "nt" else "%#d" 
            #next_change = date_iter.strftime(f"%b {day_format}, %Y")
            next_change = date_iter.strftime("%b %-d") #, %Y
            if dst_active:
                dst_info = f"Clocks go back {next_change}" #Ends
            else:
                dst_info = f"Clocks go forward {next_change}" #Starts
            break
        else:
            dst_info = "Does not observe Daylight Savings"

    #🕒
    string = (f"Time in {place.name}: **{timeformatted}**\n"
           f"-# GMT{gmt_offset}  ({abbrev})  •  {dst_info}")
    return string.rstrip()

async def get_weather_data(place:Place) -> WeatherData:
    params_main_all = {        
        "latitude": place.lat,
        "longitude": place.lon,
        "timezone": "auto",
        #"temperature_unit": "fahrenheit",
        #"wind_speed_unit": "mph",

        #"current_weather": True, 
        "current":"temperature_2m,apparent_temperature,"
                  "precipitation,"
                  "wind_gusts_10m,wind_speed_10m,wind_direction_10m,"
                  "weather_code",

        "daily": 
            "temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max,"
            "sunrise,sunset,weather_code",

        "hourly": 
            #"rain,"
            #"showers,"
            #"snowfall,"
            "temperature_2m,"
            "precipitation_probability,"
            "precipitation,"
            "windspeed_10m,winddirection_10m,"
            "weather_code"
            , 
        #"minutely_15": 
        #    "precipitation,"
        #    "rain,"
        #    "weather_code"
        #    , 
        
        #"hourly": "rain,showers,snowfall,temperature_2m,apparent_temperature,precipitation_probability,precipitation,wind_speed_10m,sunshine_duration",
        #"current": "temperature_2m,apparent_temperature,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
        #"daily":"temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,
        #         daylight_duration,sunshine_duration,precipitation_hours,precipitation_probability_max,precipitation_sum,snowfall_sum,showers_sum,rain_sum"
    }
    paramstesting = {        
        "latitude": place.lat,
        "longitude": place.lon,
        "timezone": "auto",
        "minutely_15": 
            "precipitation,"
            "rain,"
            "weather_code"
            , 
            }

    url = "https://api.open-meteo.com/v1/forecast"
    params = params_main_all
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    #current_w_resp = data.get("current_weather", {})
    current_resp = data.get("current", {})
    daily_resp = data.get("daily", {})
    hourly_resp = data.get("hourly", {})
    #minute15_resp = data.get("minutely_15", {})

    print("Weather =========\n")
    #print(json.dumps(data, indent=4))
    #print(data)

    #print(json.dumps(daily_resp, indent=4))

    daily_zip      = zip_weather_data(daily_resp,   DailyWeather)
    hourly_zip     = zip_weather_data(hourly_resp,  HourlyWeather)
    #minutely15_zip = zip_weather_data(minute15_resp, HourlyWeather)

    valid_fields = {f.name for f in fields(CurrentWeather)}
    current = CurrentWeather(**{k: v for k, v in remap_keys(current_resp).items() if k in valid_fields})

    weather_model = WeatherData(
        place_name = place.name,
        lat = place.lat,
        lon = place.lon,
        tz = place.tz,
        current = current,
        hourly = hourly_zip,
        daily = daily_zip,
        #minutely15 = minutely15_zip,
    )

    return weather_model

# ───── Formatting ───────────────────────────────────────

def format_iso_hour(iso_time: str) -> str:
    return datetime.fromisoformat(iso_time).strftime("%b %d %-I%p").lower()

def get_next_24_hours(weather_model: WeatherData) -> list[HourlyWeather]:
    """Returns hourly entries for the next 24 hours from now."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now + timedelta(hours=24)

    return [
        h for h in weather_model.hourly
        if now <= datetime.fromisoformat(h.time) < cutoff
    ]



def get_next_n_hours(w: WeatherData, n) -> list[HourlyWeather]:
    local_tz = w.tz  # or derive from weather_model
    now = datetime.now(local_tz).replace(tzinfo=None, minute=0, second=0, microsecond=0)
    cutoff = now + timedelta(hours=n)

    return [
        h for h in w.hourly
        if now <= datetime.fromisoformat(h.time) < cutoff
    ]

def get_next_n_hours_minute(w: WeatherData, n) -> list[Minutely15Weather]:
    local_tz = w.tz  # or derive from weather_model
    now = datetime.now(local_tz).replace(tzinfo=None, minute=0, second=0, microsecond=0)
    cutoff = now + timedelta(hours=n)

    return [
        h for h in w.minutely15
        if now <= datetime.fromisoformat(h.time) < cutoff
    ]


def format_weather_simple(w: WeatherData) -> str:
    daily = w.daily[0] if w.daily else None
    hourly = w.hourly[0] if w.hourly else None
    return (
        f"Weather for **{w.place_name}**\n"
        f"```ansi\n"
        f"Temp: {w.current.temp}°F feels like {w.current.temp_apparent}\n"
        f"{daily.temp_low}°F / {daily.temp_high}°F\n"  
        f"Wind Speed: {w.current.wind_speed} mph\n"
        f"Precipitation: {daily.precipitation_probability_max}%\n"
        f"```"
    )

def arrow_for_angle(angle): # Map wind direction (degrees) to arrow emoji
    arrows = ["⬆️", "↗️", "➡️", "↘️", "⬇️", "↙️", "⬅️", "↖️"]
    return arrows[round(angle / 45) % 8]

def format_weather_hourly_wind(w: WeatherData) -> str:
    lines = [f"🌀 Hourly wind for **{w.place_name}**:"]
    for row in w.hourly:
        hour = format_iso_hour(row.time)
        lines.append(f"{hour}: {row.windspeed} mph {arrow_for_angle(row.winddirection)}")
    return "\n".join(lines)

def format_weather_daily_forecast(w: WeatherData) -> str:
    lines = [f"Forecast for **{w.place_name}**:"]
    for row in w.daily:
        hi = row.temp_high
        lo = row.temp_low
        precip_chance = row.precipitation_probability_max or 0
        time = datetime.fromisoformat(row.time).strftime("%b %-d").lower()
        lines.append(f"{time}: {hi:.0f}-{lo:.0f}°F, {precip_chance}%")
    return "\n".join(lines)\
    
def format_weather_hourly_forecast(w: WeatherData) -> str:
    lines = [f"🌡️Forecast for **{w.place_name}**:"]
    for row in w.hourly:
        temp = row.temp
        precip_chance = row.precipitation_probability or 0
        time = format_iso_hour(row.time)
        lines.append(f"{time}: {temp}°C, {precip_chance}%")
    return "\n".join(lines)



async def build_weather_embed(w: WeatherData):
    condition = WEATHERCODE_DESCRIPTIONS[w.weathercode]

    embed = discord.Embed(
        title=f"{w.place_name},",
        description=condition.capitalize(),
        color=0x4A7FB5
    )
    embed.add_field(name="Temperature", value=f"{w.temperature}°F", inline=True)
    #embed.add_field(name="Feels like", value=f"{w.date_today}°F", inline=True)
    #embed.add_field(name="Humidity", value=f"{w.time}%", inline=True)
    #embed.add_field(name="Wind", value=f"{w.windspeed} mph", inline=True)

    # forecast is a list of (day_name, condition_emoji, temp) tuples
    #forecast_str = "  ".join([f"{d} {e} {t}°" for d, e, t in forecast])
    #embed.add_field(name="5-day forecast", value=forecast_str, inline=False)

    embed.set_footer(text=f"Updated just now · /weather {w.place_name}")
    return embed


async def prep_astral_data(w: WeatherData):
    lat = w.lat
    long = w.lon
    place_name = w.place_name
    tf = TimezoneFinder()

    timezone_str = tf.timezone_at(lat=lat, lng=long)
    tz = ZoneInfo(timezone_str)
    localtime = datetime.now(tz)

    observer = astral.Observer(latitude=lat, longitude=long)
    s = sun(observer, date=localtime.date())


    daily = w.daily[0]
    sunrise = datetime.fromisoformat(daily.sunrise).replace(tzinfo=tz)
    sunset  = datetime.fromisoformat(daily.sunset).replace(tzinfo=tz)

    #sunrise_astral = s['sunrise'].astimezone(tz)
    #sunset_astral  = s['sunset'].astimezone(tz)
    noon = s['noon'].astimezone(tz)
    dawn = s['dawn'].astimezone(tz)
    dusk = s['dusk'].astimezone(tz)

    #await sun_graph.generate_sun_card(sunrise, sunset, noon, dawn, dusk, localtime) 
    return [sunrise, sunset, noon, dawn, dusk, localtime]

# ────────────────────────────────────────────



weather_settings_group = app_commands.Group(name="weather", description="Weather related commands")


class LocationTools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.guildjackid = 875349586141675582
        self.guildobject = discord.Object(id=self.guildjackid) 
        self.moeidnum = 98200277580009472

    @app_commands.command(name="time", description="the local time of any place!")
    async def time(self, interaction: discord.Interaction, location: str):
        location_data = await lookup_location(location)
        thetimeinplace = await get_time(location_data)
        print(thetimeinplace)
        await interaction.response.send_message(thetimeinplace)
    #===========================================================
    # Weather
    #========
    @app_commands.command(name="weather", description="your local weather, right now")
    async def weather(self, interaction: discord.Interaction, place: str,  time: str = None):

        await interaction.response.defer()#wait longer than 3 seconds ty

        await interaction.followup.send("not implimented", ephemeral=True)


    @app_commands.command(name="weatherembed", description="your local weather, right now")
    async def weatherembed(self, interaction: discord.Interaction, place: str,  time: str = None):
        await interaction.response.defer()#wait longer than 3 seconds ty
        
        await interaction.response.defer()#wait longer than 3 seconds ty
        location_data = await lookup_location(place)
        weatherdata = await get_weather_data(location_data)
        emb = await build_weather_embed(weatherdata)
        await interaction.followup.send(embed=emb)

    @app_commands.command(name="weathersimple", description="your local weather, right now")
    async def weathersimple(self, interaction: discord.Interaction, place: str,  time: str = None):
        await interaction.response.defer()#wait longer than 3 seconds ty
        
        location_data = await lookup_location(place)
        weatherdata = await get_weather_data(location_data)

        formatted = format_weather_simple(weatherdata)
        await interaction.followup.send(formatted)

async def setup(bot):
    await bot.add_cog(LocationTools(bot))
