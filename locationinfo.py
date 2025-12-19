import requests
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo 
import json
from TokensAndKeys import MYEMAIL as ToK

async def lookup_place(place_name):
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
        "User-Agent": f"silly_python_project_im_new_i_hope_this_header_is_ok/1.0 ({ToK.myemail})"  # required
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
    print(address)
    print(name)
    placename = (f"{name}, {country}")
    if results.get("addresstype") == "country":
        placename = country
    lat = float(results.get("lat", 0.0))
    lon = float(results.get("lon", 0.0))

    #print("📍 Place:", placename)
    #print(json.dumps(results, indent=2)) #, sort_keys=True
    return (placename, lat, lon)


async def gettime(whatplace):
    placename, lat, lon = await lookup_place(whatplace)
    #print(f"📍 Place: {str(placename)}")
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=lat, lng=lon)

    tz = ZoneInfo(timezone_str)
    now = datetime.now(tz)

    # Formatted time
    timeformatted = now.strftime("%-I:%M%p").lower() # e.g., 4:38pm
    abbrev = now.strftime("%Z")                      # e.g., EDT

    # GMT offset in hours
    offset_hours = now.utcoffset().total_seconds() / 3600
    offset_sign = "+" if offset_hours >= 0 else "-"
    gmt_offset = f"{offset_sign}{abs(int(offset_hours))}"

    dst_info = ""
    dst_active = now.dst() != timedelta(0)

    next_change = None
    current_dst = now.dst()
    date_iter = now
    for _ in range(365):  # check next year max
        date_iter += timedelta(days=1)
        if date_iter.dst() != current_dst:
            # handle Windows vs Unix strftime day format
            #day_format = "%-d" if os.name != "nt" else "%#d" 
            #next_change = date_iter.strftime(f"%b {day_format}, %Y")
            next_change = date_iter.strftime("%b %-d") #, %Y
            if dst_active:
                dst_info = f"Daylight Savings ends {next_change}"
            else:
                dst_info = f"Daylight Savings starts {next_change}"
            break
        else:
            dst_info = "Does not observe Daylight Savings"

    #🕒
    string = (f"Time in {placename}: **{timeformatted}**\n"
           f"-# GMT{gmt_offset}  ({abbrev})  •  {dst_info}")
    return string.rstrip()

async def get_weather(whatplace):
    placename, lat, lon = await lookup_place(whatplace)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        #"hourly": "rain,showers,snowfall,temperature_2m,apparent_temperature,precipitation_probability,precipitation,wind_speed_10m,sunshine_duration",
        #"current": "temperature_2m,apparent_temperature,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
        "current_weather": True,
        "timezone": "auto",
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit":"fahrenheit",
        "wind_speed_unit":"mph",
        "hourly": "windspeed_10m,winddirection_10m",
        #"daily":"temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,daylight_duration,sunshine_duration,precipitation_hours,precipitation_probability_max,precipitation_sum,snowfall_sum,showers_sum,rain_sum"

    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    print(json.dumps(data, indent=2)) #, sort_keys=True


    
    # --- Current Weather ---
    current = data.get("current_weather", {})
    temperature = current.get("temperature")
    windspeed = current.get("windspeed")
    weathercode = current.get("weathercode")
    time = current.get("time")

    # --- Daily Forecast (today only) ---
    daily = data.get("daily", {})
    t_min = daily.get("temperature_2m_min", [None])[0]  # default to [None] in case list missing
    t_max = daily.get("temperature_2m_max", [None])[0]
    date_today = daily.get("time", [None])[0]

    # --- Print nicely ---
    print(f"📍 Weather for {date_today}")
    print(f"Current Temperature: {temperature}°C")
    print(f"Today's Low: {t_min}°C / High: {t_max}°C")
    print(f"Wind Speed: {windspeed} km/h")
    print(f"Reported at: {time}")


    # --hourly wind

    hourly = data.get("hourly", {})
    windspeeds = hourly.get("windspeed_10m", [])
    directions = hourly.get("winddirection_10m", [])
    times = hourly.get("time", [])

    # Map wind direction (degrees) to arrow emoji
    def arrow_for_angle(angle):
        # 8 main directions (N, NE, E, SE, S, SW, W, NW)
        arrows = ["⬆️", "↗️", "➡️", "↘️", "⬇️", "↙️", "⬅️", "↖️"]
        # divide angle into 8 slices of 45 degrees each
        index = round(angle / 45) % 8
        return arrows[index]

    # Print next 24 hours
    print("🌀 Hourly wind forecast:")
    for t, ws, wd in zip(times[:24], windspeeds[:24], directions[:24]):
        # Convert time to readable format
        hour = datetime.fromisoformat(t).strftime("%H:%M")
        arrow = arrow_for_angle(wd)
        print(f"{hour}: {ws} km/h {wd}{arrow}")

    return data

if __name__ == "__main__":
    lat = 39.2904   # example: Baltimore, MD
    lon = -76.6122
    import asyncio


    weather =asyncio.run(get_weather("owings mills"))


    #asyncio.run(gettime("maryland"))


    #print(weather)  # inspect what the JSON gives



    # Extract current weather
    #current = weather.get("current_weather")"""  """
    #if current:
    #    print("Current temperature:", current.get("temperature"))
    ## Extract hourly
    #hourly = weather.get("hourly", {})
    #times = hourly.get("time", [])
    #temps = hourly.get("temperature_2m", [])
    #for t, temp in zip(times, temps):
    #    print(t, temp)



