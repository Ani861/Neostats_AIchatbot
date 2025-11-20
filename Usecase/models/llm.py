import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from config.config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

def get_llm():
    
    try:
        if not GOOGLE_API_KEY:
            raise ValueError("API Key not found in configuration.")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            google_api_key=GOOGLE_API_KEY,
            temperature=0, 
            max_retries=2,
        )
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        raise e