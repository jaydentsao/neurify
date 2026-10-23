import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests

scope = "user-modify-playback-state,user-library-read,playlist-read-private"

#spotipy api
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope=scope,
        client_id="6eb11310ae9c4a57b1a23a650d330c0f",
        client_secret="73c0a915a8d643a2937bcf3ec2fd3198",
        redirect_uri="http://127.0.0.1:5000/callback"
    )
)
results = sp.current_user_saved_tracks()
spotify_liked_song_ids=[
    item['track']['id'] for item in results['items']
    if item.get('track') and item['track'].get('id')
]

#apicall to get song from reccobeats
request=requests.get(
    "https://api.reccobeats.com/v1/track",
    params={"ids": ",".join(spotify_liked_song_ids)},
    headers={"Accept": "application/json"},
)

request.raise_for_status()

recco_ids = [i["id"] for i in request.json()["content"]]

features = requests.get(
    "https://api.reccobeats.com/v1/audio-features",
    params={"ids": ",".join(recco_ids)},
    headers={"Accept": "application/json"},
)
features.raise_for_status()

SONG_DATABASE=[]

#creating database

for i in features.json()["content"]:
    SONG_DATABASE.append({
        "spotify_id":i["href"].rstrip("/").split("/")[-1].split("?")[0],
        "valence":i["valence"],
        "arousal":i["energy"]
    })

def get_nearest_song(valence: float, arousal: float)->dict:
    return min(
        SONG_DATABASE,
        #lambda uses euclidean distance
        key=lambda s: (s["valence"] - valence) ** 2 + (s["arousal"] - arousal) ** 2,
    )

def play_nearest_song(valence: float, arousal:float):
    song=get_nearest_song(valence,arousal)
    spotify_id=song["spotify_id"]
    sp.add_to_queue(uri="spotify:track:"+spotify_id)

play_nearest_song(-0.2571,0.5820)