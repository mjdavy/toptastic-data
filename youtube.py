
import json
import logging
import googleapiclient.discovery
import os
import sqlite3

from my_app.toptastic_api import get_db_connection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("youtube.log", mode="w"),
        logging.StreamHandler()
    ]
)

# Read the API keys from the file
api_keys_file = os.path.expanduser('~/secrets/youtube_api_keys.txt')
try:
    with open(api_keys_file) as f:
        api_keys = f.read().splitlines()
except Exception as e:
    logging.error(f'Error reading secrets file: {e}')
    exit(1)

# Initialize the index of the current API key
current_key_index = 0

# Function to get the YouTube Data API service with the current API key
def get_youtube_service():
    api_key = api_keys[current_key_index]
    youtube_service = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
    return youtube_service


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
                exit(1)
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

    for row in songs:
        song = dict(row)
        try: 
            video_id = get_youtube_video_id(f"{song['song_name']} {song['artist']}")
            if video_id:
                conn.execute('UPDATE songs SET video_id = ? WHERE id = ?', (video_id, song['id']))
                song['video_id'] = video_id
        except Exception as e:
            logging.error(f'Error updating video ID for song {song["song_name"]} by {song["artist"]}: {e}')
            
    conn.commit()
    conn.close()

    logging.info('Video IDs updated successfully.')

update_video_ids()