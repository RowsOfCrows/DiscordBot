
import discord
import random
from astral import LocationInfo
from astral.sun import sun
import datetime
import urllib.parse
import requests

BingMapsKey="AoNl4tonPaHE_hQnTli8b9DmX41_gPDOKThNhhibNw6HkMUYXhsMl0KC_q9v63dV"
rightnow = datetime.datetime.now()
utctime = datetime.datetime.utcnow()

def bingLocation(locationQuery, weatherResources=False, timezoneResources=False, realplace=False):
    if type(locationQuery) == str:
        cool = locationQuery
    else:
        cool = ' '.join(locationQuery)
    bingplace = requests.get(f"http://dev.virtualearth.net/REST/v1/Locations?query={cool}&key={BingMapsKey}")
    #print(f"http://dev.virtualearth.net/REST/v1/Locations?query={locationQuery}&key={BingMapsKey}")
    bingjson = bingplace.json() if bingplace and bingplace.status_code == 200 else None
    coordlist = bingjson["resourceSets"][0]["resources"][0]["point"]["coordinates"]
    actualplace = bingjson["resourceSets"][0]["resources"][0]["name"]
    if realplace:
        return actualplace
    if weatherResources:
        return weatherList(coordlist, actualplace)
    #if timezoneResources:
    #    #return bingtimezone(coordlist)
    #    pass
    coordDict ={"lat": coordlist[0], "long": coordlist[1]}
    return coordDict



def bingTimeZone(placefornow, placecurrenttime=False):
    coord = bingLocation(placefornow)
    timezoneurl = requests.get(f"https://dev.virtualearth.net/REST/v1/TimeZone/{coord['lat']},{coord['long']}?&key={BingMapsKey}") #?datetime={datetime_utc}
    timezonejson = timezoneurl.json() if timezoneurl and timezoneurl.status_code == 200 else None
    timezoneName = timezonejson["resourceSets"][0]["resources"][0]["timeZone"]["genericName"]
    timezoneAbbrev = timezonejson["resourceSets"][0]["resources"][0]["timeZone"]["genericName"]
    offsetnumber = timezonejson["resourceSets"][0]["resources"][0]["timeZone"]["utcOffset"]
    if placecurrenttime:
        localtimecool = timezonejson["resourceSets"][0]["resources"][0]["timeZone"]["convertedTime"]["localTime"]
        #dt_string = "2020-12-18 3:11:09"
        dt_object = datetime.datetime.strptime(localtimecool, "%Y-%m-%dT%H:%M:%S")
        #dt = dt.replace(tzinfo=timezone.utc)
        formattedtime = dt_object.strftime(f"%I:%M %p").lstrip("0")#- {timezoneAbbrev}
        return formattedtime
    return timezoneName

def convertTime(datetime_utc, timezoneid):
    url = requests.get(f"https://dev.virtualearth.net/REST/v1/TimeZone/Convert/?datetime={datetime_utc}&desttz={timezoneid}&key={BingMapsKey}")
    jayson =  url.json() if url and url.status_code == 200 else None
    timezonenamecool = jayson["resourceSets"][0]["resources"][0]["timeZone"]["convertedTime"]["localTime"]
    return timezonenamecool

def stringtime(place):
    place2 = ' '.join(place)

    if "shugan".lower() == place2.lower():
        place2 = "Belgium"
    if "floyd".lower() == place2.lower():
        place2 = "Melbourne Australia"
    print(place2)
    actualplace = bingLocation(place2,realplace=True)
    timethere = bingTimeZone(place2, True)
    #if "taiwan" in place:
    #    actualplace = "Taiwan"
    string = f"Time in {actualplace}: **{timethere}**"

    return string

def astralSunStuff(place):
    coords = bingLocation(place, timezoneResources=True)
    locato = LocationInfo('name','region','US/Central', coords["lat"], coords["long"])
    sunList = sun(locato.observer, date=datetime.date(rightnow.year, rightnow.month, rightnow.day))
    #print(sunList["sunrise"])  #utc
    timezonename = bingTimeZone(place) #get timezone
    timezonename = urllib.parse.quote(timezonename)
    #import re
    #timezonename = re.sub("\s","_",timezonename)
    for keys, values in sunList.items():
        string = str(sunList[keys])
        aroo = string[:10]+"T"+string[11:19]+"Z"
        gosh = convertTime(aroo, timezonename)
        gosh = gosh[11:-3]
        dt_object = datetime.datetime.strptime(gosh,"%H:%M")
        fuck = dt_object.strftime("%I:%M %p").lstrip("0")
        sunList.update({keys:fuck})
    sunApiPlace = requests.get(f"https://api.sunrise-sunset.org/json?lat={coords['lat']}&lng={coords['long']}&date=today")
    sunjson = sunApiPlace.json() if sunApiPlace and sunApiPlace.status_code == 200 else None
    daylength = sunjson["results"]['day_length']
    sunList["daylength"] = daylength[:-3].lstrip("0")
    #f'Dawn:    {s["dawn"]}\n'
    #f'Sunrise: {s["sunrise"]}\n'       #convert time- get time, compare, put it back in
    #f'Noon:    {s["noon"]}\n'          #insert time
    #f'Sunset:  {s["sunset"]}\n'        #convert sunlist times to timezone times
    #f'Dusk:    {s["dusk"]}\n'
    return sunList


def getweatherembed(place):
    weatherstuff = bingLocation(place, weatherResources=True)   #get location and weather dict
    sunstuff = astralSunStuff(place)                            #get sun dict
    currenttime = bingTimeZone(place, True)
    bloop = embededweather(weatherstuff, sunstuff, currenttime)  #pass dicts to embded
    return bloop

def weatherList(coordz, *Realplace):
    points = ','.join(str(e) for e in coordz)
    weatherpoints = requests.get(f'https://api.weather.gov/points/{points}')
    weatherjson = weatherpoints.json() if weatherpoints and weatherpoints.status_code == 200 else None
    placeurl = weatherjson["properties"]["forecast"]
    forecasturl = requests.get(placeurl)
    forecastjson = forecasturl.json() if forecasturl and forecasturl.status_code == 200 else None
    weatherNow = forecastjson["properties"]["periods"][0]
    weatherDict = {}
    if Realplace:
        weatherDict['place'] = Realplace[0]
    weatherDict['cTemp'] = int((int(weatherNow["temperature"]) - 32) * 5/9)
    weatherDict['fTemp'] = weatherNow["temperature"]
    weatherDict['windSpeed'] = weatherNow["windSpeed"]
    weatherDict['windDirection'] = weatherNow["windDirection"]
    weatherDict['shortForecast'] = weatherNow["shortForecast"]
    weatherDict['isDaytime'] = weatherNow["isDaytime"]
    weatherDict['detailedForecast'] = weatherNow['detailedForecast']
    return weatherDict
    #   weatherNow includes:
    #       "number": 1,
    #       "name": "Tonight",
    #       "startTime": "2021-11-04T22:00:00-04:00",
    #       "endTime": "2021-11-05T06:00:00-04:00",
    #       "isDaytime": false,
    #       "temperature": 31,
    #       "temperatureUnit": "F",
    #       "temperatureTrend": null,
    #       "windSpeed": "5 mph",
    #       "windDirection": "N",
    #       "icon": "https://api.weather.gov/icons/land/night/skc?size=medium",
    #       "shortForecast": "Clear",
    #       "detailedForecast": "Clear, with a low around 31. North wind around 5 mph."

def embededweather(weatherlist, sunstuff, currentlocaltime):

    if weatherlist['isDaytime']:
        colorbe =0x00d5ff
        daytimeEmoji = "🌞"
    else:
        colorbe = 0x0057a0
        daytimeEmoji = "🌝"


    if [x for x in list(weatherlist.values()) if 'Rain' in str(x)]:
        rainlist = ["🌧", "☔️", "💦", "💧"]
        rainlistresult = random.randint(0,(len(rainlist)-1))
        emoji = rainlist[rainlistresult]
    elif [x for x in list(weatherlist.values()) if 'Snow' in str(x)]:
        snowlist = ["❄️", "☃️", "⛄️", "🌨"]
        snowlistresult = random.randint(0,(len(snowlist)-1))
        emoji = snowlist[snowlistresult]
    elif [x for x in list(weatherlist.values()) if 'Cloudy' in str(x)]:
        if 'Mostly' in list(weatherlist.values()):
            emoji = "⛅️️"
        elif 'Partly' in list(weatherlist.values()):
            emoji = "🌤️"
        else:
            emoji = "☁️"
    elif [x for x in list(weatherlist.values()) if 'Clear' in str(x)]:
        emoji = "🌈"
    else:
        emoji = "🌞"
    embededcool=discord.Embed(title=f"{daytimeEmoji} Weather in {weatherlist['place']} {daytimeEmoji}",
    description=f"{emoji}   {weatherlist['shortForecast']} - {currentlocaltime}",
    color=colorbe,
    )
    embededcool.add_field(name=f"{weatherlist['fTemp']}°F",#👉💨🌄⭐👀
                          value=f"Wind:\n"
                                f"Sunrise:\n"
                                f"Sunset:\n"
                                f"Day length:", inline=True)
    embededcool.add_field(name=f"{weatherlist['cTemp']}°C",
                          value=f"{weatherlist['windSpeed']}, {weatherlist['windDirection']}\n"
                                f"{sunstuff['sunrise']}\n"
                                f"{sunstuff['sunset']}\n️"
                                f"{sunstuff['daylength']} hrs", inline=True)
    #embededcool.set_footer(text=f"👀👀👀👀👀")#{weatherlist['detailedForecast']}
    return embededcool