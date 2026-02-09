"""
Configuration file for NBA Props Model - The Odds API Version
"""

# ====================
# THE ODDS API CONFIGURATION
# ====================

# Your The Odds API key - from https://the-odds-api.com/
ODDS_API_KEY = '44f324b50f4a7ba9388f08341dd36c72'

# The Odds API base URL
ODDS_API_BASE_URL = 'https://api.the-odds-api.com/v4'

# Sport key for NBA
NBA_SPORT_KEY = 'basketball_nba'

# How many days ahead to fetch games for (0 = today only, 3 = today + next 3 days)
DAYS_AHEAD = 3

# ====================
# BOOKMAKERS TO FETCH
# ====================

# Which sportsbooks to get odds from
BOOKMAKERS = [
    'fanduel',
    'draftkings', 
    'betmgm',
    'pointsbet',
    'caesars',
    'pinnacle'
]

# ====================
# PROP MARKETS TO FETCH
# ====================

# Player prop markets we want
PROP_MARKETS = [
    'player_points',
    'player_assists',
    'player_rebounds',
    'player_threes'
]

# ====================
# PROP TYPES MAPPING
# ====================

PROP_TYPES = {
    'player_points': {
        'name': 'Points',
        'stat_key': 'PTS',
        'enabled': True
    },
    'player_assists': {
        'name': 'Assists', 
        'stat_key': 'AST',
        'enabled': True
    },
    'player_rebounds': {
        'name': 'Rebounds',
        'stat_key': 'REB',
        'enabled': True
    },
    'player_threes': {
        'name': '3-Pointers',
        'stat_key': 'FG3M',
        'enabled': True
    }
}

# ====================
# MODEL SETTINGS
# ====================

# How many recent games to analyze for player averages
RECENT_GAMES_WINDOW = 10

# How many games to require before making a prediction
MIN_GAMES_PLAYED = 3

# Minimum AI score to be considered a "value play" (0-10 scale)
# Global fallback threshold
MIN_AI_SCORE_THRESHOLD = 10

# Per-prop-type minimum AI score thresholds
# Points/Assists/Rebounds require 10, 3-Pointers require 7.5
MIN_AI_SCORE_BY_TYPE = {
    'points': 10.0,
    'assists': 10.0,
    'rebounds': 10.0,
    'threes': 10.0,
    '3-pointers': 10.0,
}

# How many "best plays" to feature at the top of dashboard
TOP_PLAYS_COUNT = 6

# ====================
# STATISTICAL WEIGHTS
# ====================

# How much weight to give different factors in AI score calculation
WEIGHTS = {
    'recent_form': 0.30,      # Last 10 games average
    'season_average': 0.20,   # Full season average
    'consistency': 0.25,      # How consistent player has been
    'trending': 0.15,         # Is player trending up or down
    'sample_size': 0.10       # How many games played
}

# ====================
# DASHBOARD SETTINGS
# ====================

# Title for your dashboard
DASHBOARD_TITLE = "CourtSide Analytics - NBA Props"

# Subtitle
DASHBOARD_SUBTITLE = "Powered by The Odds API • Real-Time Props"

# Color scheme
COLORS = {
    'primary': '#1a472a',      # Dark green
    'secondary': '#2d5a3d',    # Medium green
    'accent': '#4ade80',       # Light green
    'background': '#0f172a',   # Dark blue-gray
    'card': '#1e293b',         # Card background
    'text': '#e2e8f0',         # Light gray text
    'success': '#22c55e',      # Green for wins
    'danger': '#ef4444'        # Red for losses
}

# ====================
# FILE PATHS
# ====================

# Where to store data
DATA_DIR = 'data'
PROPS_HISTORY_FILE = f'{DATA_DIR}/props_history.json'
PERFORMANCE_FILE = f'{DATA_DIR}/performance.json'

# Output file name
OUTPUT_HTML = 'index.html'

# ====================
# DEBUGGING
# ====================

# Set to True to see detailed logs in console
DEBUG_MODE = True

# Set to True to save API responses to files (for troubleshooting)
SAVE_API_RESPONSES = True