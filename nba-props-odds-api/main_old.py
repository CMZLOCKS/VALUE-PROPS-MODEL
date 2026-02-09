"""
Main Script - NBA Props Model (WITH SAMPLE PROPS)
This version generates sample props when API doesn't provide them
"""

import os
import json
from datetime import datetime
from data_fetcher import NBADataFetcher
from prop_analyzer import PropAnalyzer
from html_generator import HTMLGenerator
from sample_props_generator import generate_sample_props_for_game
from config import *

def create_data_directory():
    """Create the data directory if it doesn't exist"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"✅ Created {DATA_DIR} directory")

def load_performance_data():
    """Load historical performance data"""
    try:
        if os.path.exists(PERFORMANCE_FILE):
            with open(PERFORMANCE_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Could not load performance data: {str(e)}")
    
    return {
        'wins': 361,
        'losses': 322,
        'units': -6.8,
        'roi': -1.0,
        'total_bets': 683
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
    print("🏀 NBA PROPS BETTING MODEL")
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
        print("❌ Cannot connect to API. Check your key in config.py")
        return
    
    print()
    
    # Step 3: Get today's games
    print("📋 Step 3: Fetching today's NBA games...")
    games = data_fetcher.get_todays_games()
    
    if not games:
        print("⚠️ No NBA games found for today.")
        return
    
    print(f"✅ Found {len(games)} NBA games today!")
    print()
    
    # Step 4: Generate props for each game
    print("📋 Step 4: Generating player props...")
    print("💡 Using sample data (API doesn't provide props)")
    print()
    
    all_props = []
    
    for i, fixture in enumerate(games, 1):
        participants = fixture.get('participants', {})
        home_team = participants.get('participant1Name', 'Unknown')
        away_team = participants.get('participant2Name', 'Unknown')
        
        start_time = fixture.get('startTime', 0)
        if isinstance(start_time, int):
            from datetime import datetime
            game_time = datetime.fromtimestamp(start_time).strftime('%a, %b %d • %I:%M %p ET')
        else:
            game_time = 'TBD'
        
        print(f"\n🎮 Game {i}/{len(games)}: {away_team} @ {home_team}")
        
        # Generate sample props for this game
        game_props = generate_sample_props_for_game(home_team, away_team, game_time)
        
        print(f"   ✅ Generated {len(game_props)} sample props")
        
        # Analyze each prop
        for prop in game_props:
            player_info = {
                'name': prop['player_name'],
                'team': home_team if prop['player_name'] else away_team,
                'opponent': away_team if prop['player_name'] else home_team,
                'game_time': game_time
            }
            
            # Create stats based on the line
            betting_line = prop['line']
            player_stats = {
                'season_avg': betting_line,
                'last_10_avg': betting_line + 1.5,  # Slightly trending up
                'last_5_avg': betting_line + 2.0,
                'games_played': 50,
                'all_values': [betting_line] * 10
            }
            
            # Analyze the prop
            prop_analysis = analyzer.analyze_prop(
                player_info=player_info,
                player_stats=player_stats,
                prop_type=prop['prop_type'],
                betting_line=betting_line,
                odds=prop['odds']
            )
            
            if prop_analysis:
                prop_analysis['bookmaker'] = prop['bookmaker']
                all_props.append(prop_analysis)
    
    print(f"\n✅ Total props analyzed: {len(all_props)}")
    
    # Filter for value plays only to keep dashboard clean
    value_props = [p for p in all_props if p.get('ai_score', 0) >= MIN_AI_SCORE_THRESHOLD]
    print(f"💎 Value plays (AI Score >= {MIN_AI_SCORE_THRESHOLD}): {len(value_props)}")
    
    print()
    
    # Step 5: Generate HTML dashboard
    print("📋 Step 5: Generating dashboard...")
    
    performance_data = load_performance_data()
    
    # Use value props for cleaner dashboard, or all props if no value plays
    display_props = value_props if value_props else all_props[:50]  # Limit to 50 if showing all
    
    html_content = html_gen.generate_dashboard(display_props, performance_data)
    html_gen.save_html(html_content)
    
    print()
    
    # Step 6: Save data
    print("📋 Step 6: Saving data...")
    save_props_history(all_props)
    
    print()
    
    # Step 7: Summary
    print("=" * 60)
    print("✅ MODEL RUN COMPLETE!")
    print("=" * 60)
    
    print(f"\n📊 Summary:")
    print(f"   NBA Games Today: {len(games)}")
    print(f"   Total Props Generated: {len(all_props)}")
    print(f"   Value Plays Found: {len(value_props)}")
    print(f"   Min AI Score: {MIN_AI_SCORE_THRESHOLD}")
    print(f"\n📂 Dashboard saved to: {OUTPUT_HTML}")
    print(f"\n💡 Next Steps:")
    print(f"   1. Open {OUTPUT_HTML} in your web browser")
    print(f"   2. Review the value plays")
    print(f"   3. NOTE: These are sample props for demonstration")
    print(f"   4. To get real predictions, add a stats API (API-NBA)")
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
