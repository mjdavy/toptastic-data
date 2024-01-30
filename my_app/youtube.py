
import json
import logging
from pathlib import Path
import pickle
#from flask import Request
import googleapiclient.discovery
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import sqlite3
from google.auth.transport.requests import Request
from pytube import YouTube


from my_app.toptastic_api import get_db_connection

class QuotaExceededError(Exception):
    pass

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logging.getLogger('googleapiclient.http').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

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
CLIENT_SECRETS_FILE = os.path.join(os.path.dirname(api_keys_file), "client_secret.json")

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

def get_authenticated_service():
    creds = None
    # The file .token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    token_path = Path.home() / ".token.pickle"
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=creds)

# Function to get the YouTube Data API service with the current API key
def get_youtube_service():
    api_key = api_keys[current_key_index]
    youtube_service = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
    return youtube_service

def create_playlist(youtube, title, description):
    try:
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
    except googleapiclient.errors.HttpError as e:
        if e.resp.status == 403 :
            raise QuotaExceededError("Youtube API quota exeeded. Try again tomorrow.")
        
    logger.info(playlists_insert_response)

    return playlists_insert_response["id"]

def add_video_to_playlist(youtube, playlist_id, video_id):
    logger.info(f"Adding video with id: {video_id} to playist with id: {playlist_id}")
    response = youtube.playlistItems().insert(
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
    logger.info(response)

# Initialize the index of the current API key
current_key_index = 0

def get_youtube_video_id(query):
    global current_key_index  # Add this line
    try:
        logger.info(f'Getting video id for {query} from YouTube.')
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
            logger.error(f"HTTP error occurred: {e}")

    return None

# Update video IDs for songs that don't have them
def update_video_ids():
    conn = get_db_connection()
    songs = conn.execute('SELECT * FROM songs WHERE video_id IS NULL').fetchall()

    logger.info(f'Updating video IDs for {len(songs)} songs.')

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
            else :
                logger.info(f'No video ID found for song {song["song_name"]} by {song["artist"]}.')
                conn.execute('UPDATE songs SET video_id = ? WHERE id = ?', ('', song['id'])) # Set video ID to empty string

        except QuotaExceededError:
            break
        except Exception as e:
            logging.error(f'Error updating video ID for song {song["song_name"]} by {song["artist"]}: {e}')
            
    logger.info(f'{update_count} Video IDs updated successfully.')
    remaining = conn.execute('SELECT count(*) FROM songs WHERE video_id IS NULL').fetchone()[0]
    logger.info(f'{remaining} videos remaining.')
    conn.close()

def download_video(video_id, folder, filename):
    
    youtube = YouTube(f'https://www.youtube.com/watch?v={video_id}')

    # Get stream
    video = youtube.streams.get_highest_resolution()
    
    full_path = os.path.join(folder, filename)
    if os.path.exists(full_path):
        raise FileExistsError()
    else:
        logger.info(f'Downloading video to {full_path}.')
        out_video_filepath = video.download(output_path=folder, filename=filename)
        logger.info(f'Video downloaded to {out_video_filepath}.')
    