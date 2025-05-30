import requests
import logging

def keep_alive_ping():
    try:
        response = requests.get("https://thomaggio-backend.onrender.com/health")
        if response.status_code == 200:
            logging.info("Ping de keep-alive -> OK")
        else:
            logging.warning(f"Ping de keep-alive deu status -> {response.status_code}")
    except Exception as e:
        logging.error(f"Erro no ping de keep-alive -> {e}")
