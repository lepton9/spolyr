import json
import os
from dotenv import load_dotenv
import requests
import base64
from bs4 import BeautifulSoup

load_dotenv()

REDIRECT_URI = "http://localhost:3000"
API_URL = "http://api.genius.com"
AUTHENTICATION_URL = "https://api.genius.com/oauth/authorize"
AUTH_URL = "https://api.genius.com/oauth/token"
SONGS_URL = "https://api.genius.com/songs"
GENIUS_URL = "http://genius.com"

CLIENT_ID = os.getenv("GENIUS_CLIENT_ID")
CLIENT_SECRET = os.getenv("GENIUS_CLIENT_SECRET")
CLIENT_TOKEN = os.getenv("GENIUS_TOKEN") # Also valid as the access_token


class lyricsFetcher:
    def __init__(self):
        self.song_id = ""
        self.song_path = ""
        self.song_name = ""
        self.artists = []
        self.getAccessToken()

    def getAccessToken(self):
        if not CLIENT_ID or not CLIENT_SECRET:
            print("Set environment variables: CLIENT_ID | CLIENT_SECRET")
            return

        encoded_credentials = base64.b64encode(CLIENT_ID.encode() + b':' + CLIENT_SECRET.encode()).decode("utf-8")

        headers = {
            "Authorization": f"Basic " + encoded_credentials,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        data = {
            "grant_type": "client_credentials",
        }

        res = requests.post(AUTH_URL, data=data, headers=headers)
        json = res.json()
        self.access_token = json["access_token"]

    def searchSong(self, songName, artists):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        search_url = API_URL + f"/search?q={songName}"
        artist = artists[0]
        res = requests.get(search_url, headers=headers)
        json = res.json()
        song_info = None

        for hit in json["response"]["hits"]:
            if hit["result"]["primary_artist"]["name"] == artist:
                song_info = hit
                break
        if song_info:
            self.song_id = song_info["result"]["id"]
            self.song_path = song_info["result"]["path"]
            self.song_name = songName
            self.artists = artists
            return True

        return False

    def getLyrics(self, songName, artists):
        if not self.access_token:
            print("No access token for Genius API")
            return None
        found = self.searchSong(songName, artists)
        if found:
            page_url = GENIUS_URL + self.song_path
            page = requests.get(page_url)
            html = BeautifulSoup(page.text, "html.parser")
            lyrics = html.find("div", attrs = {"id":"lyrics-root"})
            #lyrics = html.find("div", attrs = {'data-lyrics-container': True})
            if lyrics:
                lyricsText = lyrics.get_text(separator = "\n", strip=True).split("\n")
                #lyricsText = lyricsText[next((i+1 for i,s in enumerate(lyricsText) if f"{self.song_name} Lyrics" in s), 0):-3]
                lyricsText = lyricsText[next((i+1 for i,s in enumerate(lyricsText) if f" Lyrics" in s), 0):-3]
                return lyricsText
        return None


"""
if __name__ == "__main__":
    lf = lyricsFetcher()
    lyrics = lf.getLyrics("SongName", ["Artists"])
    print(lyrics)
"""
    

