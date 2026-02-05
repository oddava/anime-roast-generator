"""Application constants and configuration values."""

# ============================================
# Rate Limiting
# ============================================

# Roast generation rate limit
ROAST_RATE_LIMIT_PER_MINUTE = 10

# Anime search rate limit
SEARCH_RATE_LIMIT_PER_MINUTE = 30

# Anime details rate limit
ANIME_DETAILS_RATE_LIMIT_PER_MINUTE = 30

# Comments rate limits
COMMENT_CREATE_RATE_LIMIT_PER_MINUTE = 5
COMMENT_VOTE_RATE_LIMIT_PER_MINUTE = 10
COMMENT_EDIT_RATE_LIMIT_PER_MINUTE = 5
COMMENT_DELETE_RATE_LIMIT_PER_MINUTE = 5

# ============================================
# Comment Configuration
# ============================================

# Maximum comment content length
MAX_COMMENT_LENGTH = 1000

# Maximum author name length
MAX_AUTHOR_NAME_LENGTH = 50

# Comment edit time limit (15 minutes in seconds)
COMMENT_EDIT_TIME_LIMIT_SECONDS = 15 * 60

# Maximum comment depth for threading
MAX_COMMENT_DEPTH = 3

# Default comments per page
DEFAULT_COMMENTS_PER_PAGE = 20

# Maximum comments per page
MAX_COMMENTS_PER_PAGE = 50

# ============================================
# Spam Detection
# ============================================

# Maximum comments per minute per IP
MAX_COMMENTS_PER_MINUTE = 10

# Burst detection threshold
BURST_THRESHOLD = 3

# Burst delay in seconds
BURST_DELAY_SECONDS = 10

# Duplicate detection window in minutes
DUPLICATE_WINDOW_MINUTES = 5

# Similarity threshold (0.0 - 1.0)
SIMILARITY_THRESHOLD = 0.9

# ============================================
# Anime Search
# ============================================

# Minimum search query length
MIN_SEARCH_QUERY_LENGTH = 2

# Maximum search query length
MAX_SEARCH_QUERY_LENGTH = 100

# Default search results per page
DEFAULT_SEARCH_RESULTS = 10

# Maximum search results per page
MAX_SEARCH_RESULTS = 50

# ============================================
# Roast Generation
# ============================================

# Maximum anime name length
MAX_ANIME_NAME_LENGTH = 100

# Gemini API timeout in seconds
GEMINI_API_TIMEOUT_SECONDS = 30

# Maximum retries for roast generation
MAX_ROAST_RETRIES = 2

# Cache TTL in seconds (1 hour)
CACHE_TTL_SECONDS = 3600

# Maximum cache size
MAX_CACHE_SIZE = 1000

# ============================================
# Review Analysis
# ============================================

# Minimum reviews required for analysis
MIN_REVIEWS_FOR_ANALYSIS = 10

# Maximum reviews to fetch
MAX_REVIEWS_TO_FETCH = 25

# Maximum verified complaints to return
MAX_VERIFIED_COMPLAINTS = 5

# Minimum confidence threshold for complaints (0.0 - 1.0)
MIN_CONFIDENCE_THRESHOLD = 0.6

# ============================================
# Security
# ============================================

# Maximum request body size in bytes (1MB)
MAX_REQUEST_BODY_SIZE = 1 * 1024 * 1024

# CORS preflight cache max age in seconds (10 minutes)
CORS_MAX_AGE_SECONDS = 600

# Security headers
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

# ============================================
# Frontend
# ============================================

# Roast history maximum items
MAX_ROAST_HISTORY_ITEMS = 20

# Local storage keys
LOCAL_STORAGE_KEYS = {
    "roast_history": "animeRoastHistory",
    "username": "animeRoastUsername_v2",
    "collapsed_threads": "animeRoastCollapsedThreads",
}

# Cookie keys
COOKIE_KEYS = {
    "username": "animeRoastUsername",
}

# ============================================
# Timeouts
# ============================================

# AniList API timeout
ANILIST_TIMEOUT_SECONDS = 10

# AniList connection timeout
ANILIST_CONNECT_TIMEOUT_SECONDS = 5

# Frontend API request timeout
FRONTEND_API_TIMEOUT_MS = 35000

# ============================================
# Stats Default Values
# ============================================

DEFAULT_STATS = {
    "horniness_level": 50,
    "plot_armor_thickness": 50,
    "filler_hell": 50,
    "power_creep": 50,
    "cringe_factor": 50,
    "fan_toxicity": 50,
}
