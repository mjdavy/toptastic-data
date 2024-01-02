import datetime
import logging
import sys
from my_app.toptastic_api import add_playlist_to_db, debug_dump_songs, get_playlist_from_db, get_songs, scrape_songs

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

#
# Get songs for a given date. If they don't exist in the database, scrape them from the web
#
def fetch_and_store_songs(date):
    logging.info(f'Getting songs for date {date}.')

    # Convert the date to the desired format (yyyymmdd)
    date_str = date.strftime("%Y%m%d")
    logging.info(f'Converted date {date} to {date_str}.')

    # Check if the playlist is already in the database
    playlist = get_playlist_from_db(date_str)
    if playlist:
        logging.info(f'Playlist for date {date} containing {len(playlist)} songs fetched from the db.')
        debug_dump_songs(playlist)
        return
    
    logging.info(f'Playlist for date {date} not found in the db. Performing web scrape.')
    songs = scrape_songs(date)
    logging.info(f'Playlist for date {date} scraped from web returned {len(songs)} songs.')

    # Convert the songs to a JSON string and print it to the console
    debug_dump_songs(songs)

     # Add the playlist to the database
    if len(songs) >= 40:
        add_playlist_to_db(date_str, songs)
    else:
        logging.error(f'Playlist for date {date} only contains {len(songs)} songs. Not adding to the db.')

# Get the current date
today = datetime.date.today()

# Get today's date
today = datetime.date.today()

# Find the most recent Friday
if today.weekday() == 4:
    # Today is Friday, use the previous Friday
    days_since_last_friday = 7
else:
    # Find the most recent Friday
    days_since_last_friday = (today.weekday() - 4) % 7

current_date = today - datetime.timedelta(days=days_since_last_friday)

# Find the first Friday of the year 2000
year_2000 = datetime.date(2000, 1, 1)
first_friday = year_2000 + datetime.timedelta(days=(4 - year_2000.weekday() + 7) % 7)

# Iterate over the Fridays from most recent (not including today if is it friday) back to the first Friday of the year 2000

while current_date >= first_friday:

    logging.info(f'Fetching songs for {current_date}.')

    try :
        # Call the get_songs function for each Friday
        fetch_and_store_songs(current_date)

    except Exception as e:
        # Handle the exception gracefully
        logging.error(f"Error occurred for {current_date}: {e}")

    # Move to the previous Friday
    current_date -= datetime.timedelta(days=7)