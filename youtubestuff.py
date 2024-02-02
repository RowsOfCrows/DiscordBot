#import xmltodict
import TokensAndKeys
#from googleapiclient.discovery import build

channelid="UCJMn0gckjHPGYtdoHozOW9A"
#service = build('youtube', 'v3',developerKey=TokensAndKeys.YoutubeApiKey)

riotyoutubeID = "UC2t5bjwHdUX4vM2g8TRDq5g"
youtuberss = "https://www.youtube.com/feeds/videos.xml?channel_id="
riotytrss = f"{youtuberss}{riotyoutubeID}"

import urllib.request
import re

def yt_search(cool):
    search_keyword = '+'.join(cool)
    print(search_keyword)
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search_keyword)
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())

    heck = ("https://www.youtube.com/watch?v=" + video_ids[0]+"\n")
    return heck

def lastchanneluploads():
    pass



def rsstest():
    for item, valu in d["entries"][0].items():
        print(item, valu)
    #cool = (ps['entries'][0]["summary"])
    #cool = re.sub("<.*?>", "", cool)
    #print(cool)
    pass

def xml2dstuff(): #need local xml, heck ur life
    my_ordered_dict=xmltodict.parse(ps)
    print("Ordered Dictionary is:")
    print(my_ordered_dict)
    pass

def embedredditrss():
    pass



#request = service.Channels.(
#
#
#)
#
#response = request.execute()