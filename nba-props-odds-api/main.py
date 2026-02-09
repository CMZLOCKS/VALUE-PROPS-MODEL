"""
Main Script - NBA Props Model (The Odds API Version)
Run this file to generate prop predictions with REAL data!
"""

import os
import sys
import json
from datetime import datetime, timedelta
from data_fetcher import NBADataFetcher
from prop_analyzer import PropAnalyzer
from html_generator import HTMLGenerator
from prop_tracker import (
    track_new_picks,
    load_tracking_data,
    grade_pending_picks,
    backfill_profit_loss,
    merge_and_save_performance,
    _prop_type_key,
)
from config import *

# Set console encoding to UTF-8 for emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def create_data_directory():
    """Create the data directory if it doesn't exist"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"✅ Created {DATA_DIR} directory")

def load_performance_data():
    """Load historical performance data (overall + daily and daily_by_type for today/yesterday)"""
    try:
        if os.path.exists(PERFORMANCE_FILE):
            with open(PERFORMANCE_FILE, 'r') as f:
                data = json.load(f)
            # Ensure daily and daily_by_type exist for Daily Performance section
            data.setdefault('daily', {})
            data.setdefault('daily_by_type', {})
            return data
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Could not load performance data: {str(e)}")
    
    return {
        'wins': 0,
        'losses': 0,
        'units': 0.0,
        'roi': 0.0,
        'total_bets': 0,
        'daily': {},
        'daily_by_type': {}
    }

def save_performance_data(performance_data):
    """Save performance data to file"""
    try:
        with open(PERFORMANCE_FILE, 'w') as f:
            json.dump(performance_data, f, indent=2)
        if DEBUG_MODE:
            print("✅ Performance data saved")
    except Exception as e:
        print(f"❌ Error saving performance data: {str(e)}")

def save_props_history(props):
    """Save today's props to history file"""
    try:
        history = {}
        if os.path.exists(PROPS_HISTORY_FILE):
            with open(PROPS_HISTORY_FILE, 'r') as f:
                history = json.load(f)
        
        today = datetime.now().strftime('%Y-%m-%d')
        history[today] = {
            'date': today,
            'total_props': len(props),
            'value_plays': len([p for p in props if p.get('is_value_play')]),
            'props': props
        }
        
        with open(PROPS_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        
        if DEBUG_MODE:
            print("✅ Props history saved")
            
    except Exception as e:
        print(f"❌ Error saving props history: {str(e)}")

def main():
    """Main function that runs the entire model"""
    print("=" * 60)
    print("🏀 NBA PROPS BETTING MODEL - THE ODDS API VERSION")
    print("=" * 60)
    print()
    
    # Step 1: Setup
    print("📋 Step 1: Setting up...")
    create_data_directory()
    
    data_fetcher = NBADataFetcher()
    analyzer = PropAnalyzer()
    html_gen = HTMLGenerator()
    
    print()
    
    # Step 2: Check API connection
    print("📋 Step 2: Checking API connection...")
    if not data_fetcher.check_api_connection():
        print("❌ Cannot connect to The Odds API. Check your key in config.py")
        return
    
    print()
    
    # Step 3: Get today's games with odds
    print("📋 Step 3: Fetching NBA games and player props...")
    games = data_fetcher.get_todays_games()
    
    if not games:
        print("⚠️ No NBA games found for today.")
        print("💡 This could mean:")
        print("   - No NBA games scheduled today")
        print("   - Games don't have player props available yet")
        return
    
    print(f"✅ Found {len(games)} NBA games!")
    print()
    
    # Step 4: Extract all player props
    print("📋 Step 4: Extracting player props from games...")
    all_props_raw = data_fetcher.get_player_props_from_games(games)
    
    if not all_props_raw:
        print("⚠️ No player props found in games")
        print("💡 Props might not be available yet (usually posted ~4 hours before game)")
        return
    
    print(f"✅ Found {len(all_props_raw)} total props from sportsbooks!")
    print()
    
    # Step 5: Analyze each prop with player stats (both Over AND Under)
    print("📋 Step 5: Analyzing props with player statistics...")
    analyzed_props = []

    # Group props by player + prop type + bookmaker + line (deduplicate)
    # We want one entry per unique (player, market, bookmaker, line) to analyze both sides
    unique_props = {}
    for prop in all_props_raw:
        key = f"{prop['player_name']}_{prop['market']}_{prop['bookmaker']}_{prop['line']}"
        if key not in unique_props:
            unique_props[key] = prop

    print(f"📊 Analyzing {len(unique_props)} unique player/prop combinations (Over + Under)...")

    for i, (key, prop) in enumerate(unique_props.items(), 1):
        if i % 50 == 0:
            print(f"   Processed {i}/{len(unique_props)}...")

        player_name = prop['player_name']
        prop_type = prop['prop_type']

        # Get stat key for this prop type
        stat_key = PROP_TYPES.get(prop['market'], {}).get('stat_key', 'PTS')

        # Get player stats (instant from bulk cache — no API call)
        player_stats = data_fetcher.get_player_stats(player_name, stat_key)

        # Only analyze if we have enough games
        if player_stats['games_played'] < MIN_GAMES_PLAYED:
            continue

        # Determine player's team and opponent
        player_team = prop.get('team', '')
        home_team = prop.get('home_team', '')
        away_team = prop.get('away_team', '')
        start_time = prop.get('start_time', 'TBD')

        # ALWAYS find the correct game for this player
        player_abbrev = data_fetcher.get_team_abbreviation(player_team) if player_team else ''
        
        # Find the game this player is actually in
        correct_game = None
        for g in games:
            gh = data_fetcher.get_team_abbreviation(g.get('home_team', ''))
            ga = data_fetcher.get_team_abbreviation(g.get('away_team', ''))
            if player_abbrev and player_abbrev in (gh, ga):
                correct_game = g
                break
        
        # Use the correct game info
        game_date = None
        if correct_game:
            home_team = correct_game.get('home_team', '')
            away_team = correct_game.get('away_team', '')
            commence_time = correct_game.get('commence_time', '')
            start_time = data_fetcher.format_game_time(commence_time)
            # Game date (ET) for tracking/grading
            try:
                dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                try:
                    from zoneinfo import ZoneInfo
                    dt_et = dt.astimezone(ZoneInfo('America/New_York'))
                except ImportError:
                    dt_et = dt - timedelta(hours=5)
                game_date = dt_et.strftime('%Y-%m-%d')
            except Exception:
                game_date = datetime.now().strftime('%Y-%m-%d')
            
            # Determine opponent
            home_abbrev = data_fetcher.get_team_abbreviation(home_team)
            away_abbrev = data_fetcher.get_team_abbreviation(away_team)
            
            if player_abbrev == home_abbrev:
                opponent = away_team
                # Ensure player_team is set correctly
                if not player_team or player_team == '':
                    player_team = home_team
            elif player_abbrev == away_abbrev:
                opponent = home_team
                # Ensure player_team is set correctly
                if not player_team or player_team == '':
                    player_team = away_team
            else:
                # Fallback
                opponent = away_team if home_team == player_team else home_team
        else:
            # No game found - use original data
            home_abbrev_check = data_fetcher.get_team_abbreviation(home_team)
            away_abbrev_check = data_fetcher.get_team_abbreviation(away_team)
            
            if player_abbrev == home_abbrev_check:
                opponent = away_team
            elif player_abbrev == away_abbrev_check:
                opponent = home_team
            else:
                opponent = away_team

        # Get opponent defense stats
        opponent_abbrev = data_fetcher.get_team_abbreviation(opponent)
        opponent_defense = data_fetcher.get_opponent_defense(opponent_abbrev)

        player_info = {
            'name': player_name,
            'team': player_team,
            'opponent': opponent,
            'game_time': start_time
        }

        betting_line = prop['line']
        over_odds = prop.get('over_odds', prop['odds'])
        under_odds = prop.get('under_odds', -110)

        # === Analyze OVER ===
        over_analysis = analyzer.analyze_prop(
            player_info=player_info,
            player_stats=player_stats,
            prop_type=prop_type,
            betting_line=betting_line,
            odds=over_odds,
            side='Over',
            opponent_defense=opponent_defense
        )
        if over_analysis:
            over_analysis['bookmaker'] = prop['bookmaker']
            over_analysis['side'] = 'Over'
            over_analysis['home_team'] = home_team
            over_analysis['away_team'] = away_team
            over_analysis['team'] = player_team
            over_analysis['start_time'] = start_time
            over_analysis['game_date'] = game_date or datetime.now().strftime('%Y-%m-%d')
            analyzed_props.append(over_analysis)

        # === Analyze UNDER ===
        under_analysis = analyzer.analyze_prop(
            player_info=player_info,
            player_stats=player_stats,
            prop_type=prop_type,
            betting_line=betting_line,
            odds=under_odds,
            side='Under',
            opponent_defense=opponent_defense
        )
        if under_analysis:
            under_analysis['bookmaker'] = prop['bookmaker']
            under_analysis['side'] = 'Under'
            under_analysis['home_team'] = home_team
            under_analysis['away_team'] = away_team
            under_analysis['team'] = player_team
            under_analysis['start_time'] = start_time
            under_analysis['game_date'] = game_date or datetime.now().strftime('%Y-%m-%d')
            analyzed_props.append(under_analysis)

    print(f"\n✅ Successfully analyzed {len(analyzed_props)} props (Over + Under)")
    
    # Filter for value plays using per-prop-type thresholds
    value_props = []
    for p in analyzed_props:
        prop_lower = p.get('prop_type', 'points').lower()
        min_score = MIN_AI_SCORE_BY_TYPE.get(prop_lower, MIN_AI_SCORE_THRESHOLD)
        if p.get('ai_score', 0) >= min_score:
            value_props.append(p)
    print(f"💎 Found {len(value_props)} value plays (per-type thresholds: PTS/AST/REB=10, 3PT=7.5)")
    
    # Build sharp display: min ~25 props, top by AI score per type (points, assists, rebounds, threes)
    display_props = html_gen._select_sharp_display_props(value_props, analyzed_props)
    if not display_props:
        display_props = value_props if value_props else sorted(analyzed_props, key=lambda x: x.get('ai_score', 0), reverse=True)[:50]
    print(f"📊 Sharp display: {len(display_props)} props (min 25, balanced across PTS/AST/REB/3PT)")
    
    print()
    
    # Step 6: Tracking — track new picks, grade pending, update performance.json
    print("📋 Step 6: Tracking & grading picks...")
    deduplicated = html_gen._deduplicate_props(display_props)
    sorted_props = sorted(deduplicated, key=lambda x: x.get('ai_score', 0), reverse=True)
    top_plays = html_gen._select_diverse_top_plays(sorted_props, TOP_PLAYS_COUNT)
    top_play_keys = {
        (p.get('player_name', ''), _prop_type_key(p), p.get('betting_line', 0), p.get('side', ''))
        for p in top_plays
    }
    track_new_picks(value_props, top_play_keys, data_fetcher)
    tracking = load_tracking_data()
    grade_pending_picks(tracking, data_fetcher)
    backfill_profit_loss(tracking)
    merge_and_save_performance(tracking)
    
    performance_data = load_performance_data()
    
    html_content = html_gen.generate_dashboard(display_props, performance_data)
    html_gen.save_html(html_content)
    
    print()
    
    # Step 7: Save data
    print("📋 Step 7: Saving data...")
    save_props_history(analyzed_props)
    
    print()
    
    # Step 8: Summary
    print("=" * 60)
    print("✅ MODEL RUN COMPLETE!")
    print("=" * 60)
    
    print(f"\n📊 Summary:")
    print(f"   NBA Games: {len(games)}")
    print(f"   Total Props Analyzed: {len(analyzed_props)}")
    print(f"   Value Plays Found: {len(value_props)}")
    print(f"   Min AI Score: {MIN_AI_SCORE_THRESHOLD}")
    print(f"\n📂 Dashboard saved to: {OUTPUT_HTML}")
    print(f"\n💡 Next Steps:")
    print(f"   1. Open {OUTPUT_HTML} in your web browser")
    print(f"   2. Review the value plays and AI analysis")
    print(f"   3. Compare lines across different sportsbooks")
    print(f"   4. Make informed betting decisions!")
    print()
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Model run interrupted by user")
    except Exception as e:
        print(f"\n\n❌ An error occurred: {str(e)}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()

