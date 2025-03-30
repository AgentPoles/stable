"""Configuration settings for the application."""

from typing import List, Dict

# Configuration for parties to analyze
PARTIES = {
    "target": "0xECC2a9240268BC7a26386ecB49E1Befca2706AC9",  # StableLabs
    "whale": "0x8b37a5Af68D315cf5A64097D96621F64b5502a22"   # Whale
}

# Configuration for Snapshot spaces to analyze
SPACES = [
    {
        "name": "AAVE",
        "space_id": "aave.eth"
    }
]

# Number of proposals to fetch per request
NUMBER_OF_PROPOSALS_PER_REQUEST = 30

# Number of votes to fetch per request
NUMBER_OF_VOTES_PER_REQUEST = 100

# Rate limiting settings
MAX_REQUESTS_PER_WINDOW = 10
TIME_WINDOW_SECONDS = 1.0

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1 