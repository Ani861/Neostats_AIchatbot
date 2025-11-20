import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings 
from config.config import GOOGLE_API_KEY 

logger = logging.getLogger(__name__)

def get_embedding_model():
   
    try:
        if not GOOGLE_API_KEY:
            raise ValueError("API Key not found for embeddings.")
            
        return GoogleGenerativeAIEmbeddings(
            # CHANGE THIS LINE: Add "models/" prefix
            model="models/text-embedding-004", 
            google_api_key=GOOGLE_API_KEY
        )
    except Exception as e:
        logger.error(f"Failed to initialize Embeddings: {e}")
        raise e