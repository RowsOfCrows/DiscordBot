import os

if not os.path.exists("LocalData"):
    os.makedirs("LocalData")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOTDATA_DIR   = os.path.normpath(os.path.join(BASE_DIR, '..', 'BotData'))
LOCALDATA_DIR = os.path.normpath(os.path.join(BASE_DIR, '..', 'LocalData'))