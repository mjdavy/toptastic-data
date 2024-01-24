import logging
from my_app.youtube import download_video
from my_app.toptastic_api import get_playlist_from_db
import os
import certifi
from datetime import datetime
from dateutil.relativedelta import relativedelta, FR
import json
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("download.log", mode="w"),
        logging.StreamHandler()
    ]
)

def get_last_friday(date):
    if date.weekday() == 4:  # If today is Friday
        last_friday = date + relativedelta(weekday=FR(-2))  # Get the Friday of last week
    else:
        last_friday = date + relativedelta(weekday=FR(-1))  # Get the most recent Friday
    return last_friday.date()


def valid_date(s):
    try:
        date = datetime.strptime(s, "%Y%m%d")
        if date.year < 2000:
            raise argparse.ArgumentTypeError("Date must be later than the year 2000")
        return date
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("date", help="The date for the playlist in YYYYMMDD format", type=valid_date)
    args = parser.parse_args()

    os.environ['SSL_CERT_FILE'] = certifi.where()
    logging.info('Starting download.py')
    try:
        playlist_date = get_last_friday(args.date).strftime('%Y%m%d')
        logging.info(f'Getting playlist for {playlist_date}')
        playlist = get_playlist_from_db(playlist_date)
        if playlist:
            video_folder = os.path.expanduser('~/Downloads/videos')
            playlist_folder = os.path.join(video_folder, playlist_date)
            os.makedirs(playlist_folder, exist_ok=True)
            with open(os.path.join(playlist_folder, 'playlist.json'), 'w') as f:
                json.dump(playlist, f, indent=4)
            for song in playlist:
                video_file = f"{song['video_id']}.mp4"
                try:
                    download_video(song['video_id'], playlist_folder, video_file)
                except FileExistsError:
                    logging.info(f'File already downloaded: {video_file}')
                except Exception as e:
                    logging.error(f'Error downloading video: {e}')
            
    except Exception as e:
        logging.error(f'Error getting playlist: {e}')
        raise e
    
if __name__ == "__main__":
    run()