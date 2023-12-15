import logging
from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import sqlite3

app = Flask(__name__)

logging.basicConfig(filename='app.log', level=logging.INFO)

def get_db_connection():
    conn = sqlite3.connect('songs.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/songs/<date>', methods=['GET'])
def get_songs(date):
    conn = get_db_connection()
    songs = conn.execute('SELECT * FROM songs WHERE date = ?', (date,)).fetchall()

    if songs:
        logging.info(f'Songs for date {date} found in database.')
        return jsonify([dict(ix) for ix in songs])

    url = f'https://www.officialcharts.com/charts/singles-chart/{date}/7501/' 
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    divs = soup.find_all('div', class_='description block')

    songs = []
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

        conn.execute('''
            INSERT INTO songs (date, re_new, song_name, artist, lw, peak, weeks, video_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, re_new, song_name, artist, lw, peak, weeks, video_id))

    conn.commit()
    conn.close()

    logging.info(f'Songs for date {date} scraped from web and stored in database.')
    return jsonify(songs)

if __name__ == '__main__':
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            date TEXT,
            re_new TEXT,
            song_name TEXT,
            artist TEXT,
            lw TEXT,
            peak TEXT,
            weeks TEXT,
            video_id TEXT
        )
    ''')
    conn.close()
    app.run(debug=True)