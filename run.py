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
    port = 5001
    logging.info('Starting server...')
    create_tables_if_needed()
    # Print the status URL to the console
    logging.info(f"Access the status URL at http://localhost:{port}/api/status")
    app.run(host='0.0.0.0', debug=True, port=port)
