
import json
import logging
import googleapiclient.discovery
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import sqlite3

from my_app.toptastic_api import get_db_connection

class QuotaExceededError(Exception):
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("youtube.log", mode="w"),
        logging.StreamHandler()
    ]
)

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logging.getLogger('googleapiclient.http').setLevel(logging.ERROR)

# Read the API keys from the file
api_keys_file = os.path.expanduser('~/OneDrive/secrets/toptastic/youtube_api_keys.txt')
try:
    with open(api_keys_file) as f:
        api_keys = f.read().splitlines()
except Exception as e:
    logging.error(f'Error reading api keys: {e}')
    exit(1)


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

def get_authenticated_service():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_console()
    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

# Function to get the YouTube Data API service with the current API key
def get_youtube_service():
    api_key = api_keys[current_key_index]
    youtube_service = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
    return youtube_service

def create_playlist(youtube, title, description):
    playlists_insert_response = youtube.playlists().insert(
        part="snippet,status",
        body=dict(
            snippet=dict(
                title=title,
                description=description
            ),
            status=dict(
                privacyStatus="private"
            )
        )
    ).execute()

    return playlists_insert_response["id"]

def add_video_to_playlist(youtube, playlist_id, video_id):
    youtube.playlistItems().insert(
        part="snippet",
        body=dict(
            snippet=dict(
                playlistId=playlist_id,
                resourceId=dict(
                    kind="youtube#video",
                    videoId=video_id
                )
            )
        )
    ).execute()

# Initialize the index of the current API key
current_key_index = 0

def get_youtube_video_id(query):
    global current_key_index  # Add this line
    try:
        logging.info(f'Getting video id for {query} from YouTube.')
        youtube = get_youtube_service() 
        request = youtube.search().list(
            q=query,
            part='id',
            maxResults=1,
            type='video'
        )
        response = request.execute()

        items = response.get('items', [])
        if items:
            return items[0]['id']['videoId']
        
    except googleapiclient.errors.HttpError as e:
        if e.resp.status == 403 :
        # Quota exceeded error, switch to the next API key
            current_key_index += 1
            if current_key_index >= len(api_keys):
                # All quotas are used up, stop the program
                logging.info("All API keys have exceeded their quotas.")
                raise QuotaExceededError("All API keys have exceeded their quotas.")
            else:
                # Retry with the next API key
                logging.info(f"Quota exceeded for API key {api_keys[current_key_index - 1]}. Switching to API key {api_keys[current_key_index]}.")
                youtube = get_youtube_service()
        else:
            # Other HTTP error, handle it as desired
            logging.error(f"HTTP error occurred: {e}")

    return None

# Update video IDs for songs that don't have them
def update_video_ids():
    conn = get_db_connection()
    songs = conn.execute('SELECT * FROM songs WHERE video_id IS NULL OR video_id = ""').fetchall()

    logging.info(f'Updating video IDs for {len(songs)} songs.')

    update_count = 0
    for row in songs:
        song = dict(row)
        try: 
            video_id = get_youtube_video_id(f"{song['song_name']} {song['artist']}")
            if video_id:
                conn.execute('UPDATE songs SET video_id = ? WHERE id = ?', (video_id, song['id']))
                conn.commit()  # commit after each update
                song['video_id'] = video_id
                update_count += 1
        except QuotaExceededError:
            break
        except Exception as e:
            logging.error(f'Error updating video ID for song {song["song_name"]} by {song["artist"]}: {e}')
            
    logging.info(f'{update_count} Video IDs updated successfully.')
    remaining = conn.execute('SELECT count(*) FROM songs WHERE video_id IS NULL OR video_id = ""').fetchone()[0]
    logging.info(f'{remaining} videos remaining.')
    conn.close()

update_video_ids()