import time
import requests
import json
import webbrowser
from urllib.parse import urlencode
import base64
import socket
from datetime import datetime, timedelta
import os
from sys import exit
import keyboard
from dotenv import load_dotenv
from lyrics import lyricsFetcher


load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

REDIRECT_URI = "http://localhost:3000/callback"

AUTHORIZE = "https://accounts.spotify.com/authorize"
TOKEN = "https://accounts.spotify.com/api/token"
PLAYLISTS = "https://api.spotify.com/v1/me/playlists"
DEVICES = "https://api.spotify.com/v1/me/player/devices"
PLAY = "https://api.spotify.com/v1/me/player/play"
PAUSE = "https://api.spotify.com/v1/me/player/pause"
NEXT = "https://api.spotify.com/v1/me/player/next"
PREVIOUS = "https://api.spotify.com/v1/me/player/previous"
PLAYER = "https://api.spotify.com/v1/me/player"
TRACKS = "https://api.spotify.com/v1/playlists/{{PlaylistId}}/tracks"
CURRENTLYPLAYING = "https://api.spotify.com/v1/me/player/currently-playing"
SHUFFLE = "https://api.spotify.com/v1/me/player/shuffle"

NEXT_SONG_KEY = 'n'
PREVIOUS_SONG_KEY = 'p'
TOGGLEPLAYBACK_KEY = 'space'
EXIT_KEY = 'q'


def clearScreen():
    os.system("cls" if os.name == "nt" else "clear")

def extractCode(s):
    start = s.find("code=")
    if start > 0 and len(s) > start + len("code="):
        start = start + len("code=")
        end = s.rfind("'")
        if end < start:
            end = len(s)
        return s[start:end]
    return ""

def listenUrl():
    soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        soc.bind(("", 3000))
    except socket.error as message:
        print("Socket failed")
        exit(1)

    soc.listen(9)
    conn, address = soc.accept()
    message = conn.recv(4096)
    #soc.shutdown(socket.SHUT_RDWR)
    soc.close()
    return extractCode(str(message.split()[1]))

class song:
    def __init__(self, name, artists):
        self.name = name
        self.artists = artists
        self.lyrics = ""

class session:
    def __init__(self):
        self.exitFlag = False
        self.auth_code = ""
        self.access_token = ""
        self.refresh_token = ""
        self.expires_at = 3600
        self.current_song = None
        self.lyrics = None
        self.lyrFetcher = lyricsFetcher()


    def login(self):
        scope = "user-read-private user-read-email user-modify-playback-state user-read-playback-position user-library-read streaming user-read-playback-state user-read-recently-played playlist-read-private"
        #scope = "user-read-private user-read-email"

        auth_headers = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'redirect_uri': REDIRECT_URI,
            'scope': scope,
            'show_dialog': 'True'
        }

        url = AUTHORIZE + "?" + urlencode(auth_headers)
        webbrowser.open(url)
        self.auth_code = listenUrl()
        return self.auth_code != ""

    def fetchAccessToken(self):
        if (self.auth_code == ""): return

        encoded_credentials = base64.b64encode(CLIENT_ID.encode() + b':' + CLIENT_SECRET.encode()).decode("utf-8")

        data = {
            "grant_type": "authorization_code",
            "code": self.auth_code,
            "redirect_uri": REDIRECT_URI
        }

        headers = {
            "Authorization": "Basic " + encoded_credentials,
            "Content-Type": "application/x-www-form-urlencoded"
        }

        res = requests.post(TOKEN, data=data, headers=headers)
        token_info = res.json()

        self.access_token = token_info["access_token"]
        self.refresh_token = token_info["refresh_token"]
        self.expires_at = datetime.now().timestamp() + token_info["expires_in"]



    def callback(code):
        pass


# Refresh access token if datetime.now().timestamp() > self.expires_at
    def refresh(self):
        if (self.refresh_token == ""):
            self.login()
            return

        if self.tokenExpired():
            print("Refreshing token")
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': CLIENT_ID
            }
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}

            res = requests.post(TOKEN, data=data, headers=headers)
            if res.status_code == 200:
                token_info = res.json()
                self.access_token = token_info["access_token"]
                self.expires_at = datetime.now().timestamp() + token_info["expires_in"]
            else: print(f"Refreshing access_token failed, status: {res.status_code}")

    def tokenExpired(self):
        return datetime.now().timestamp() > self.expires_at

    def getReq(self, url):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        return requests.get(url, headers=headers)

    def postReq(self, url):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        return requests.post(url, headers=headers)

    def getCurrentSong(self):
        res = self.getReq(CURRENTLYPLAYING)
        if res.status_code == 204: return # Empty res, no song playing
        curSong = res.json()
        #print(curSong)
        if res.status_code == 200 and curSong["item"] and curSong["is_playing"]:
            songName = curSong["item"]["name"]
            artists = [artist["name"] for artist in curSong["item"]["artists"]]
            if (self.current_song is None or self.current_song.name != songName):

                clearScreen()
                self.current_song = song(songName, artists)
                print("Getting lyrics...")
                self.searchLyrics(songName, artists)
                return True

        elif res.status_code > 200:
            print(f"Status: {curSong['error']['status']}, Message: {curSong['error']['message']}")
        return False

    def searchLyrics(self, songName, artists):
        #self.lyrics = None
        if self.current_song is not None:
            self.lyrics = self.lyrFetcher.getLyrics(songName, artists)


# Only works on spotify premium user
    def nextSong(self, event):
        res = self.postReq(NEXT)

    def previousSong(self, event):
        res = self.postReq(PREVIOUS)

    def togglePlayback(self, event):
        res = self.getReq(PLAYER)
        if res.status_code == 200 and res.json()["is_playing"]:
            res = self.postReq(PAUSE)
        else:
            res = self.postReq(PLAY)


    def exitSession(self, event):
        clearScreen()
        print("Exiting program..\n")
        self.exitFlag = True


    def printLyrics(self):
        clearScreen()
        print(f"Currently playing: {self.current_song.name}")
        print(f"Artists: {self.current_song.artists}")
        print()

        if self.lyrics:
            for line in self.lyrics:
                if line.startswith("[") and line.endswith("]"):
                    print()
                print(line)
        else:
            print("No lyrics found..")

        #keyboard.send("ctrl+home")
        #print("", flush=True)
            


    def run(self):
        while(True):
            self.refresh()

            keyboard.on_release_key(NEXT_SONG_KEY, self.nextSong, True)
            keyboard.on_release_key(PREVIOUS_SONG_KEY, self.previousSong, True)
            keyboard.on_release_key(TOGGLEPLAYBACK_KEY, self.togglePlayback, True)
            keyboard.on_release_key(EXIT_KEY, self.exitSession, True)
            
            if self.exitFlag:
                exit(0)

            songChanged = self.getCurrentSong()
            if songChanged:
                self.printLyrics()
            time.sleep(2)

    def startSession(self):
        if CLIENT_ID and CLIENT_SECRET:
            loggedIn = self.login()
            self.fetchAccessToken()
        else:
            print("Set environment variables: CLIENT_ID | CLIENT_SECRET")

        if self.access_token == "": 
            print("Authentication failed!")
            exit(1)
        clearScreen()
        print("Session started successfully!")
        self.run()

def main():
    ses = session()
    ses.startSession()

if __name__ == "__main__":
    main()

