
import discord
import random
from astral import LocationInfo
from astral.sun import sun
from datetime import datetime, timedelta
import urllib.parse
import TokensAndKeys
import requests



BingMapsKey = TokensAndKeys.bingmapsApiKey
weatherapidotcomkey = TokensAndKeys.WeatherApiDotComKey 
rightnow = datetime.now()
utctime = datetime.utcnow()

emojiDict={
    "Moon": "🌙",
    "Night":"🌃",
    "Mostly_Cloudy": "⛅️️",
    "Partly_Cloudy": "🌤️",
    "Cloudy": "☁️",
    "Overcast": "☁️",
    "Sunny": "🌞",
    "Rainbow": "🌈",
    "Snowflake": "❄️",
    "Snowing": "🌨",
    "Raining": "🌧",
    "raining2": "☔️",
    "snowlist": ["❄️", "☃️", "⛄️", "🌨"],
    "rainlist": ["🌧", "☔️", "💦", "💧"]
}

#=========

async def bingGetLocationDataByQuery(locationQuery):
    if type(locationQuery) == str:
        cool = locationQuery
    else:
        cool = ''.join(locationQuery)
    bingplace = requests.get(f"http://dev.virtualearth.net/REST/v1/Locations?query={cool}&key={BingMapsKey}")
    #print(f"http://dev.virtualearth.net/REST/v1/Locations?query={cool}&key={BingMapsKey}")
    bingjsondata = bingplace.json() if bingplace and bingplace.status_code == 200 else None
    return bingjsondata

async def bingGetLocationDataByCoords(lat,long):
    
    bingplace = requests.get(f"http://dev.virtualearth.net/REST/v1/Locations/{lat},{long}?&key={BingMapsKey}")
    bingjsondata = bingplace.json() if bingplace and bingplace.status_code == 200 else None
    print(f"http://dev.virtualearth.net/REST/v1/Locations/{lat},{long}?&key={BingMapsKey}")
    #http://dev.virtualearth.net/REST/v1/Locations/47.60322952,-122.33027649?&key=AuQX5ztwTTNpJ0flr2pxkaWz_EJSdujIZvz91VBHTw4oFo39aa6hXdyJinlUiw54
    return bingjsondata

async def bingGetNameOfLocation(bingdata):
    nameofplace = bingdata["resourceSets"][0]["resources"][0]["name"]
    return nameofplace

async def bingGetCoords(bingdata):
    coordlist = bingdata["resourceSets"][0]["resources"][0]["point"]["coordinates"]
    return coordlist

async def bingLocalTime(lat,long):
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

async def getTimeString(place):
    place2 = ''.join(place) #I have no idea why I wrote this here or like this, it seems redundant but it works so I'm not touching it
    
    if "shugan".lower() == place2.lower():
        place2 = "Belgium"
    if "floyd".lower() == place2.lower():
        place2 = "Melbourne Australia"
    if "moe".lower() == place2.lower():
        place2 = "Maryland"
    
    bingdata = bingGetLocationDataByQuery(place2)
    placename = bingGetNameOfLocation(bingdata)
    coordlist = bingGetCoords(bingdata)
    timethere, abbrev = bingLocalTime(*coordlist)
    string = f"Time in {placename}: **{timethere}** {abbrev}"
     
    return string

async def astralSunStuff(coords):

    #astral gives you some sun stats with datetime values
    #I reput them in as formatted times that make peoples eyes heal
    locato = LocationInfo('name','region','US/Central', coords[0], coords[1])
    rawSunInfo = sun(locato.observer, date=datetime(rightnow.year, rightnow.month, rightnow.day))#print("sunlist: ", rawSunInfo) #{'dawn': datetime.datetime(2024, 2, 5, 14, 57, 53, 300320, tzinfo=datetime.timezone.utc)}
    sunInfo = {key: value.strftime('%#I:%M%p') for key, value in rawSunInfo.items()}

    #get day length and put it in the suninfo dict
    sunApiPlace = requests.get(f"https://api.sunrise-sunset.org/json?lat={coords[0]}&lng={coords[1]}&date=today")
    sunjson = sunApiPlace.json() if sunApiPlace and sunApiPlace.status_code == 200 else None
    daylengthraw = sunjson["results"]['day_length'] # 09:51:59 h m s
    parse = datetime.strptime(daylengthraw, "%H:%M:%S")
    daylength = parse.strftime("%#Hh %Mm")
    sunInfo["daylength"] = daylength
    #f'Dawn:    {sunInfo["dawn"]}\n'
    #f'Sunrise: {sunInfo["sunrise"]}\n'
    #f'Noon:    {sunInfo["noon"]}\n'  
    #f'Sunset:  {sunInfo["sunset"]}\n'
    #f'Dusk:    {sunInfo["dusk"]}\n'
    return sunInfo



########################
#   new weather stuff  #
########################

async def getWeatherapidotcomData(query): #city name, Latitude/Longitude (decimal degree), US Zipcode, UK Postcode, Canada Postalcode, IP address, 
    response = requests.get(f"http://api.weatherapi.com/v1/forecast.json?key={weatherapidotcomkey}&q={query}&days=2&aqi=no&alerts=no")
    weatherjson = response.json() if response and response.status_code == 200 else None

    weatherDict = {}
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

    return weatherDict

async def sunDayLength(lat, long):

    sunApiPlace = requests.get(f"https://api.sunrise-sunset.org/json?lat={lat}&lng={long}&date=today")
    sunjson = sunApiPlace.json() if sunApiPlace and sunApiPlace.status_code == 200 else None
    daylengthraw = sunjson["results"]['day_length'] # 09:51:59 h m s
    parse = datetime.strptime(daylengthraw, "%H:%M:%S")
    daylength = parse.strftime("%#Hh %Mm")
    return daylength

async def getWeatherMsg(place):
    #bingdata = bingGetLocationData(place)
    #nameofplace = bingGetNameOfLocation(bingdata)
    
    try:
        weatherdata = getWeatherapidotcomData(place)
        #currentlocationtime = bingLocalTime(bingdata)     
    except Exception as e:
        print("something didnt return prob: ", e)
        return #"something fuck up lol"

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

async def createweatherembed(place):

    weatherdata = await getWeatherapidotcomData(place)
    daylength = await sunDayLength(weatherdata['lat'],weatherdata['long'])

    if weatherdata['is_day'] == 1:
        daytimehexcolor=0x0ba4ff
    else:
        daytimehexcolor=0x2d626b
    
    fulllocation = (f"{weatherdata['Location']}, {weatherdata['region']},\n{weatherdata['country']}")
    

    
    if weatherdata['textcondition'] == emojiDict:
        emoji = emojiDict[weatherdata['textcondition']]
    elif weatherdata['is_day'] == 1:
        emoji = emojiDict['Sunny']
    else:
        emoji = emojiDict['Moon']



    try: 
        weatherembed = discord.Embed(title=f"Weather in\n{fulllocation}", 
                                     url="", 
                                     description=f"**{emoji} {weatherdata['textcondition']} {emoji}**", 
                                     color=daytimehexcolor)
        #weatherembed.set_author(name=f"someone", 
        #                    url="", 
        #                    icon_url=f"https:{weatherdata['icon']}")

        weatherembed.add_field(name="Current Temperature",
                                value=f"``` {weatherdata['temp_f']}°F   {weatherdata['temp_c']}°C```", inline=False)        

        weatherembed.add_field(name="Feels Like",
                                value=f"``` {weatherdata['feelslike_f']}°F   {weatherdata['feelslike_c']}°C```", inline=False)
        
        weatherembed.add_field(name="⬆ High • Low ⬇",
                        value=f"``` {weatherdata['hightemp_f']}°F   {weatherdata['lowtemp_f']}°F\n"
                              f" {weatherdata['hightemp_c']}°C   {weatherdata['lowtemp_c']}°C```\n",
                        inline=False)

        #weatherembed.add_field(name="\u200B", value="\u200B")
        

        weatherembed.add_field(name="💨 Wind Speed  •  Wind Direction 💨",
                                value=f"``` {weatherdata['wind_mph']}mph   {weatherdata['wind_kph']}kph   {weatherdata['wind_dir']}```", inline=False)
        
        weatherembed.add_field(name="",
                                value=f"```   ```", inline=False)
        

        weatherembed.add_field(name="",
                        value=f"Sunrise: {weatherdata['sunrise']}\n"
                                f"Sunset:  {weatherdata['sunset']}\n"
                                f"Day Length: {daylength}\n"
                            )
        #weatherembed.add_field(name="\u200B", value="\u200B", inline=False)
#

        

    except Exception as e:
        print("createweatherembed failed: ", e)
    return weatherembed


