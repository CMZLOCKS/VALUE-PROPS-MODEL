"""
Diagnostic Script - Check what The Odds API is returning
Run this to see ALL games The Odds API has available right now
"""

import requests
from datetime import datetime

# Your API key
ODDS_API_KEY = '44f324b50f4a7ba9388f08341dd36c72'
ODDS_API_BASE = 'https://api.the-odds-api.com/v4'

print("=" * 70)
print("🔍 ODDS API DIAGNOSTIC TEST")
print("=" * 70)
print()

# Test 1: Get all NBA events
print("📊 Fetching ALL NBA events from The Odds API...")
print()

url = f"{ODDS_API_BASE}/sports/basketball_nba/events"
params = {
    'apiKey': ODDS_API_KEY,
    'dateFormat': 'iso'
}

try:
    response = requests.get(url, params=params, timeout=15)
    
    if response.status_code != 200:
        print(f"❌ Error: API returned status {response.status_code}")
        exit()
    
    games = response.json()
    
    print(f"✅ The Odds API returned {len(games)} total NBA games with odds")
    print()
    print("=" * 70)
    print("GAMES AVAILABLE:")
    print("=" * 70)
    
    today = datetime.now().date()
    
    for i, game in enumerate(games, 1):
        home = game.get('home_team', 'Unknown')
        away = game.get('away_team', 'Unknown')
        commence = game.get('commence_time', '')
        game_id = game.get('id', '')
        
        if commence:
            dt = datetime.fromisoformat(commence.replace('Z', '+00:00'))
            game_date = dt.date()
            game_time = dt.strftime('%I:%M %p ET')
            date_str = dt.strftime('%a, %b %d')
            
            # Mark if today
            today_marker = "📅 TODAY" if game_date == today else f"📆 {date_str}"
        else:
            game_time = "TBD"
            today_marker = "?"
        
        print(f"\n{i}. {away} @ {home}")
        print(f"   {today_marker} • {game_time}")
        print(f"   Game ID: {game_id[:16]}...")
    
    print()
    print("=" * 70)
    
    # Count today's games
    todays_games = []
    for game in games:
        commence = game.get('commence_time', '')
        if commence:
            try:
                dt = datetime.fromisoformat(commence.replace('Z', '+00:00'))
                if dt.date() == today:
                    todays_games.append(game)
            except:
                pass
    
    print(f"\n📊 Summary:")
    print(f"   Total games with odds: {len(games)}")
    print(f"   Games today: {len(todays_games)}")
    print(f"   Games other days: {len(games) - len(todays_games)}")
    
    # Test 2: Check if props are available for today's games
    print()
    print("=" * 70)
    print("🎯 CHECKING PLAYER PROPS AVAILABILITY")
    print("=" * 70)
    
    for i, game in enumerate(todays_games[:3], 1):  # Check first 3 games
        home = game.get('home_team', '')
        away = game.get('away_team', '')
        game_id = game.get('id', '')
        
        print(f"\n{i}. {away} @ {home}")
        
        # Check if this game has props
        props_url = f"{ODDS_API_BASE}/sports/basketball_nba/events/{game_id}/odds"
        props_params = {
            'apiKey': ODDS_API_KEY,
            'regions': 'us',
            'markets': 'player_points,player_assists,player_rebounds,player_threes',
            'oddsFormat': 'american'
        }
        
        try:
            props_response = requests.get(props_url, params=props_params, timeout=15)
            if props_response.status_code == 200:
                props_data = props_response.json()
                bookmakers = props_data.get('bookmakers', [])
                
                total_props = 0
                for bookmaker in bookmakers:
                    for market in bookmaker.get('markets', []):
                        total_props += len(market.get('outcomes', []))
                
                if total_props > 0:
                    print(f"   ✅ HAS PROPS: {total_props} player props available")
                else:
                    print(f"   ⚠️ NO PROPS: Game has no player props yet")
            else:
                print(f"   ❌ ERROR: Couldn't fetch props (status {props_response.status_code})")
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
    
    print()
    print("=" * 70)
    print("✅ DIAGNOSTIC COMPLETE")
    print("=" * 70)
    
    # Check API usage
    remaining = response.headers.get('x-requests-remaining', 'Unknown')
    used = response.headers.get('x-requests-used', 'Unknown')
    print(f"\n📊 API Usage: {used} used, {remaining} remaining")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
