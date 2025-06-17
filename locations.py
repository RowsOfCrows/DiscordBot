
import discord
import random
from datetime import datetime, timedelta
import urllib.parse
import TokensAndKeys
import requests


BingMapsKey = TokensAndKeys.bingmapsApiKey
weatherapidotcomkey = TokensAndKeys.WeatherApiDotComKey 
rightnow = datetime.now()
utctime = datetime.utcnow()

emojiDict={
    "moon": "🌙",
    "night":"🌃",
    "mostly Cloudy": "⛅️️",
    "partly Cloudy": "🌤️",
    "cloudy": "☁️",
    "overcast": "☁️",
    "sunny": "🌞",
    "mist":"🌫",
    "Rainbow": "🌈",
    "snowflake": "❄️",
    "snowing": "🌨",
    "raining": "🌧",
    "raining2": "☔️",
    "snowlist": ["❄️", "☃️", "⛄️", "🌨"],
    "rainlist": ["🌧", "☔️", "💦", "💧"]
}

#=====================================
# Retrieve and parse location data
#==========

async def bingGetLocationDataByQuery(locationQuery):
    if type(locationQuery) == str:
        cool = locationQuery
    else:
        cool = ''.join(locationQuery)
    bingplace = requests.get(f"http://dev.virtualearth.net/REST/v1/Locations?query={cool}&key={BingMapsKey}")
    bingjsondata = bingplace.json() if bingplace and bingplace.status_code == 200 else None
    return bingjsondata

async def bingGetLocationDataByCoords(lat,long):
    
    bingplace = requests.get(f"http://dev.virtualearth.net/REST/v1/Locations/{lat},{long}?&key={BingMapsKey}")
    bingjsondata = bingplace.json() if bingplace and bingplace.status_code == 200 else None
    print(f"http://dev.virtualearth.net/REST/v1/Locations/{lat},{long}?&key={BingMapsKey}")
    #http://dev.virtualearth.net/REST/v1/Locations/47.60322952,-122.33027649?&key=AuQX5ztwTTNpJ0flr2pxkaWz_EJSdujIZvz91VBHTw4oFo39aa6hXdyJinlUiw54
    return bingjsondata

async def bingParseNameOfLocation(bingjsondata):
    return bingjsondata["resourceSets"][0]["resources"][0]["name"]

async def bingParseCoords(bingjsondata):
    return bingjsondata["resourceSets"][0]["resources"][0]["point"]["coordinates"]

async def bingParseLocalTime(lat,long):
    timezoneurl = requests.get(f"https://dev.virtualearth.net/REST/v1/TimeZone/{lat},{long}?&key={BingMapsKey}") #?datetime={datetime_utc}
    #print(f"https://dev.virtualearth.net/REST/v1/TimeZone/{coord[0]},{coord[1]}?&key={BingMapsKey}")
    timezonejson = timezoneurl.json() if timezoneurl and timezoneurl.status_code == 200 else None

    timezoneNameAbbrev = timezonejson["resourceSets"][0]["resources"][0]["timeZone"]["abbreviation"]   

    localtime = timezonejson["resourceSets"][0]["resources"][0]["timeZone"]["convertedTime"]["localTime"] #dt_string = "2020-12-18 3:11:09"
    dt_object = datetime.strptime(localtime, "%Y-%m-%dT%H:%M:%S")
    formattedlocaltime = dt_object.strftime(f"%#I:%M %p")
    timeWithAbbrev = f"{formattedlocaltime} {timezoneNameAbbrev}"

    return formattedlocaltime, timezoneNameAbbrev

#===========
# Testing
#========
async def getTimeString(place):
    place2 = ''.join(place) #I have no idea why I wrote this here or like this, it seems redundant but it works so I'm not touching it
    
    if "shugan".lower() == place2.lower():
        place2 = "Belgium"
    if "floyd".lower() == place2.lower():
        place2 = "Melbourne Australia"
    if "moe".lower() == place2.lower():
        place2 = "Maryland"
    
    bingdata = await bingGetLocationDataByQuery(place2)
    placename = await bingParseNameOfLocation(bingdata)
    coordlist = await bingParseCoords(bingdata)
    timethere, abbrev = await bingParseLocalTime(*coordlist)
    string = f"Time in {placename}: **{timethere}** {abbrev}"
     
    return string

async def getWeatherMsg(place):
    #bingdata = bingGetLocationData(place)
    #nameofplace = bingGetNameOfLocation(bingdata)
    
    try:
        weatherdata = getWeatherapidotcomData(place)
        #currentlocationtime = bingLocalTime(bingdata)     
    except Exception as e:
        print("something didnt return prob: ", e)
        return #"something fuck up lol"

    if weatherdata['daily_chance_of_rain'] or weatherdata['daily_chance_of_snow']:
        pass

    thingo =  (f"Weather in **{weatherdata['Location']}**\n"
               f"{weatherdata['condition']}\n"
               f"Temperature: {weatherdata['temp_f']}, {weatherdata['temp_c']}\n"
               f"Feels Like: {weatherdata['feelslike_f']}, {weatherdata['feelslike_c']}\n"
               f"Wind: {weatherdata['wind_mph']} mph, {weatherdata['wind_kph']} kph {weatherdata['wind_dir']}\n"
               ""
               #f"precipitation: {weatherdata['precipitation']}\n"
               #f"rain: {weatherdata['rain']}\n"
               #f"showers: {weatherdata['showers']}\n"
               #f"snowfall: {weatherdata['snowfall']}\n"
               
              )
              #{sundata}
              #{currentlocationtime}"f"snowdepth: {weatherdata['snowdepth']}\n"

    return thingo

########################
#   new weather stuff  #
########################

async def getWeatherapidotcomData(query): #city name, Latitude/Longitude (decimal degree), US Zipcode, UK Postcode, Canada Postalcode, IP address, 
    response = requests.get(f"http://api.weatherapi.com/v1/forecast.json?key={weatherapidotcomkey}&q={query}&days=2&aqi=no&alerts=no")
    weatherjson = response.json() if response and response.status_code == 200 else None

    weatherDict = {}
    try:
        weatherDict['Location'] = weatherjson['location']['name']
        weatherDict['region'] = weatherjson['location']['region']
        weatherDict['country'] = weatherjson['location']['country']
        weatherDict['lat'] = weatherjson['location']['lat']
        weatherDict['long'] = weatherjson['location']['lon']
        weatherDict['is_day'] = weatherjson['current']['is_day']
        weatherDict['localtime'] = datetime.strptime(weatherjson['location']['localtime'], "%Y-%m-%d %H:%M").strftime("%#I:%M %p")

        weatherDict['temp_f'] = int(weatherjson['current']['temp_f'])
        weatherDict['temp_c'] = int(weatherjson['current']['temp_c'])
        weatherDict['feelslike_c'] = int(weatherjson['current']['feelslike_c'])
        weatherDict['feelslike_f'] = int(weatherjson['current']['feelslike_f'])
        weatherDict['hightemp_f'] = int(weatherjson['forecast']['forecastday'][0]['day']['maxtemp_f'])
        weatherDict['hightemp_c'] = int(weatherjson['forecast']['forecastday'][0]['day']['maxtemp_c'])
        weatherDict['lowtemp_f'] = int(weatherjson['forecast']['forecastday'][0]['day']['mintemp_f'])
        weatherDict['lowtemp_c'] = int(weatherjson['forecast']['forecastday'][0]['day']['mintemp_c'])

        weatherDict['daily_chance_of_rain'] = weatherjson['forecast']['forecastday'][0]['day']["daily_chance_of_rain"] if weatherjson['forecast']['forecastday'][0]['day']["daily_will_it_rain"] is not 0 else None
        weatherDict['daily_chance_of_snow'] = weatherjson['forecast']['forecastday'][0]['day']["daily_chance_of_snow"] if weatherjson['forecast']['forecastday'][0]['day']["daily_will_it_snow"] is not 0 else None   

        weatherDict['wind_mph'] = weatherjson['current']['wind_mph']
        weatherDict['wind_kph'] = weatherjson['current']['wind_kph']
        weatherDict['wind_dir'] = weatherjson['current']['wind_dir']

        weatherDict['humidity'] = weatherjson['current']['humidity']
        weatherDict['cloud'] = weatherjson['current']['cloud']

        weatherDict['textcondition'] = weatherjson['current']['condition']['text']
        weatherDict['icon'] = weatherjson['current']['condition']['icon']

        weatherDict['sunrise'] = weatherjson['forecast']['forecastday'][0]['astro']['sunrise'].lstrip('0')
        weatherDict['sunset'] = weatherjson['forecast']['forecastday'][0]['astro']['sunset'].lstrip('0')
        weatherDict['moon_phase'] = weatherjson['forecast']['forecastday'][0]['astro']['moon_phase']
        weatherDict['moon_illumination'] = weatherjson['forecast']['forecastday'][0]['astro']['moon_illumination']
    except KeyError as e:
        print("weatherdict key error: ", e)

    return weatherDict

async def sunDayLength(lat, long):

    sunApiPlace = requests.get(f"https://api.sunrise-sunset.org/json?lat={lat}&lng={long}&date=today")
    sunjson = sunApiPlace.json() if sunApiPlace and sunApiPlace.status_code == 200 else None
    daylengthraw = sunjson["results"]['day_length'] # 09:51:59 h m s
    parse = datetime.strptime(daylengthraw, "%H:%M:%S")
    daylength = parse.strftime("%#Hh %Mm")
    return daylength

async def getWeatherEmoji(weatherdata):
    if weatherdata['textcondition'].lower() == emojiDict:
        emoji = emojiDict[weatherdata['textcondition']]
    elif "rain"   in weatherdata['textcondition'].lower():
        emoji = emojiDict['raining']
    elif "cloudy" in weatherdata['textcondition'].lower():
        emoji = emojiDict['cloudy']
    elif "mist"   in weatherdata['textcondition'].lower():
        emoji = emojiDict['mist']
    elif "snow"   in weatherdata['textcondition'].lower():
        emoji = emojiDict['snowflake']
    elif weatherdata['is_day'] == 1:
        emoji = emojiDict['sunny']
    else:
        emoji = emojiDict['moon']
    
    return emoji

async def createweatherembedboxes(place):

    locationjson = await bingGetLocationDataByQuery(place)
    coords = await bingParseCoords(locationjson)
    nameoflocation = await bingParseNameOfLocation(locationjson)

    weatherdata = await getWeatherapidotcomData(','.join(map(str, coords)))
    daylength = await sunDayLength(weatherdata['lat'],weatherdata['long'])

    if weatherdata['is_day'] == 1:
        daytimehexcolor=0x0ba4ff
    else:
        daytimehexcolor=0x2d626b
    
    #fulllocation = (f"{weatherdata['Location']}, {weatherdata['region']},\n{weatherdata['country']}")

    
    emoji = await getWeatherEmoji(weatherdata)


    try: 
        weatherembed = discord.Embed(title=f"Weather in {nameoflocation}", 
                                     url="https://www.accuweather.com/en/us/national/weather-radar", 
                                     description=f"", 
                                     color=daytimehexcolor)
        #weatherembed.set_author(name=f"someone", 
        #                    url="", 
        #                    icon_url=f"https:{weatherdata['icon']}")
        #weatherembed.add_field(name=f"Weather in {nameoflocation}",
        #                        value=f"",inline=False)  

     
        weatherembed.add_field(name="",
                                value=f"```ansi\n\u001b[0;0m"
                                         f"{weatherdata['localtime']}"
                                         f"         \u001b[1;34m"
                                         f"{weatherdata['temp_f']}°F • {weatherdata['temp_c']}°C"
                                         f"        \u001b[0;0m"
                                         f"{weatherdata['textcondition']}{emoji} ```", inline=False)  
        

    
        weatherembed.add_field(name = chr(173), value = chr(173), inline=True)

        weatherembed.add_field(name=" Feels Like",
                                value=f"```ansi\n\u001b[0;34m {weatherdata['feelslike_f']}°F • {weatherdata['feelslike_c']}°C```", inline=True)

        weatherembed.add_field(name="⬆⬇ High, Low",
                    value=  f"```ansi\n\u001b[0;34m"
                            f" {weatherdata['hightemp_f']}°F • {weatherdata['hightemp_c']}°C\n"
                            f" {weatherdata['lowtemp_f']}°F • {weatherdata['lowtemp_c']}°C```\n",
                    inline=True)
        
        #==== Next Row ====
        
        weatherembed.add_field(name=" Wind Speed 💨",
                                value=f"```ansi\n\u001b[0;36m {weatherdata['wind_mph']}mph\n {weatherdata['wind_kph']}kph\n {weatherdata['wind_dir']}```", inline=True)
     
        weatherembed.add_field(name="💧 Humidity 💧",
                                value=f"```ansi\n\u001b[0;34m {weatherdata['humidity']}%```", inline=True)

        weatherembed.add_field(name="🌞 Daylight 🌝",
                        value=f"```ansi\n\u001b[0;33m"
                              f"   Sunrise: {weatherdata['sunrise']}\n"
                              f"    Sunset: {weatherdata['sunset']}\n"
                              f"Day Length: {daylength}\n```")

        if weatherdata['daily_chance_of_rain']:
            weatherembed.add_field(name="Chance of Rain",
                value=f"```ansi\n\u001b[0;33m"
                      f" {weatherdata['daily_chance_of_rain']}%```")
        elif weatherdata['daily_chance_of_snow']:
            weatherembed.add_field(name="Chance of Snow",
                value=f"```ansi\n\u001b[0;33m"
                      f" {weatherdata['daily_chance_of_snow']}%```")
        else:
            pass

        #weatherembed.add_field(name="🌥 Cloud 🌥", 
        #                value=f"``` {weatherdata['cloud']}```", inline=True) #idk what they mean by cloud, it's fully cloudy out and it gives me 0
        #weatherembed.add_field(name = chr(173), value = chr(173), inline=True)
        #weatherembed.add_field(name = chr(173), value = chr(173), inline=False)
        #weatherembed.add_field(name="\u200B", value="\u200B")   

    except Exception as e:
        print("createweatherembed failed: ", e)

    return weatherembed

async def createweatherembedline(place):

    try:
        location = await bingGetLocationDataByQuery(place)
        coords = await bingParseCoords(location)
        nameoflocation = await bingParseNameOfLocation(location)
    except Exception as e:
        print("createweatherembed location search not work: ", e)
        return 1

    try: 
        weatherdata = await getWeatherapidotcomData(','.join(map(str, coords)))
        daylength = await sunDayLength(weatherdata['lat'],weatherdata['long'])
    except Exception as e:
        print("createweatherembed weatherdata lookup not working: ", e)
        return 2


    if weatherdata['is_day'] == 1:
        daytimehexcolor=0x0ba4ff
    else:
        daytimehexcolor=0x2d626b
    
    #fulllocation = (f"{weatherdata['Location']}, {weatherdata['region']},\n{weatherdata['country']}")

    
    emoji = await getWeatherEmoji(weatherdata)



    try: 
        weatherembed = discord.Embed(title=f"Weather in {nameoflocation}", 
                                     url="https://www.accuweather.com/en/us/national/weather-radar", 
                                     description=f"", 
                                     color=daytimehexcolor)
        #weatherembed.set_author(name=f"someone", 
        #                    url="", 
        #                    icon_url=f"https:{weatherdata['icon']}")
        #weatherembed.add_field(name=f"Weather in {nameoflocation}",
        #                        value=f"",inline=False)  


        #\u001b[{format};{color}m     https://gist.github.com/kkrypt0nn/a02506f3712ff2d1c8ca7c9e0aed7c06

        weatherembed.add_field(name="",
                                value=  f"```ansi\n"
                                        f""               f"             "  f"\u001b[0;0m"    f"{weatherdata['localtime']}"
                                        f"\n\u001b[1;34m" f"             "  f"\u001b[0;0m"    f"{weatherdata['textcondition']} {emoji}"
                                        f"\n\u001b[1;34m" f"    Current: "  f"\u001b[0;34m"   f"{weatherdata['temp_f']}°F • {weatherdata['temp_c']}°C"
                                        f"\n\u001b[0;34m" f" Feels Like: "  f"\u001b[0;33m"   f"{weatherdata['feelslike_f']}°F • {weatherdata['feelslike_c']}°C"
                                        f"\n\u001b[1;34m" f"     ⬆ High: "  f"\u001b[0;34m"   f"{weatherdata['hightemp_f']}°F • {weatherdata['hightemp_c']}°C"
                                        f"\n\u001b[1;34m" f"     ⬇  Low: "  f"\u001b[0;34m"   f"{weatherdata['lowtemp_f']}°F • {weatherdata['lowtemp_c']}°C"
                                        f"\n\u001b[1;36m" f" Wind Speed: "  f"\u001b[0;36m"   f"{weatherdata['wind_mph']}mph • {weatherdata['wind_kph']}kph {weatherdata['wind_dir']}"
                                        f"\n\u001b[1;36m" f"   Humidity: "  f"\u001b[0;36m"   f"{weatherdata['humidity']}%"
                                        f"\n\u001b[1;33m" f"    Sunrise: "  f"\u001b[0;33m"   f"{weatherdata['sunrise']}"
                                        f"\n\u001b[1;33m" f"     Sunset: "  f"\u001b[0;33m"   f"{weatherdata['sunset']}"
                                        f"\n\u001b[1;33m" f" Day Length: "  f"\u001b[0;33m"   f"{daylength}" 
                                        f"```"
                                , inline=False)
        #weatherembed.add_field(name="",
        #                        value=  "[Radar](https://www.accuweather.com/en/us/national/weather-radar)")

        #weatherembed.set_footer(icon_url= "",
        #                        text= "")
    except Exception as e:
        weatherembed = None
        print("createweatherembed failed: ", e)

    return weatherembed
