import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
import json

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

SONG_FILE = "song_data.json"

#read json data
def load_songs() -> dict:
    try:
        with open(SONG_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict):
        data = [data]
    return {s["spotify_id"]: s for s in data if "spotify_id" in s}

cached = load_songs()

# ADD SONGS HERE
results = sp.current_user_saved_tracks(limit=50,offset=len(cached))
spotify_liked_song_ids=[
    item['track']['id'] for item in results['items']
    if item.get('track') and item['track'].get('id')
]

missing_ids = [i for i in spotify_liked_song_ids if i not in cached]

# api request for missing songs
HEADERS = {"Accept": "application/json"}

def fetch_song(spotify_id: str):
    """Return cached entry for a song, or None if ReccoBeats doesn't have it."""
    track = requests.get(
        "https://api.reccobeats.com/v1/track",
        params={"ids": spotify_id},
        headers=HEADERS,
    )
    if track.status_code == 400: # missing song in reccobeats
        return None
    track.raise_for_status()
    content = track.json().get("content", [])
    if not content:
        return None

    features = requests.get(
        "https://api.reccobeats.com/v1/audio-features",
        params={"ids": content[0]["id"]},
        headers=HEADERS,
    )
    if features.status_code == 400:
        return None
    features.raise_for_status()
    content = features.json().get("content", [])
    if not content:
        return None

    return {
        "spotify_id": spotify_id,
        "valence": content[0]["valence"],
        "arousal": content[0]["energy"],
    }

if missing_ids:
    for spotify_id in missing_ids:
        song = fetch_song(spotify_id)
        if song is None:
            print(f"skipping {spotify_id}: not in ReccoBeats")
            song = {"spotify_id": spotify_id, "missing": True}
        cached[spotify_id] = song

    #write to json
    with open(SONG_FILE, "w", encoding="utf-8") as file:
        json.dump(list(cached.values()), file, indent=4)