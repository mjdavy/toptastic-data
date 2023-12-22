
import json
import logging
from googleapiclient.discovery import build
import os
import sqlite3

from my_app.toptastic_api import get_db_connection

# Get your YouTube Data API key from an environment variable
api_key = os.getenv('YOUTUBE_DATA_API_KEY')

# Build the service
youtube = build('youtube', 'v3', developerKey=api_key)

def get_youtube_video_id(query):
    logging.info(f'Getting video id for {query} from YouTube.')
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