"""
Data Fetcher Module - The Odds API + Estimated Stats Fallback
This file handles all communication with The Odds API and provides player stats

STRATEGY: Uses estimated stats for common players to ensure the model always works
"""

import os
import requests
import json
import re
import time
import unicodedata
from datetime import datetime, timedelta
from config import *

# Default value for DAYS_AHEAD if not in config
try:
    DAYS_AHEAD
except NameError:
    DAYS_AHEAD = 3  # Default: today + next 3 days

# Manual alias map
PLAYER_NAME_ALIASES = {
    "nicolas claxton": "nic claxton",
    "cameron johnson": "cam johnson",
    "carlton carrington": "bub carrington",
    "c.j. mccollum": "cj mccollum",
}

# Estimated stats for NBA players (2024-25 season) - Add more as needed
FALLBACK_PLAYER_STATS = {
    # Dallas Mavericks
    "luka doncic": {"PTS": 28.5, "AST": 8.5, "REB": 8.2, "FG3M": 3.5, "GP": 50, "TEAM": "DAL"},
    "kyrie irving": {"PTS": 25.2, "AST": 5.5, "REB": 4.8, "FG3M": 3.0, "GP": 50, "TEAM": "DAL"},
    "klay thompson": {"PTS": 14.5, "AST": 2.5, "REB": 3.5, "FG3M": 2.8, "GP": 48, "TEAM": "DAL"},
    "pj washington": {"PTS": 12.5, "AST": 2.2, "REB": 6.8, "FG3M": 1.8, "GP": 50, "TEAM": "DAL"},
    "dereck lively ii": {"PTS": 9.2, "AST": 1.5, "REB": 7.8, "FG3M": 0.0, "GP": 50, "TEAM": "DAL"},
    "daniel gafford": {"PTS": 11.5, "AST": 1.2, "REB": 5.5, "FG3M": 0.0, "GP": 48, "TEAM": "DAL"},
    
    # San Antonio Spurs
    "victor wembanyama": {"PTS": 23.5, "AST": 3.8, "REB": 10.8, "FG3M": 1.8, "GP": 50, "TEAM": "SAS"},
    "devin vassell": {"PTS": 16.5, "AST": 3.5, "REB": 4.2, "FG3M": 2.2, "GP": 45, "TEAM": "SAS"},
    "harrison barnes": {"PTS": 12.5, "AST": 2.5, "REB": 4.5, "FG3M": 1.5, "GP": 50, "TEAM": "SAS"},
    "stephon castle": {"PTS": 10.5, "AST": 3.2, "REB": 3.5, "FG3M": 1.2, "GP": 50, "TEAM": "SAS"},
    "chris paul": {"PTS": 10.2, "AST": 8.5, "REB": 4.2, "FG3M": 1.5, "GP": 48, "TEAM": "SAS"},
    "keldon johnson": {"PTS": 14.5, "AST": 2.8, "REB": 5.5, "FG3M": 1.8, "GP": 50, "TEAM": "SAS"},
    "jeremy sochan": {"PTS": 11.2, "AST": 3.2, "REB": 6.8, "FG3M": 0.8, "GP": 48, "TEAM": "SAS"},
    
    # Oklahoma City Thunder
    "shai gilgeous-alexander": {"PTS": 30.2, "AST": 6.5, "REB": 5.8, "FG3M": 2.2, "GP": 52, "TEAM": "OKC"},
    "jalen williams": {"PTS": 21.5, "AST": 4.8, "REB": 5.5, "FG3M": 1.8, "GP": 50, "TEAM": "OKC"},
    "chet holmgren": {"PTS": 18.5, "AST": 2.5, "REB": 9.2, "FG3M": 1.5, "GP": 48, "TEAM": "OKC"},
    "luguentz dort": {"PTS": 11.5, "AST": 1.8, "REB": 4.2, "FG3M": 2.2, "GP": 50, "TEAM": "OKC"},
    "isaiah joe": {"PTS": 8.5, "AST": 1.5, "REB": 2.5, "FG3M": 2.5, "GP": 50, "TEAM": "OKC"},
    
    # Houston Rockets
    "alperen sengun": {"PTS": 19.5, "AST": 4.8, "REB": 9.5, "FG3M": 0.8, "GP": 50, "TEAM": "HOU"},
    "jalen green": {"PTS": 22.5, "AST": 3.5, "REB": 4.5, "FG3M": 2.8, "GP": 48, "TEAM": "HOU"},
    "fred vanvleet": {"PTS": 14.5, "AST": 7.2, "REB": 3.8, "FG3M": 2.5, "GP": 48, "TEAM": "HOU"},
    "dillon brooks": {"PTS": 12.5, "AST": 2.2, "REB": 3.5, "FG3M": 1.8, "GP": 50, "TEAM": "HOU"},
    "jabari smith jr.": {"PTS": 12.2, "AST": 1.5, "REB": 6.8, "FG3M": 1.8, "GP": 50, "TEAM": "HOU"},
}


def _normalize_name(name):
    """Normalize a player name for fuzzy comparison"""
    name = name.lower().strip()
    # Strip accent characters (ć → c, ä → a, etc.)
    name = unicodedata.normalize('NFD', name)
    name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
    name = name.replace(".", "")
    name = name.replace("'", "'")
    name = re.sub(r'\s+', ' ', name)
    return name


def _fuzzy_lookup(lookup_name, data_dict):
    """Find a key in data_dict matching lookup_name with fuzzy logic"""
    if lookup_name in data_dict:
        return data_dict[lookup_name]

    lower = lookup_name.lower()
    for key, val in data_dict.items():
        if key.lower() == lower:
            return val

    alias = PLAYER_NAME_ALIASES.get(lower)
    if alias:
        for key, val in data_dict.items():
            if key.lower() == alias:
                return val

    norm = _normalize_name(lookup_name)
    for key, val in data_dict.items():
        if _normalize_name(key) == norm:
            return val

    suffixes = ['jr', 'sr', 'ii', 'iii', 'iv']
    for suffix in suffixes:
        if norm.endswith(f' {suffix}'):
            dotted = norm + '.'
            for key, val in data_dict.items():
                if _normalize_name(key) == dotted:
                    return val
        elif norm.endswith(f' {suffix}.'):
            undotted = norm.rstrip('.')
            for key, val in data_dict.items():
                if _normalize_name(key) == undotted:
                    return val

    # Try adding common suffixes (e.g. "Derrick Jones" → "Derrick Jones Jr")
    for suffix in suffixes:
        with_suffix = f'{norm} {suffix}'
        for key, val in data_dict.items():
            if _normalize_name(key) == with_suffix:
                return val

    return None


class NBADataFetcher:
    """Fetches NBA betting data from The Odds API"""

    # Team name → abbreviation mapping for Odds API full names
    TEAM_ABBREV_MAP = {
        'lakers': 'LAL', 'celtics': 'BOS', 'warriors': 'GSW', 'heat': 'MIA',
        'nets': 'BKN', 'bucks': 'MIL', 'clippers': 'LAC', 'suns': 'PHX',
        'knicks': 'NYK', 'bulls': 'CHI', 'nuggets': 'DEN', 'mavericks': 'DAL',
        '76ers': 'PHI', 'grizzlies': 'MEM', 'hawks': 'ATL', 'jazz': 'UTA',
        'pelicans': 'NOP', 'timberwolves': 'MIN', 'pistons': 'DET', 'trail blazers': 'POR',
        'kings': 'SAC', 'pacers': 'IND', 'magic': 'ORL', 'raptors': 'TOR',
        'cavaliers': 'CLE', 'hornets': 'CHA', 'spurs': 'SAS', 'rockets': 'HOU',
        'wizards': 'WAS', 'thunder': 'OKC'
    }

    def __init__(self):
        self.odds_api_key = ODDS_API_KEY
        self.odds_api_base = ODDS_API_BASE_URL
        self.nba_sport_key = NBA_SPORT_KEY

        self.player_team_cache = {}
        self.player_season_stats = {}
        self.team_defense_stats = {}

        if DEBUG_MODE:
            print("✅ Data Fetcher initialized")
            print(f"📡 Using The Odds API for props")

        self._preload_all_player_data()
        self._preload_team_defense_data()

    def _preload_all_player_data(self):
        """Load player stats from nba_api bulk endpoint with cache fallback"""
        cache_file = os.path.join(DATA_DIR, 'nba_player_stats_cache.json')

        # Try loading from cache first (valid for 12 hours)
        cached = self._load_stats_cache(cache_file)
        if cached:
            self.player_season_stats = cached
            for player, stats in self.player_season_stats.items():
                if 'TEAM' in stats:
                    self.player_team_cache[player] = stats['TEAM']
            if DEBUG_MODE:
                print(f"✅ Loaded {len(self.player_season_stats)} players from cache")
            return

        # Try fetching from nba_api
        fetched = self._fetch_bulk_player_stats()
        if fetched:
            self.player_season_stats = fetched
            self._save_stats_cache(cache_file, fetched)
            for player, stats in self.player_season_stats.items():
                if 'TEAM' in stats:
                    self.player_team_cache[player] = stats['TEAM']
            if DEBUG_MODE:
                print(f"✅ Loaded {len(self.player_season_stats)} players from nba_api")
            return

        # Fallback to hardcoded estimates
        if DEBUG_MODE:
            print("⚠️ nba_api unavailable, using fallback estimates")
        self.player_season_stats = FALLBACK_PLAYER_STATS.copy()
        for player, stats in self.player_season_stats.items():
            if 'TEAM' in stats:
                self.player_team_cache[player] = stats['TEAM']
        if DEBUG_MODE:
            print(f"✅ Loaded stats for {len(self.player_season_stats)} players (fallback)")

    def _load_stats_cache(self, cache_file):
        """Load cached player stats if fresh (< 12 hours old)"""
        try:
            if not os.path.exists(cache_file):
                return None
            mod_time = os.path.getmtime(cache_file)
            age_hours = (time.time() - mod_time) / 3600
            if age_hours > 12:
                if DEBUG_MODE:
                    print("📊 Cache expired, will refresh from nba_api")
                return None
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            return None

    def _save_stats_cache(self, cache_file, data):
        """Save player stats to cache file"""
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def _fetch_bulk_player_stats(self):
        """Fetch all player stats from nba_api LeagueDashPlayerStats"""
        try:
            from nba_api.stats.endpoints import LeagueDashPlayerStats
            if DEBUG_MODE:
                print("📊 Fetching bulk player stats from nba_api...")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://www.nba.com/',
                'Accept': 'application/json',
            }

            # Season stats
            season_stats = LeagueDashPlayerStats(
                season='2025-26',
                per_mode_detailed='PerGame',
                headers=headers,
                timeout=60
            )
            rows = season_stats.get_normalized_dict()['LeagueDashPlayerStats']

            # Recent stats (last 10 games)
            recent_stats = LeagueDashPlayerStats(
                season='2025-26',
                per_mode_detailed='PerGame',
                last_n_games=10,
                headers=headers,
                timeout=60
            )
            recent_rows = recent_stats.get_normalized_dict()['LeagueDashPlayerStats']

            # Build recent lookup by player name
            recent_lookup = {}
            for row in recent_rows:
                name = row.get('PLAYER_NAME', '').lower()
                recent_lookup[name] = row

            # Build player stats dict
            player_data = {}
            for row in rows:
                name = row.get('PLAYER_NAME', '').lower()
                team = row.get('TEAM_ABBREVIATION', '')
                gp = row.get('GP', 0)
                if gp < 5:
                    continue

                recent = recent_lookup.get(name, row)
                minutes = row.get('MIN', 0)
                player_data[name] = {
                    'PTS': row.get('PTS', 0),
                    'AST': row.get('AST', 0),
                    'REB': row.get('REB', 0),
                    'FG3M': row.get('FG3M', 0),
                    'GP': gp,
                    'MIN': minutes,
                    'FG_PCT': row.get('FG_PCT', 0),
                    'FG3_PCT': row.get('FG3_PCT', 0),
                    'TEAM': team,
                    'L10_PTS': recent.get('PTS', row.get('PTS', 0)),
                    'L10_AST': recent.get('AST', row.get('AST', 0)),
                    'L10_REB': recent.get('REB', row.get('REB', 0)),
                    'L10_FG3M': recent.get('FG3M', row.get('FG3M', 0)),
                }

            if DEBUG_MODE:
                print(f"✅ Fetched stats for {len(player_data)} players from nba_api")
            return player_data

        except Exception as e:
            if DEBUG_MODE:
                print(f"⚠️ nba_api fetch failed: {e}")
            return None

    def _preload_team_defense_data(self):
        """Load team defensive stats from nba_api with cache fallback"""
        cache_file = os.path.join(DATA_DIR, 'nba_team_defense_cache.json')

        # Try cache first (valid for 12 hours)
        cached = self._load_stats_cache(cache_file)
        if cached:
            self.team_defense_stats = cached
            if DEBUG_MODE:
                print(f"✅ Loaded defense stats for {len(self.team_defense_stats)} teams from cache")
            return

        fetched = self._fetch_team_defense_stats()
        if fetched:
            self.team_defense_stats = fetched
            self._save_stats_cache(cache_file, fetched)
            if DEBUG_MODE:
                print(f"✅ Loaded defense stats for {len(self.team_defense_stats)} teams from nba_api")
            return

        if DEBUG_MODE:
            print("⚠️ Team defense stats unavailable, using league averages")
        self.team_defense_stats = {}

    def _fetch_team_defense_stats(self):
        """Fetch team defensive stats from nba_api"""
        try:
            from nba_api.stats.endpoints import LeagueDashTeamStats
            if DEBUG_MODE:
                print("📊 Fetching team defense stats from nba_api...")

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'Referer': 'https://www.nba.com/',
                'Accept': 'application/json',
            }

            # Base stats (team averages)
            base = LeagueDashTeamStats(
                season='2025-26',
                per_mode_detailed='PerGame',
                headers=headers,
                timeout=60
            )
            base_rows = base.get_normalized_dict()['LeagueDashTeamStats']

            time.sleep(1)  # Rate limit

            # Advanced stats (DEF_RATING, PACE)
            advanced = LeagueDashTeamStats(
                season='2025-26',
                measure_type_detailed_defense='Advanced',
                per_mode_detailed='PerGame',
                headers=headers,
                timeout=60
            )
            adv_rows = advanced.get_normalized_dict()['LeagueDashTeamStats']

            # Build base lookup
            team_data = {}
            for row in base_rows:
                team_name = row.get('TEAM_NAME', '')
                # Convert full name to abbreviation
                abbrev = self.get_team_abbreviation(team_name)
                if abbrev:
                    team_data[abbrev] = {
                        'PTS': row.get('PTS', 110),
                        'AST': row.get('AST', 25),
                        'REB': row.get('REB', 44),
                        'FG3M': row.get('FG3M', 12),
                    }

            # Merge advanced stats
            adv_lookup = {}
            for r in adv_rows:
                team_name = r.get('TEAM_NAME', '')
                abbrev = self.get_team_abbreviation(team_name)
                if abbrev:
                    adv_lookup[abbrev] = r
            
            for abbrev, stats in team_data.items():
                adv = adv_lookup.get(abbrev, {})
                stats['DEF_RATING'] = adv.get('DEF_RATING', 110.0)
                stats['OFF_RATING'] = adv.get('OFF_RATING', 110.0)
                stats['PACE'] = adv.get('PACE', 100.0)
                # Approximate points allowed per game
                stats['PTS_ALLOWED'] = stats['DEF_RATING'] * stats['PACE'] / 100.0

            if DEBUG_MODE:
                print(f"✅ Fetched defense stats for {len(team_data)} teams")
            return team_data

        except Exception as e:
            if DEBUG_MODE:
                print(f"⚠️ Team defense fetch failed: {e}")
            return None

    def get_opponent_defense(self, opponent_abbrev):
        """Get defensive stats for an opponent team"""
        defaults = {'DEF_RATING': 110.0, 'PACE': 100.0, 'PTS_ALLOWED': 110.0,
                     'PTS': 110, 'AST': 25, 'REB': 44, 'FG3M': 12, 'OFF_RATING': 110.0}
        return self.team_defense_stats.get(opponent_abbrev, defaults)

    def get_team_abbreviation(self, full_name):
        """Convert full team name to abbreviation"""
        if not full_name:
            return ''
        lower = full_name.lower()
        for key, abbrev in self.TEAM_ABBREV_MAP.items():
            if key in lower:
                return abbrev
        return full_name[:3].upper()

    def get_todays_games(self):
        """Fetch NBA games for today and next few days from The Odds API"""
        try:
            url = f"{self.odds_api_base}/sports/{self.nba_sport_key}/events"
            params = {'apiKey': self.odds_api_key, 'dateFormat': 'iso'}

            days_ahead = DAYS_AHEAD  # From config
            
            if DEBUG_MODE:
                if days_ahead == 0:
                    print(f"\n📅 Fetching NBA games for today only...")
                else:
                    print(f"\n📅 Fetching NBA games (today + next {days_ahead} days)...")

            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                print(f"❌ API returned status code: {response.status_code}")
                return []

            games = response.json()
            
            if DEBUG_MODE:
                print(f"📊 The Odds API returned {len(games)} total games with betting lines available")
            
            # Get current time in UTC (same as API)
            now_utc = datetime.utcnow()
            today_utc = now_utc.date()
            cutoff_date_utc = today_utc + timedelta(days=days_ahead)
            
            upcoming_games = []

            for game in games:
                commence_time = game.get('commence_time', '')
                if commence_time:
                    try:
                        # Parse ISO time (API gives UTC)
                        game_datetime = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                        
                        # Convert to naive UTC for comparison
                        if game_datetime.tzinfo:
                            game_datetime_utc = game_datetime.utctimetuple()
                            game_date_utc = datetime(*game_datetime_utc[:3]).date()
                        else:
                            game_date_utc = game_datetime.date()
                        
                        # Check if game is within our window (comparing UTC dates)
                        # Also include games from past 24 hours (for games in progress/just finished)
                        yesterday_utc = today_utc - timedelta(days=1)
                        if yesterday_utc <= game_date_utc <= cutoff_date_utc:
                            upcoming_games.append(game)
                    except Exception as e:
                        if DEBUG_MODE:
                            print(f"⚠️ Error parsing game time: {e}")

            if DEBUG_MODE:
                if days_ahead == 0:
                    print(f"✅ Found {len(upcoming_games)} NBA games for today")
                else:
                    print(f"✅ Found {len(upcoming_games)} NBA games (next {days_ahead+1} days)")
                
                # Show why some games might be missing
                if len(upcoming_games) < 3:
                    print(f"💡 Note: The Odds API only shows games with betting lines available.")
                    print(f"   Props are usually posted 4-6 hours before tipoff.")
                    print(f"   Check back closer to game time for more props!")

            return upcoming_games

        except Exception as e:
            print(f"❌ Error fetching games: {str(e)}")
            if DEBUG_MODE:
                import traceback
                traceback.print_exc()
            return []

    def get_player_props_for_event(self, event_id, home_team, away_team, commence_time):
        """Fetch player props for a specific event"""
        try:
            url = f"{self.odds_api_base}/sports/{self.nba_sport_key}/events/{event_id}/odds"
            params = {
                'apiKey': self.odds_api_key,
                'regions': 'us',
                'markets': ','.join(PROP_MARKETS),
                'oddsFormat': 'american',
                'dateFormat': 'iso'
            }

            if DEBUG_MODE:
                print(f"📊 Fetching props for event {event_id}...")

            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                if DEBUG_MODE:
                    print(f"   API returned {response.status_code}")
                return []

            data = response.json()
            all_props = []
            for market_key in PROP_MARKETS:
                props = self._extract_props_from_event(data, market_key)
                all_props.extend(props)

            return all_props

        except Exception as e:
            if DEBUG_MODE:
                print(f"⚠️ Error fetching props: {str(e)}")
            return []

    def _extract_props_from_event(self, event_data, market_key):
        """Extract player props from event data"""
        props = []

        try:
            home_team = event_data.get('home_team', 'Unknown')
            away_team = event_data.get('away_team', 'Unknown')
            commence_time = event_data.get('commence_time', '')

            if commence_time:
                dt_utc = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                # Convert UTC to Eastern Time
                try:
                    from zoneinfo import ZoneInfo
                    dt_et = dt_utc.astimezone(ZoneInfo('America/New_York'))
                except ImportError:
                    # Fallback: manual EST offset (UTC-5)
                    dt_et = dt_utc - timedelta(hours=5)
                game_time_str = dt_et.strftime('%a, %b %d • %I:%M %p ET')
            else:
                game_time_str = 'TBD'

            for bookmaker in event_data.get('bookmakers', []):
                bookmaker_name = bookmaker.get('title', 'Unknown')

                for market in bookmaker.get('markets', []):
                    if market.get('key') != market_key:
                        continue

                    prop_type = self._get_prop_type_from_market(market_key)

                    player_props = {}
                    for outcome in market.get('outcomes', []):
                        player_name = outcome.get('description', '')
                        if not player_name:
                            continue
                        if player_name not in player_props:
                            player_props[player_name] = {}
                        side = outcome.get('name', '')
                        player_props[player_name][side] = {
                            'line': outcome.get('point', 0),
                            'odds': outcome.get('price', -110)
                        }

                    for player_name, sides in player_props.items():
                        player_team = self._get_player_team(player_name)

                        if 'Over' in sides:
                            props.append({
                                'game_id': event_data.get('id', ''),
                                'home_team': home_team,
                                'away_team': away_team,
                                'team': player_team,
                                'start_time': game_time_str,
                                'player_name': player_name,
                                'prop_type': prop_type,
                                'line': sides['Over']['line'],
                                'odds': sides['Over']['odds'],
                                'over_odds': sides['Over']['odds'],
                                'under_odds': sides['Under']['odds'] if 'Under' in sides else -110,
                                'side': 'Over',
                                'bookmaker': bookmaker_name,
                                'market': market_key
                            })

                        if 'Under' in sides:
                            props.append({
                                'game_id': event_data.get('id', ''),
                                'home_team': home_team,
                                'away_team': away_team,
                                'team': player_team,
                                'start_time': game_time_str,
                                'player_name': player_name,
                                'prop_type': prop_type,
                                'line': sides['Under']['line'],
                                'odds': sides['Under']['odds'],
                                'over_odds': sides['Over']['odds'] if 'Over' in sides else -110,
                                'under_odds': sides['Under']['odds'],
                                'side': 'Under',
                                'bookmaker': bookmaker_name,
                                'market': market_key
                            })

        except Exception as e:
            if DEBUG_MODE:
                print(f"⚠️ Error extracting props: {str(e)}")

        return props

    def get_player_props_from_games(self, games):
        """Extract all player props from games"""
        all_props = []

        try:
            for i, game in enumerate(games, 1):
                event_id = game.get('id', '')
                if not event_id:
                    continue

                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')
                commence_time = game.get('commence_time', '')

                if DEBUG_MODE:
                    print(f"\n🎮 Game {i}/{len(games)}: {away_team} @ {home_team}")

                game_props = self.get_player_props_for_event(event_id, home_team, away_team, commence_time)
                all_props.extend(game_props)

                if DEBUG_MODE:
                    print(f"   Found {len(game_props)} props")

            if DEBUG_MODE:
                print(f"\n✅ Total props extracted: {len(all_props)}")

            return all_props

        except Exception as e:
            print(f"❌ Error extracting props: {str(e)}")
            return all_props

    def _get_prop_type_from_market(self, market_key):
        """Map market key to prop type"""
        mapping = {
            'player_points': 'points',
            'player_assists': 'assists',
            'player_rebounds': 'rebounds',
            'player_threes': 'threes'
        }
        return mapping.get(market_key, 'unknown')

    def _get_player_team(self, player_name):
        """Get team abbreviation from cache"""
        result = _fuzzy_lookup(player_name, self.player_team_cache)
        if result:
            self.player_team_cache[player_name] = result
            return result
        return ''

    def get_player_stats(self, player_name, stat_type='PTS'):
        """Get player stats from cache or estimate"""
        season = _fuzzy_lookup(player_name, self.player_season_stats)

        if not season:
            # Estimate for unknown players
            estimates = {'PTS': 12.0, 'AST': 3.0, 'REB': 4.5, 'FG3M': 1.2}
            estimated_value = estimates.get(stat_type, 10.0)

            return {
                'season_avg': round(estimated_value, 1),
                'last_10_avg': round(estimated_value, 1),
                'last_5_avg': round(estimated_value, 1),
                'games_played': 40,
                'minutes': 20.0,
                'fg_pct': 0.44,
                'fg3_pct': 0.35,
                'all_values': []
            }

        season_avg = season.get(stat_type, 0)
        games_played = int(season.get('GP', 50))
        l10_key = f'L10_{stat_type}'
        last_10_avg = season.get(l10_key, season_avg)

        return {
            'season_avg': round(season_avg, 1),
            'last_10_avg': round(last_10_avg, 1),
            'last_5_avg': round(last_10_avg, 1),
            'games_played': games_played,
            'minutes': round(season.get('MIN', 20.0), 1),
            'fg_pct': round(season.get('FG_PCT', 0.44), 3),
            'fg3_pct': round(season.get('FG3_PCT', 0.35), 3),
            'all_values': []
        }

    def format_game_time(self, commence_time_iso):
        """Format ISO commence time string to display format with ET conversion"""
        if not commence_time_iso:
            return 'TBD'
        try:
            dt_utc = datetime.fromisoformat(commence_time_iso.replace('Z', '+00:00'))
            try:
                from zoneinfo import ZoneInfo
                dt_et = dt_utc.astimezone(ZoneInfo('America/New_York'))
            except ImportError:
                dt_et = dt_utc - timedelta(hours=5)
            return dt_et.strftime('%a, %b %d • %I:%M %p ET')
        except Exception:
            return 'TBD'

    def check_api_connection(self):
        """Test if The Odds API connection is working"""
        try:
            url = f"{self.odds_api_base}/sports"
            params = {'apiKey': self.odds_api_key}

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                print("✅ The Odds API connection successful!")
                remaining = response.headers.get('x-requests-remaining', 'Unknown')
                used = response.headers.get('x-requests-used', 'Unknown')
                print(f"📊 API Usage: {used} used, {remaining} remaining")
                return True
            else:
                print(f"❌ API returned status code: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ API connection failed: {str(e)}")
            return False