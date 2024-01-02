import logging
from my_app.toptastic_api import app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("toptastic.log", mode="w"),
        logging.StreamHandler()
    ]
)

if __name__ == '__main__':
    app.run(debug=True)