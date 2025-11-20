import os
import logging
from dotenv import load_dotenv

# Setup Global Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


load_dotenv()

try:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        logging.warning(" GOOGLE_API_KEY is missing. Ensure it is set in Streamlit Secrets or .env file.")
except Exception as e:
    logging.error(f"Error loading configuration: {e}")
    GOOGLE_API_KEY = None