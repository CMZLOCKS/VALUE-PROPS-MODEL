"""
Configuration file for NBA Props Model - The Odds API Version
"""

# ====================
# THE ODDS API CONFIGURATION
# ====================

ODDS_API_KEY = '44f324b50f4a7ba9388f08341dd36c72'
ODDS_API_BASE_URL = 'https://api.the-odds-api.com/v4'
NBA_SPORT_KEY = 'basketball_nba'
DAYS_AHEAD = 3

# ====================
# BOOKMAKERS & MARKETS
# ====================

BOOKMAKERS = ['fanduel', 'draftkings', 'betmgm', 'pointsbet', 'caesars', 'pinnacle']
PROP_MARKETS = ['player_points', 'player_assists', 'player_rebounds', 'player_threes']

PROP_TYPES = {
    'player_points': {'name': 'Points', 'stat_key': 'PTS', 'enabled': True},
    'player_assists': {'name': 'Assists', 'stat_key': 'AST', 'enabled': True},
    'player_rebounds': {'name': 'Rebounds', 'stat_key': 'REB', 'enabled': True},
    'player_threes': {'name': '3-Pointers', 'stat_key': 'FG3M', 'enabled': True}
}

# ====================
# MODEL SETTINGS
# ====================

RECENT_GAMES_WINDOW = 10
MIN_GAMES_PLAYED = 3
MIN_AI_SCORE_THRESHOLD = 10
MIN_AI_SCORE_BY_TYPE = {
    'points': 10.0, 'assists': 10.0, 'rebounds': 10.0,
    'threes': 10.0, '3-pointers': 10.0
}
TOP_PLAYS_COUNT = 6

# Sharp display: minimum ~25 props, balanced across points/assists/rebounds/threes (top by AI score per type)
TARGET_MIN_DISPLAY = 25
MIN_DISPLAY_PER_TYPE = 7   # min from each of points, assists, rebounds, threes (7+6+6+6=25 or cap per type)

WEIGHTS = {
    'recent_form': 0.30, 'season_average': 0.20, 'consistency': 0.25,
    'trending': 0.15, 'sample_size': 0.10
}

DASHBOARD_TITLE = "CMZPROPS MODEL"
DASHBOARD_SUBTITLE = "NBA Props Model • Live API Data • Season 2025-26"

COLORS = {
    'primary': '#1a472a', 'secondary': '#2d5a3d', 'accent': '#4ade80',
    'background': '#0f172a', 'card': '#1e293b', 'text': '#e2e8f0',
    'success': '#22c55e', 'danger': '#ef4444'
}

# ====================
# FILE PATHS
# ====================

DATA_DIR = 'data'
PROPS_HISTORY_FILE = f'{DATA_DIR}/props_history.json'
PERFORMANCE_FILE = f'{DATA_DIR}/performance.json'
TRACKING_FILE = f'{DATA_DIR}/props_tracking.json'
OUTPUT_HTML = 'index.html'

# ====================
# DEBUGGING & NEW TRACKING
# ====================

DEBUG_MODE = True
SAVE_API_RESPONSES = True

# New: Daily tracking & betting units
UNITS_PER_BET = 1.0

# Grading: hours after game start before we try to grade (stats available)
GRADING_HOURS_AFTER_GAME = 4