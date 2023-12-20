import sqlite3

def rename_and_delete_tables():
    conn = sqlite3.connect('songs.db')
    cursor = conn.cursor()

    # Rename old songs table
    cursor.execute('ALTER TABLE songs RENAME TO old_songs')

    # Rename new tables (if needed)
    cursor.execute('ALTER TABLE new_songs RENAME TO songs')
    cursor.execute('ALTER TABLE new_playlists RENAME TO playlists')
    cursor.execute('ALTER TABLE new_playlist_songs RENAME TO playlist_songs')

    # Delete old songs table
    cursor.execute('DROP TABLE IF EXISTS old_songs')

    conn.commit()
    conn.close()

def update_lw_field():
    conn = sqlite3.connect('songs.db')
    cursor = conn.cursor()

    # Select all records from new_playlist_songs
    cursor.execute('SELECT * FROM new_playlist_songs')
    records = cursor.fetchall()

    for record in records:
        playlist_id, song_id, position, lw, peak, weeks, is_new, is_reentry = record

        # Check if lw field contains 'New' or 'RE'
        if str(lw) in ['New', 'RE']:
            # Update the lw field to 0
            cursor.execute('''
                UPDATE new_playlist_songs
                SET lw = 0
                WHERE playlist_id = ? AND song_id = ? AND position = ?
            ''', (playlist_id, song_id, position))

    conn.commit()
    conn.close()    

def create_new_tables():
    conn = sqlite3.connect('songs.db')
    cursor = conn.cursor()

    # Create new tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS new_songs (
            id INTEGER PRIMARY KEY,
            song_name TEXT NOT NULL,
            artist TEXT NOT NULL,
            video_id TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS new_playlists (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS new_playlist_songs (
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

def insert_song(song_name, artist, video_id):
    conn = sqlite3.connect('songs.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO new_songs (song_name, artist, video_id)
        VALUES (?, ?, ?)
    ''', (song_name, artist, video_id))

    song_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return song_id

def insert_playlist(date):
    conn = sqlite3.connect('songs.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO new_playlists (date)
        VALUES (?)
    ''', (date,))

    playlist_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return playlist_id

def insert_playlist_song(playlist_id, song_id, position, lw, peak, weeks, is_new, is_reentry):
    conn = sqlite3.connect('songs.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO new_playlist_songs (playlist_id, song_id, position, lw, peak, weeks, is_new, is_reentry)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (playlist_id, song_id, position, lw, peak, weeks, is_new, is_reentry))

    conn.commit()
    conn.close()

def convert_data():
    conn = sqlite3.connect('songs.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM songs ORDER BY date')
    songs = cursor.fetchall()

    current_date = None
    position = 0

    for song in songs:
        date, re_new, song_name, artist, lw, peak, weeks, video_id = song

        if date != current_date:
            current_date = date
            playlist_id = insert_playlist(date)
            position = 0

        song_id = insert_song(song_name, artist, video_id)

        is_new = 1 if re_new == 'NEW' else 0
        is_reentry = 1 if re_new == 'RE' else 0

        insert_playlist_song(playlist_id, song_id, position, lw, peak, weeks, is_new, is_reentry)

        position += 1

    conn.close()

# Run the conversion
#create_new_tables()
#convert_data()
# update_lw_field()
rename_and_delete_tables()