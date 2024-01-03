import logging
from my_app.toptastic_api import app, create_tables_if_needed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("toptastic.log", mode="w"),
        logging.StreamHandler()
    ]
)

if __name__ == '__main__':
    logging.info('Starting server...')
    create_tables_if_needed()
    # Print the status URL to the console
    logging.info("Access the status URL at http://localhost:8080/api/status")
    app.run(debug=True,port=8080)
