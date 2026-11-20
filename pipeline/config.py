import os
from pathlib import Path

# Paths, built from this file's location so they work on any laptop
ROOT = Path(__file__).resolve().parent.parent
ID_LIST = ROOT / "data" / "input" / "id_list.csv"
CACHE_DIR = ROOT / "data" / "cache"
OUTPUT_DIR = ROOT / "data" / "output"

# TMDb API
API_BASE_URL = "https://api.themoviedb.org/3"
REQUEST_TIMEOUT = (5, 30)        
MAX_RETRIES = 3                  
BACKOFF_SECONDS = 1         
PAUSE_BETWEEN_CALLS = 0.25   
USER_AGENT = "streamvault-licensing-analysis (AmaliTech DE02 training)"

# Analysis rules
WINDOW_START_YEAR = 2000
LEAD_ACTOR_COUNT = 3 


def get_api_key() -> str:
    """Return the TMDb key from the environment, or stop with a clear message."""
    key = os.environ.get("TMDB_API_KEY")
    if not key:
        raise RuntimeError(
            "TMDB_API_KEY is not set. See the README for how to set it."
        )
    return key