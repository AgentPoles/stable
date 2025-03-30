"""Configuration settings for the application."""

# AAVE Governance Space ID
AAVE_SNAPSHOT_SPACE_ID = "aave.eth"

# Stable Labs address
STABLE_LABS = "0xECC2a9240268BC7a26386ecB49E1Befca2706AC9"

# Whale address
WHALE = "0x8b37a5Af68D315cf5A64097D96621F64b5502a22"

# Number of proposals to fetch per request
NUMBER_OF_PROPOSALS_PER_REQUEST = 30

# Rate limiting settings
MAX_REQUESTS_PER_WINDOW = 10
TIME_WINDOW_SECONDS = 1.0

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1 