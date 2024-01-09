import logging
from my_app.youtube import update_video_ids

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("youtube.log", mode="w"),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    update_video_ids()