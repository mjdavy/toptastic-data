from concurrent.futures import ThreadPoolExecutor
import logging
from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import sqlite3
import sys
import json
from flask_executor import Executor
logger = logging.getLogger(__name__)

app = Flask(__name__)
executor = Executor(app)

def get_db_connection():
    conn = sqlite3.connect('songs.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables_if_needed():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create new tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY,
            song_name TEXT NOT NULL,
            artist TEXT NOT NULL,
            video_id TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlist_songs (
            playlist_id INTEGER,
            song_id INTEGER,
            position INTEGER,
            lw INTEGER,
            peak INTEGER,
            weeks INTEGER,
            is_new INTEGER,
            is_reentry INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# Function to check if a playlist exists in the database
def get_playlist_from_db(date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            s.id,
            s.song_name, 
            s.artist, 
            s.video_id,
            ps.position, 
            ps.lw, 
            ps.peak, 
            ps.weeks, 
            ps.is_new, 
            ps.is_reentry
        FROM 
            playlists p 
            JOIN playlist_songs ps ON p.id = ps.playlist_id 
            JOIN songs s ON ps.song_id = s.id
        WHERE 
            p.date = ?
    ''', (date,))
    rows = cursor.fetchall()
    conn.close()

    # Convert rows to list of dictionaries to match the JSON structure of scrape_songs
    playlist = [
        {
            'id' : int(row['id']),
            'position': int(row['position']),
            'is_new': bool(row['is_new']), 
            'is_reentry': bool(row['is_reentry']),
            'song_name': row['song_name'],
            'artist': row['artist'],
            'lw': int(row['lw']),
            'peak': int(row['peak']),
            'weeks': int(row['weeks']),
            'video_id': row['video_id']
        } 
        for row in rows
    ]
    logger.info(f'Playlist for date {date} containing {len(playlist)} records retrieved from the db.')
    return playlist

def add_playlist_to_db(date, songs):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Add a new playlist for the given date
    cursor.execute('INSERT INTO playlists (date) VALUES (?)', (date,))
    playlist_id = cursor.lastrowid

    for position, song in enumerate(songs, start=1):
        # Check if the song already exists in the songs table
        cursor.execute('SELECT id FROM songs WHERE song_name = ? AND artist = ?', (song['song_name'], song['artist']))
        song_id = cursor.fetchone()
        if song_id is None:
            # If the song doesn't exist, add it to the songs table
            cursor.execute('INSERT INTO songs (song_name, artist) VALUES (?, ?)', (song['song_name'], song['artist']))
            song_id = cursor.lastrowid
        else:
            song_id = song_id[0]

        # Add the song to the playlist
        cursor.execute('''
            INSERT INTO playlist_songs (playlist_id, song_id, position, lw, peak, weeks, is_new, is_reentry)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (playlist_id, song_id, position, song['lw'], song['peak'], song['weeks'], song['is_new'], song['is_reentry']))
    
    logger.info(f'Playlist for date {date} added to the db successfully.')
    conn.commit()
    conn.close()

def get_video_from_db(song_name, artist):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            id, video_id
        FROM 
            songs
        WHERE 
            song_name = ? AND artist = ?
    ''', (song_name, artist,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        'id': row['id'],
        'video_id': row['video_id']
    }

from git import Repo

def commit_changes(repo_path, commit_message):
    repo = Repo(repo_path)
    repo.git.add(update=True)
    repo.index.commit(commit_message)
    repo.git.push('origin', 'main')

def update_video_in_db(song_id, video_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE songs
        SET video_id = ?
        WHERE id = ?
    ''', (video_id, song_id,))
    conn.commit()
    conn.close()

def scrape_songs(date):

    # Make a request to the website
    url = f'https://www.officialcharts.com/charts/singles-chart/{date}/7501/' 
    response = requests.get(url)

    # Use the 'html.parser' to parse the page
    soup = BeautifulSoup(response.text, 'html.parser')

     # Find all the div tags with class 'description block'
    divs = soup.find_all('div', class_='description block')

    # Create a list to store the song data
    songs = []

     # Extract and print the song name, artist, and chart information
    for div in divs:
        song_name_tag = div.find('a', class_='chart-name font-bold inline-block')
        if song_name_tag is None:
            logger.error(f'Unable to find song name tag for div: {div}')
            continue

        song_name_elements = song_name_tag.find_all('span')
        if len(song_name_elements) == 0:
            logger.error(f'Unable to find song name elements for div: {div}')
            continue

        re_new = song_name_elements[0].get_text(strip=True).upper() if len(song_name_elements) > 1 else ''
        song_name = song_name_elements[-1].get_text(strip=True)

        artist_tag = div.find('a', class_='chart-artist text-lg inline-block')
        if artist_tag is None:
            logger.error(f'Unable to find artist tag for div: {div}')
            continue
        artist = artist_tag.get_text(strip=True)

        lw_tag = div.find('li', class_='movement px-2 py-1 rounded-md inline-block mr-1 sm:mr-2')
        if lw_tag is None:
            logger.error(f'Unable to find lw tag for div: {div}')
            continue
        lw = lw_tag.get_text(strip=True).split(':')[1].replace(',', '')

        peak_tag = div.find('li', class_='peak px-2 py-1 rounded-md inline-block mr-1 sm:mr-2')
        if peak_tag is None:
            logger.error(f'Unable to find peak tag for div: {div}')
            continue
        peak = peak_tag.get_text(strip=True).split(':')[1].replace(',', '')

        weeks_tag = div.find('li', class_='weeks px-2 py-1 rounded-md inline-block mr-1 sm:mr-2')
        if weeks_tag is None:
            logger.error(f'Unable to find weeks tag for div: {div}')
            continue
        weeks = weeks_tag.get_text(strip=True).split(':')[1]

        video_id = ''  # This will be populated by a separate process

        # Determine if the song is new or a reentry
        is_new = re_new.lower() == 'new' or lw.lower() == 'new'
        is_reentry = re_new.lower() == 're' or 'lw'.lower() == 're'

         # If the song is new or a reentry, set lw to 0
        if is_new or is_reentry:
            lw = 0

        song = {
            'is_new': bool(is_new), 
            'is_reentry': bool(is_reentry),
            'song_name': song_name,
            'artist': artist,
            'lw': int(lw),
            'peak': int(peak),
            'weeks': int(weeks),
            'video_id': video_id
        }
        
        songs.append(song)

    logger.info(f'Songs for date {date} scraped from web successfully.')
    return songs

def debug_dump_songs(songs):
    songs_json = json.dumps(songs, indent=4)
    logger.debug(songs_json)

#
# Get songs for a given date. If they don't exist in the database, scrape them from the web
@app.route('/api/songs/<date>', methods=['GET'])
def get_songs(date):
    logger.info(f'Getting songs for date {date}.')

    # Check if the playlist is already in the database
    playlist = get_playlist_from_db(date)
    if playlist:
        return jsonify(playlist)
    
    logger.info(f'Playlist for date {date} not found in the db')

    return jsonify([])

# Route for the server status
@app.route('/api/status', methods=['GET'])
def get_server_status():
    return jsonify({'status': 'Server is running'})

# Route for creating a youtube playlist
from flask import request
from . import youtube

@app.route('/api/create_playlist', methods=['POST'])
def create_playlist():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    tracks = data.get('tracks')

    logger.info(f'Creating playlist with title: {title}, description: "{description}", with {len(tracks)} tracks.')
    logger.debug(f'Tracks: {tracks}')
    youtube_authenticated_service = youtube.get_authenticated_service()

    try:
        # Create a new playlist
        playlist_id = youtube.create_playlist(youtube_authenticated_service, title, description)

        # Add songs to the playlist
        for track in tracks:
            video_id = track.get('videoId')
            if not video_id:
                # If the song does not have a video ID, retrieve it
                video_id = youtube.get_youtube_video_id(f"{track['title']} {track['artist']}")
            if video_id:
                youtube.add_video_to_playlist(youtube_authenticated_service, playlist_id, video_id)

        return {'status': 'success', 'playlist_id': playlist_id}, 200

    except Exception as e:
        logger.error(f'An error occurred: {e}')
        return {'status': 'error', 'message': str(e)}, 500
    
@app.route('/api/update_videos', methods=['POST'])
def update_videos():
    data = request.get_json()
    tracks = data.get('tracks')

    updated = 0
    for track in tracks:
        title = track.get('title')
        artist = track.get('artist')
        video_id = track.get('videoId')

        if not video_id:
            # If the song does not have a video ID, skip it
            logger.info(f'Skipping video update for song {title} by {artist} because it does not have a video ID.')
            continue

        song_record = get_video_from_db(title, artist)

        if song_record is not None and song_record['video_id'] != video_id:
            logger.info(f'Updating video ID for song {title} by {artist} from {song_record["video_id"]} to {video_id}.')
            update_video_in_db(song_record['id'], video_id)
            updated += 1
        else:
            logger.info(f'Skipping video update for song {title} by {artist} because it either does not exist or is already up to date.')

    if updated > 0:
        commit_changes('/Users/martindavy/source/repos/toptastic/toptastic-data', 'Server Updated videos')

    return {
        'status': 'success',
        'updated': updated,
    }, 200