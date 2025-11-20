import logging
from langchain_community.tools import DuckDuckGoSearchRun

logger = logging.getLogger(__name__)

def perform_web_search(query):
   
    try:
        search = DuckDuckGoSearchRun()
        return search.run(query)
    except Exception as e:
        logger.error(f"Web search failed: {e}")
        return f"Search failed: {e}"