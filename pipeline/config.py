"""Settings for the StreamVault pipeline: paths, API settings and analysis rules."""

import os
from pathlib import Path

# Paths, built from this file's location so they work on any laptop
ROOT = Path(__file__).resolve().parent.parent
ID_LIST = ROOT / "data" / "input" / "id_list.csv"
CACHE_DIR = ROOT / "data" / "cache"
OUTPUT_DIR = ROOT / "data" / "output"
CHECKS_DIR = OUTPUT_DIR / "checks"   # spot-check and timing results, kept between runs

# TMDb API
API_BASE_URL = "https://api.themoviedb.org/3"
REQUEST_TIMEOUT = (5, 30)        # seconds: (connect, read)
MAX_RETRIES = 3                  # for timeouts, 429 and 5xx only
BACKOFF_SECONDS = 1              # waits 1, 2, 4 seconds between retries
PAUSE_BETWEEN_CALLS = 0.25       # seconds, so we don't overload a free API
USER_AGENT = "streamvault-licensing-analysis (AmaliTech DE02 training)"

# Analysis rules
WINDOW_START_YEAR = 2000
MIN_GROUP_SIZE = 5               # a median over fewer films is shown but marked not reliable
MIN_FILMS_PER_FRANCHISE = 2      # films on the list before a franchise can be shortlisted (Q7)
MIN_FILMS_PER_PERSON = 3         # films before a director or lead counts as a signal
MIN_SERIES_PER_PERSON = 2        # ...spread over at least this many different series
STANDALONE_SHORTLIST = 5
FRANCHISE_SHORTLIST = 3
CUTOFF_YEARS_TO_TEST = [1980, 1990, 1995, 2000, 2005, 2010]   # for the cut-off sensitivity table
SPOT_CHECK_SEED = 2026           # fixed, so the random part of the spot-check repeats
SPOT_CHECK_RANDOM = 4            # films drawn at random for the spot-check
MONEY_TOLERANCE = 0.01           # budget and revenue may differ by up to 1% in the spot-check
LEAD_ACTOR_COUNT = 3             # billing orders 0, 1 and 2 count as lead actors (Q8)


def get_api_key() -> str:
    """Return the TMDb key from the environment, or stop with a clear message."""
    key = os.environ.get("TMDB_API_KEY")
    if not key:
        raise RuntimeError(
            "TMDB_API_KEY is not set. See the README for how to set it."
        )
    return key