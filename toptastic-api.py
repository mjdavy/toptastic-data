import logging
from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import sqlite3
import sys

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

def get_db_connection():
    conn = sqlite3.connect('songs.db')
    conn.row_factory = sqlite3.Row
    return conn

#
# Get songs for a given date. If they don't exist in the database, scrape them from the web
@app.route('/api/songs/<date>', methods=['GET'])
def get_songs(date):

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
        song_name_elements = song_name_tag.find_all('span')
        re_new = song_name_elements[0].get_text(strip=True).upper() if len(song_name_elements) > 1 else ''
        song_name = song_name_elements[-1].get_text(strip=True)
        artist = div.find('a', class_='chart-artist text-lg inline-block').get_text(strip=True)
        lw = div.find('li', class_='movement px-2 py-1 rounded-md inline-block mr-1 sm:mr-2').get_text(strip=True).split(':')[1].replace(',', '')
        peak = div.find('li', class_='peak px-2 py-1 rounded-md inline-block mr-1 sm:mr-2').get_text(strip=True).split(':')[1].replace(',', '')
        weeks = div.find('li', class_='weeks px-2 py-1 rounded-md inline-block mr-1 sm:mr-2').get_text(strip=True).split(':')[1]
        video_id = ''  # This will be populated by a separate process

        song = {
            're_new': re_new,
            'song_name': song_name,
            'artist': artist,
            'lw': lw,
            'peak': peak,
            'weeks': weeks,
            'video_id': video_id
        }
        
        songs.append(song)

    logging.info(f'Songs for date {date} scraped from web successfully.')
    return jsonify(songs)
  
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

# main entry point

if __name__ == '__main__':
    create_tables_if_needed()
    app.run(debug=True)