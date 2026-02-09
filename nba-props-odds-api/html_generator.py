"""
HTML Generator for NBA Props Model - Modern Gradient Design
"""

import base64
from datetime import datetime, timedelta
from config import *

class HTMLGenerator:
    """Generates beautiful HTML dashboard for NBA props"""
    
    def __init__(self):
        """Initialize the HTML generator"""
        if DEBUG_MODE:
            print("✅ HTML Generator initialized")
    
    def _get_background_base64(self):
        """Get base64 encoded background image"""
        try:
            with open('abstract_background.jpg', 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except:
            # Fallback to empty string if image not found
            return ""
    
    def _get_team_emoji(self, team_name):
        """Get emoji for team"""
        team_emojis = {
            'lakers': '🟣', 'celtics': '🍀', 'warriors': '🌉', 'heat': '🔥',
            'nets': '⚫', 'bucks': '🦌', 'clippers': '⛵', 'suns': '☀️',
            'knicks': '🗽', 'bulls': '🐂', 'nuggets': '⛰️', 'mavs': '🐴',
            '76ers': '🔔', 'grizzlies': '🐻', 'hawks': '🦅', 'jazz': '🎵',
            'pelicans': '🐦', 'timberwolves': '🐺', 'pistons': '🔧', 'trail blazers': '🌲',
            'kings': '👑', 'pacers': '🏎️', 'magic': '✨', 'raptors': '🦖',
            'cavaliers': '⚔️', 'hornets': '🐝', 'spurs': '🤠', 'rockets': '🚀',
            'wizards': '🧙', 'thunder': '⚡'
        }
        
        team_lower = team_name.lower()
        for key, emoji in team_emojis.items():
            if key in team_lower:
                return emoji
        return '🏀'
    
    def _get_team_abbreviation(self, team_name):
        """Get team abbreviation from full name"""
        team_abbrevs = {
            'lakers': 'LAL', 'celtics': 'BOS', 'warriors': 'GSW', 'heat': 'MIA',
            'nets': 'BKN', 'bucks': 'MIL', 'clippers': 'LAC', 'suns': 'PHX',
            'knicks': 'NYK', 'bulls': 'CHI', 'nuggets': 'DEN', 'mavericks': 'DAL',
            '76ers': 'PHI', 'grizzlies': 'MEM', 'hawks': 'ATL', 'jazz': 'UTA',
            'pelicans': 'NOP', 'timberwolves': 'MIN', 'pistons': 'DET', 'trail blazers': 'POR',
            'kings': 'SAC', 'pacers': 'IND', 'magic': 'ORL', 'raptors': 'TOR',
            'cavaliers': 'CLE', 'hornets': 'CHA', 'spurs': 'SAS', 'rockets': 'HOU',
            'wizards': 'WAS', 'thunder': 'OKC'
        }

        team_lower = team_name.lower()
        for key, abbrev in team_abbrevs.items():
            if key in team_lower:
                return abbrev
        return team_name[:3].upper()

    def _get_team_logo_url(self, team_abbrev):
        """Get NBA team logo URL from CDN"""
        team_ids = {
            'LAL': '1610612747', 'BOS': '1610612738', 'GSW': '1610612744', 'MIA': '1610612748',
            'BKN': '1610612751', 'MIL': '1610612749', 'LAC': '1610612746', 'PHX': '1610612756',
            'NYK': '1610612752', 'CHI': '1610612741', 'DEN': '1610612743', 'DAL': '1610612742',
            'PHI': '1610612755', 'MEM': '1610612763', 'ATL': '1610612737', 'UTA': '1610612762',
            'NOP': '1610612740', 'MIN': '1610612750', 'DET': '1610612765', 'POR': '1610612757',
            'SAC': '1610612758', 'IND': '1610612754', 'ORL': '1610612753', 'TOR': '1610612761',
            'CLE': '1610612739', 'CHA': '1610612766', 'SAS': '1610612759', 'HOU': '1610612745',
            'WAS': '1610612764', 'OKC': '1610612760'
        }

        team_id = team_ids.get(team_abbrev, '1610612743')  # Default to DEN
        return f"https://cdn.nba.com/logos/nba/{team_id}/primary/L/logo.svg"

    def _convert_to_pst(self, game_time_str):
        """Keep game time in EST format"""
        try:
            if 'ET' in game_time_str:
                return game_time_str.replace(' ET', ' EST')
            return game_time_str
        except:
            return game_time_str

    def _generate_prop_card(self, prop, is_top_play=False):
        """Generate HTML for a single prop card"""
        player_name = prop.get('player_name', 'Unknown')
        away_team = prop.get('away_team', '')
        home_team = prop.get('home_team', '')
        player_team = prop.get('team', '')  # Player's actual team from data

        # Get team abbreviations
        away_abbrev = self._get_team_abbreviation(away_team) if away_team else ''
        home_abbrev = self._get_team_abbreviation(home_team) if home_team else ''
        player_team_abbrev = self._get_team_abbreviation(player_team) if player_team else ''

        # Determine which team the player is actually on
        # Priority: 1) player_team from data, 2) match with away, 3) match with home
        if not player_team_abbrev:
            # Try to match player team with game teams
            if away_abbrev:
                player_team_abbrev = away_abbrev
            elif home_abbrev:
                player_team_abbrev = home_abbrev
            else:
                player_team_abbrev = 'NBA'

        # Determine opponent
        if player_team_abbrev == away_abbrev:
            opponent_abbrev = home_abbrev
            game = f"{away_abbrev} @ {home_abbrev}"
        elif player_team_abbrev == home_abbrev:
            opponent_abbrev = away_abbrev
            game = f"{home_abbrev} vs {away_abbrev}"
        else:
            # Player's cached team doesn't match game teams
            # Show player's actual team vs the other teams
            if away_abbrev and home_abbrev:
                opponent_abbrev = home_abbrev
                game = f"{player_team_abbrev} vs {away_abbrev}/{home_abbrev}"
            else:
                opponent_abbrev = ''
                game = f"{player_team_abbrev}"

        # Get and format game time
        game_time = prop.get('start_time', 'TBD')
        game_time_pst = self._convert_to_pst(game_time)

        prop_type = prop.get('prop_type', 'points').lower()
        prop_type_display = prop_type.title()
        line = prop.get('betting_line', 0)
        odds = prop.get('odds', -110)
        side = prop.get('side', 'Over')  # Get the side (Over or Under)

        prediction = prop.get('prediction', 0)
        edge = prop.get('edge', 0)

        season_avg = prop.get('season_avg', 0)
        last_10 = prop.get('last_10_avg', 0)

        ai_score = prop.get('ai_score', 0)
        ev = prop.get('ev', 0)
        win_prob = prop.get('win_probability', 0)

        insights = prop.get('insights', [])

        # Set class based on side
        side_class = 'over-text' if side == 'Over' else 'under-text'
        side_lower = side.lower()  # For bet-line CSS class

        # Get team logo URL - USE PLAYER'S TEAM, NOT GAME LOCATION
        team_logo_url = self._get_team_logo_url(player_team_abbrev)

        # Format odds
        odds_str = f"+{odds}" if odds > 0 else str(odds)

        # Map prop types to data attributes for filtering
        prop_type_map = {
            'points': 'points',
            'assists': 'assists',
            'rebounds': 'rebounds',
            'threes': 'threes',
            '3pt': 'threes',
            'three_pointers': 'threes'
        }
        data_prop_type = prop_type_map.get(prop_type, 'points')

        top_play_attr = ' data-top-play="true"' if is_top_play else ''

        card_html = f"""
        <div class="prop-card {side_lower}-glow" data-prop-type="{data_prop_type}"{top_play_attr}>
            <div class="player-header">
                <div class="team-logo">
                    <img src="{team_logo_url}" alt="{player_team_abbrev}" onerror="this.parentElement.innerHTML='🏀'">
                </div>
                <div class="player-info">
                    <h3>{player_name}</h3>
                    <div class="game-info">{game} • {game_time_pst}</div>
                </div>
            </div>

            <div class="bet-line {side_lower}">
                <div class="bet-type {side_lower}-text">{side.upper()} {line} {prop_type_display.upper()}</div>
                <div class="bet-details">Last 10 Avg: {last_10:.1f}</div>
            </div>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-label">Season Avg</div>
                    <div class="stat-value">{season_avg:.1f}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Last 10 Avg</div>
                    <div class="stat-value {'positive' if last_10 > line else 'negative'}">{last_10:.1f}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">AI Score</div>
                    <div class="stat-value positive">{ai_score:.1f}</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">EV</div>
                    <div class="stat-value {'positive' if ev > 0 else 'negative'}">+{ev:.1f}%</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Win %</div>
                    <div class="stat-value">{win_prob:.0f}%</div>
                </div>
                <div class="stat-box">
                    <div class="stat-label">Edge</div>
                    <div class="stat-value positive">+{edge:.1f}</div>
                </div>
            </div>
            
            <div class="insights">
"""
        
        # Add insights
        for insight in insights[:4]:  # Max 4 insights
            tag_class = 'positive' if any(word in insight.lower() for word in ['edge', 'avg', 'high']) else ''
            card_html += f'<div class="insight-tag {tag_class}">{insight}</div>\n'
        
        card_html += """
            </div>
        </div>
"""
        return card_html
    
    def _deduplicate_props(self, props):
        """
        Remove duplicate props - keep only the best side (Over OR Under) for each player/prop combo
        
        For example, if we have:
        - LeBron James OVER 25.5 Points (AI: 8.5)
        - LeBron James UNDER 25.5 Points (AI: 7.2)
        
        We keep only the OVER (higher AI score)
        """
        # Group props by player + prop_type + line
        prop_groups = {}
        
        for prop in props:
            player = prop.get('player_name', '')
            prop_type = prop.get('prop_type', '').lower()
            line = prop.get('betting_line', 0)
            
            # Create unique key for this player/prop/line combo
            key = f"{player}_{prop_type}_{line}"
            
            # If we haven't seen this combo, or this one has a higher AI score, keep it
            if key not in prop_groups:
                prop_groups[key] = prop
            else:
                # Keep the one with higher AI score
                current_score = prop_groups[key].get('ai_score', 0)
                new_score = prop.get('ai_score', 0)
                if new_score > current_score:
                    prop_groups[key] = prop
        
        # Return deduplicated list
        return list(prop_groups.values())
    
    def _select_diverse_top_plays(self, sorted_props, count=6):
        """
        Select top plays ensuring diversity across prop types (Points, Assists, Rebounds, 3-Pointers)
        
        Strategy:
        1. Try to get at least 1 of each prop type in top 6
        2. Prioritize highest AI scores
        3. Mix of Over and Under bets
        """
        if len(sorted_props) <= count:
            return sorted_props
        
        prop_types = ['points', 'assists', 'rebounds', 'threes']
        selected = []
        used_types = set()
        
        # Phase 1: Get best play of each type (up to 4 plays)
        for prop in sorted_props:
            if len(selected) >= count:
                break
            
            prop_type = prop.get('prop_type', 'points').lower()
            
            # Normalize prop type names
            if '3-point' in prop_type or 'three' in prop_type:
                prop_type = 'threes'
            
            # Add if we don't have this type yet
            if prop_type in prop_types and prop_type not in used_types:
                selected.append(prop)
                used_types.add(prop_type)
        
        # Phase 2: Fill remaining spots with highest AI scores (any type)
        for prop in sorted_props:
            if len(selected) >= count:
                break
            
            # Skip if already selected
            if prop in selected:
                continue
            
            # Add highest scoring remaining props
            selected.append(prop)
        
        # Sort by AI score to maintain quality order
        selected.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
        
        return selected[:count]

    def _select_sharp_display_props(self, value_props, analyzed_props):
        """
        Select the sharpest props for display: at least TARGET_MIN_DISPLAY (~25),
        with minimum MIN_DISPLAY_PER_TYPE from each of points, assists, rebounds, threes.
        Takes top by AI score per category so we get the best edges from each type.
        """
        target = TARGET_MIN_DISPLAY
        per_type = MIN_DISPLAY_PER_TYPE
        # Build candidate pool: start with value plays; if fewer than target, add next best from analyzed
        pool = list(value_props) if value_props else []
        if len(pool) < target and analyzed_props:
            remaining = [p for p in analyzed_props if p not in pool]
            remaining.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
            for p in remaining:
                pool.append(p)
                if len(pool) >= target:
                    break
        if not pool:
            return []
        # Group by prop type (points, assists, rebounds, threes)
        by_type = {'points': [], 'assists': [], 'rebounds': [], 'threes': []}
        for p in pool:
            key = self._get_prop_data_type(p)
            if key in by_type:
                by_type[key].append(p)
        # Take top N per type by AI score (sharpest first)
        selected = []
        for key in ('points', 'assists', 'rebounds', 'threes'):
            by_type[key].sort(key=lambda x: x.get('ai_score', 0), reverse=True)
            selected.extend(by_type[key][:per_type])
        # Dedupe by identity (same prop object might appear if we didn't dedupe pool)
        seen_ids = set()
        unique = []
        for p in selected:
            pid = (p.get('player_name'), p.get('prop_type'), p.get('betting_line'), p.get('side'))
            if pid not in seen_ids:
                seen_ids.add(pid)
                unique.append(p)
        # If still under target, add next best from pool (any type) by AI score
        if len(unique) < target:
            pool_sorted = sorted(pool, key=lambda x: x.get('ai_score', 0), reverse=True)
            for p in pool_sorted:
                if len(unique) >= target:
                    break
                pid = (p.get('player_name'), p.get('prop_type'), p.get('betting_line'), p.get('side'))
                if pid not in seen_ids:
                    seen_ids.add(pid)
                    unique.append(p)
        return unique
    
    def _generate_tracker_section(self, props, prop_type_key, prop_type_label):
        """Generate prop tracker section for a specific prop type tab"""
        # Filter props for this type
        filtered = [p for p in props if self._get_prop_data_type(p) == prop_type_key]

        if not filtered:
            return ""

        today = datetime.now().strftime('%Y-%m-%d')

        html = f"""
        <div class="prop-tracker" data-tracker-type="{prop_type_key}">
            <div class="tracker-header">
                <h3>📋 PROP TRACKER — {prop_type_label.upper()}</h3>
                <div class="tracker-summary">
                    <span class="tracker-hits" id="hits-{prop_type_key}">✅ 0 Hits</span>
                    <span class="tracker-misses" id="misses-{prop_type_key}">❌ 0 Misses</span>
                    <span class="tracker-pending-count" id="pending-{prop_type_key}">⏳ {len(filtered)} Pending</span>
                </div>
            </div>
            <div class="tracker-list">
"""

        for i, prop in enumerate(filtered):
            player_name = prop.get('player_name', 'Unknown')
            side = prop.get('side', 'Over')
            line = prop.get('betting_line', 0)
            prop_display = prop.get('prop_type', 'points').title()
            side_class = 'over-text' if side == 'Over' else 'under-text'
            tracker_id = f"{prop_type_key}_{i}_{today}"

            html += f"""
                <div class="tracker-row" data-tracker-id="{tracker_id}">
                    <div class="tracker-player">{player_name}</div>
                    <div class="tracker-line {side_class}">{side.upper()} {line} {prop_display.upper()}</div>
                    <div class="tracker-buttons">
                        <button class="tracker-btn hit-btn" onclick="markResult('{tracker_id}', 'hit', '{prop_type_key}')">✅ Hit</button>
                        <button class="tracker-btn miss-btn" onclick="markResult('{tracker_id}', 'miss', '{prop_type_key}')">❌ Miss</button>
                        <button class="tracker-btn push-btn" onclick="markResult('{tracker_id}', 'push', '{prop_type_key}')">➖ Push</button>
                    </div>
                    <div class="tracker-result" id="result-{tracker_id}"></div>
                </div>
"""

        html += """
            </div>
        </div>
"""
        return html

    def _get_prop_data_type(self, prop):
        """Get the data-prop-type value for a prop"""
        prop_type = prop.get('prop_type', 'points').lower()
        prop_type_map = {
            'points': 'points',
            'assists': 'assists',
            'rebounds': 'rebounds',
            'threes': 'threes',
            '3pt': 'threes',
            'three_pointers': 'threes',
            '3-pointers': 'threes',
        }
        return prop_type_map.get(prop_type, 'points')

    def _generate_performance_section(self, performance_data, total_props, value_props, win_rate):
        """Generate performance statistics section"""
        wins = performance_data.get('wins', 0)
        losses = performance_data.get('losses', 0)
        units = performance_data.get('units', 0)
        roi = performance_data.get('roi', 0)
        
        return f"""
        <div class="performance-card">
            <h3>Overall Stats</h3>
            <div class="perf-stat">
                <span class="perf-label">Total Props Analyzed</span>
                <span class="perf-value">{total_props}</span>
            </div>
            <div class="perf-stat">
                <span class="perf-label">Value Plays</span>
                <span class="perf-value">{value_props}</span>
            </div>
            <div class="perf-stat">
                <span class="perf-label">Win Rate</span>
                <span class="perf-value">{win_rate:.1f}%</span>
            </div>
        </div>
        
        <div class="performance-card">
            <h3>Season Record</h3>
            <div class="perf-stat">
                <span class="perf-label">Wins</span>
                <span class="perf-value">{wins}</span>
            </div>
            <div class="perf-stat">
                <span class="perf-label">Losses</span>
                <span class="perf-value">{losses}</span>
            </div>
            <div class="perf-stat">
                <span class="perf-label">Units</span>
                <span class="perf-value">{units:+.1f}u</span>
            </div>
        </div>
        
        <div class="performance-card">
            <h3>ROI & Value</h3>
            <div class="perf-stat">
                <span class="perf-label">ROI</span>
                <span class="perf-value">{roi:+.1f}%</span>
            </div>
            <div class="perf-stat">
                <span class="perf-label">Min AI Score</span>
                <span class="perf-value">{MIN_AI_SCORE_THRESHOLD}</span>
            </div>
            <div class="perf-stat">
                <span class="perf-label">Updated</span>
                <span class="perf-value">Live</span>
            </div>
        </div>
"""

    def _get_daily_stats(self, performance_data, date_str):
        """Get overall daily stats for a date. Returns wins, losses, units, roi."""
        daily = performance_data.get('daily', {}) or {}
        d = daily.get(date_str, {})
        wins = d.get('wins', 0)
        losses = d.get('losses', 0)
        pushes = d.get('pushes', 0)
        units = d.get('units', 0.0)
        roi = d.get('roi', 0.0)
        total = wins + losses + pushes
        if total > 0 and roi == 0 and units != 0:
            roi = (units / (wins + losses)) * 100 if (wins + losses) > 0 else 0.0
        return wins, losses, units, roi

    def _get_daily_stats_by_type(self, performance_data, date_str, type_key):
        """Get daily stats for a date and prop type (top6, points, assists, rebounds, threes)."""
        by_type = performance_data.get('daily_by_type', {}) or {}
        day_data = by_type.get(date_str, {}) or {}
        d = day_data.get(type_key, {})
        wins = d.get('wins', 0)
        losses = d.get('losses', 0)
        pushes = d.get('pushes', 0)
        units = d.get('units', 0.0)
        roi = d.get('roi', 0.0)
        total = wins + losses + pushes
        if total > 0 and roi == 0 and units != 0:
            roi = (units / (wins + losses)) * 100 if (wins + losses) > 0 else 0.0
        return wins, losses, units, roi

    def _format_daily_box(self, label, wins, losses, units, roi):
        """Format a single daily box (TODAY or YESTERDAY) with W-L, units, ROI%."""
        roi_class = 'positive' if roi > 0 else ('negative' if roi < 0 else '')
        units_class = 'positive' if units > 0 else ('negative' if units < 0 else '')
        return f"""
            <div class="daily-day-box">
                <div class="daily-day-label">{label}</div>
                <div class="daily-record">{wins}-{losses}</div>
                <div class="daily-units {units_class}">{units:+.1f}u</div>
                <div class="daily-roi {roi_class}">{roi:+.1f}% ROI</div>
            </div>"""

    def _generate_daily_performance_section(self, performance_data):
        """Generate Daily Performance section: overall + per prop type (Top 6, Points, Assists, Rebounds, 3PT)."""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        w_today, l_today, u_today, r_today = self._get_daily_stats(performance_data, today)
        w_yest, l_yest, u_yest, r_yest = self._get_daily_stats(performance_data, yesterday)

        overall_html = f"""
        <div class="daily-performance-card">
            <h3>📅 Daily Performance</h3>
            <div class="daily-performance-row">
                {self._format_daily_box('TODAY', w_today, l_today, u_today, r_today)}
                {self._format_daily_box('YESTERDAY', w_yest, l_yest, u_yest, r_yest)}
            </div>
        </div>"""

        type_config = [
            ('top6', 'Top 6 Plays'),
            ('points', 'Points'),
            ('assists', 'Assists'),
            ('rebounds', 'Rebounds'),
            ('threes', '3 Points Made'),
        ]
        by_type_rows = []
        for type_key, type_label in type_config:
            w_t, l_t, u_t, r_t = self._get_daily_stats_by_type(performance_data, today, type_key)
            w_y, l_y, u_y, r_y = self._get_daily_stats_by_type(performance_data, yesterday, type_key)
            by_type_rows.append(f"""
            <div class="daily-type-row">
                <div class="daily-type-label">{type_label}</div>
                <div class="daily-type-boxes">
                    {self._format_daily_box('Today', w_t, l_t, u_t, r_t)}
                    {self._format_daily_box('Yesterday', w_y, l_y, u_y, r_y)}
                </div>
            </div>""")

        return overall_html + """
        <div class="daily-performance-by-type">
            <h3>📅 Daily Performance by Prop Type</h3>
            """ + "\n".join(by_type_rows) + """
        </div>"""

    def generate_dashboard(self, props, performance_data):
        """Generate complete HTML dashboard"""
        # First, deduplicate props - keep only the best side for each player/prop combo
        deduplicated_props = self._deduplicate_props(props)
        
        sorted_props = sorted(deduplicated_props, key=lambda x: x.get('ai_score', 0), reverse=True)
        
        # Smart top 6 selection - ensure diversity of prop types
        top_plays = self._select_diverse_top_plays(sorted_props, TOP_PLAYS_COUNT)
        
        total_props = len(deduplicated_props)
        value_props = len([p for p in deduplicated_props if p.get('is_value_play', False)])
        
        wins = performance_data.get('wins', 0)
        losses = performance_data.get('losses', 0)
        total_bets = wins + losses
        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CMZPROPS MODEL</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: url('abstract_background.jpg') no-repeat center center fixed, linear-gradient(135deg, #1a0a2e 0%, #0f172a 50%, #1e293b 100%);
            background-size: cover;
            color: #e2e8f0;
            min-height: 100vh;
            position: relative;
        }}
        
        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.4) 0%, rgba(30, 41, 59, 0.5) 100%);
            z-index: -1;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
        }}
        
        .header {{
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(51, 65, 85, 0.9) 100%);
            border-radius: 24px;
            padding: 40px 50px;
            margin-bottom: 30px;
            border: 1px solid rgba(148, 163, 184, 0.1);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
        }}
        
        .header-content {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .header-left h1 {{
            font-size: 48px;
            font-weight: 800;
            letter-spacing: -1px;
            background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        
        .header-left p {{
            color: #94a3b8;
            font-size: 16px;
            font-weight: 500;
        }}
        
        .season-record {{
            text-align: right;
        }}
        
        .season-label {{
            color: #10b981;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }}
        
        .record-number {{
            font-size: 42px;
            font-weight: 800;
            color: #10b981;
            line-height: 1;
        }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 700;
            color: #10b981;
            margin-bottom: 20px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .tabs-container {{
            display: flex;
            gap: 12px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}

        .tab-button {{
            background: rgba(30, 41, 59, 0.6);
            border: 2px solid rgba(148, 163, 184, 0.2);
            color: #94a3b8;
            padding: 12px 24px;
            border-radius: 12px;
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .tab-button:hover {{
            border-color: rgba(16, 185, 129, 0.4);
            color: #10b981;
        }}

        .tab-button.active {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-color: #10b981;
            color: #ffffff;
            box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
        }}

        .props-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .props-grid.single-column {{
            grid-template-columns: 1fr;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }}
        
        .prop-card {{
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(51, 65, 85, 0.9) 100%);
            border-radius: 20px;
            padding: 28px;
            border: 2px solid rgba(148, 163, 184, 0.15);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        /* Glow effect for OVER cards */
        .prop-card.over-glow {{
            border-color: #10b981;
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.5), 0 10px 40px rgba(0, 0, 0, 0.2);
        }}
        
        /* Glow effect for UNDER cards */
        .prop-card.under-glow {{
            border-color: #ef4444;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.5), 0 10px 40px rgba(0, 0, 0, 0.2);
        }}
        
        .prop-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #10b981 0%, #3b82f6 100%);
        }}
        
        .prop-card:hover {{
            transform: translateY(-4px);
        }}
        
        .player-header {{
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 20px;
        }}
        
        .team-logo {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: rgba(148, 163, 184, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            overflow: hidden;
        }}

        .team-logo img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
        }}
        
        .player-info h3 {{
            font-size: 24px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 4px;
        }}
        
        .game-info {{
            color: #94a3b8;
            font-size: 14px;
            font-weight: 500;
            line-height: 1.4;
        }}
        
        .bet-line {{
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 20px;
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(148, 163, 184, 0.2);
        }}

        .bet-line.under {{
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(148, 163, 184, 0.2);
        }}

        .bet-type {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        
        /* Color the OVER/UNDER text */
        .bet-type.over-text {{
            color: #10b981;
        }}
        
        .bet-type.under-text {{
            color: #ef4444;
        }}

        .bet-details {{
            color: #ffffff;
            font-size: 14px;
            opacity: 0.95;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-bottom: 20px;
        }}
        
        .stat-box {{
            background: rgba(15, 23, 42, 0.5);
            border-radius: 10px;
            padding: 12px;
            text-align: center;
        }}
        
        .stat-label {{
            color: #94a3b8;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        
        .stat-value {{
            font-size: 22px;
            font-weight: 700;
            color: #ffffff;
        }}
        
        .stat-value.positive {{
            color: #10b981;
        }}
        
        .stat-value.negative {{
            color: #ef4444;
        }}
        
        .insights {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .insight-tag {{
            background: rgba(59, 130, 246, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #60a5fa;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .insight-tag.positive {{
            background: rgba(16, 185, 129, 0.15);
            border-color: rgba(16, 185, 129, 0.3);
            color: #10b981;
        }}
        
        .performance-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }}
        
        .performance-card {{
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(51, 65, 85, 0.9) 100%);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(148, 163, 184, 0.15);
        }}
        
        .performance-card h3 {{
            color: #10b981;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 16px;
        }}
        
        .perf-stat {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
        }}
        
        .perf-stat:last-child {{
            border-bottom: none;
        }}
        
        .perf-label {{
            color: #94a3b8;
            font-size: 14px;
        }}
        
        .perf-value {{
            color: #ffffff;
            font-weight: 700;
            font-size: 16px;
        }}
        
        /* ===== Prop Tracker Styles ===== */
        .prop-tracker {{
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(51, 65, 85, 0.9) 100%);
            border-radius: 20px;
            padding: 28px;
            border: 1px solid rgba(148, 163, 184, 0.15);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
            margin-top: 30px;
            display: none;
        }}

        .tracker-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 12px;
        }}

        .tracker-header h3 {{
            font-size: 18px;
            font-weight: 700;
            color: #10b981;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .tracker-summary {{
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }}

        .tracker-summary span {{
            font-size: 14px;
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 8px;
            background: rgba(15, 23, 42, 0.5);
        }}

        .tracker-hits {{
            color: #10b981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .tracker-misses {{
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }}

        .tracker-pending-count {{
            color: #f59e0b;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }}

        .tracker-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .tracker-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(15, 23, 42, 0.5);
            border-radius: 12px;
            padding: 14px 18px;
            border: 1px solid rgba(148, 163, 184, 0.1);
            transition: all 0.3s ease;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .tracker-row.result-hit {{
            border-color: rgba(16, 185, 129, 0.4);
            background: rgba(16, 185, 129, 0.08);
        }}

        .tracker-row.result-miss {{
            border-color: rgba(239, 68, 68, 0.4);
            background: rgba(239, 68, 68, 0.08);
        }}

        .tracker-row.result-push {{
            border-color: rgba(245, 158, 11, 0.4);
            background: rgba(245, 158, 11, 0.08);
        }}

        .tracker-player {{
            font-size: 15px;
            font-weight: 700;
            color: #ffffff;
            min-width: 140px;
        }}

        .tracker-line {{
            font-size: 14px;
            font-weight: 600;
            min-width: 130px;
        }}

        .tracker-line.over-text {{
            color: #10b981;
        }}

        .tracker-line.under-text {{
            color: #ef4444;
        }}

        .tracker-buttons {{
            display: flex;
            gap: 6px;
        }}

        .tracker-btn {{
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            border: 1px solid rgba(148, 163, 184, 0.2);
            background: rgba(15, 23, 42, 0.6);
            color: #94a3b8;
            transition: all 0.2s ease;
        }}

        .tracker-btn:hover {{
            transform: scale(1.05);
        }}

        .tracker-btn.hit-btn:hover, .tracker-btn.hit-btn.active {{
            background: rgba(16, 185, 129, 0.2);
            border-color: #10b981;
            color: #10b981;
        }}

        .tracker-btn.miss-btn:hover, .tracker-btn.miss-btn.active {{
            background: rgba(239, 68, 68, 0.2);
            border-color: #ef4444;
            color: #ef4444;
        }}

        .tracker-btn.push-btn:hover, .tracker-btn.push-btn.active {{
            background: rgba(245, 158, 11, 0.2);
            border-color: #f59e0b;
            color: #f59e0b;
        }}

        .tracker-result {{
            font-size: 13px;
            font-weight: 700;
            min-width: 60px;
            text-align: center;
        }}

        /* ===== Daily Performance (Today / Yesterday + ROI) ===== */
        .daily-performance-card {{
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(51, 65, 85, 0.9) 100%);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(148, 163, 184, 0.15);
            margin-top: 30px;
        }}

        .daily-performance-card h3,
        .daily-performance-by-type h3 {{
            color: #10b981;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 16px;
        }}

        .daily-performance-row {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}

        .daily-day-box {{
            flex: 1;
            min-width: 140px;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            text-align: center;
        }}

        .daily-day-label {{
            font-size: 11px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .daily-record {{
            font-size: 22px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 4px;
        }}

        .daily-units {{
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 2px;
        }}

        .daily-units.positive {{ color: #10b981; }}
        .daily-units.negative {{ color: #ef4444; }}

        .daily-roi {{
            font-size: 14px;
            font-weight: 700;
        }}

        .daily-roi.positive {{ color: #10b981; }}
        .daily-roi.negative {{ color: #ef4444; }}

        .daily-performance-by-type {{
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(51, 65, 85, 0.9) 100%);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(148, 163, 184, 0.15);
            margin-top: 20px;
        }}

        .daily-type-row {{
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 12px 0;
            border-bottom: 1px solid rgba(148, 163, 184, 0.1);
            flex-wrap: wrap;
        }}

        .daily-type-row:last-child {{
            border-bottom: none;
        }}

        .daily-type-label {{
            font-size: 14px;
            font-weight: 700;
            color: #e2e8f0;
            min-width: 120px;
        }}

        .daily-type-boxes {{
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
        }}

        .daily-type-boxes .daily-day-box {{
            min-width: 120px;
            flex: 0 1 auto;
        }}

        @media (max-width: 768px) {{
            .header-content {{
                flex-direction: column;
                text-align: center;
                gap: 20px;
            }}
            
            .season-record {{
                text-align: center;
            }}
            
            .props-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <div class="header-left">
                    <h1>CMZPROPS MODEL</h1>
                    <p>NBA Props Model • Live API Data • Season 2025-26</p>
                </div>
                <div class="season-record">
                    <div class="season-label">SEASON RECORD</div>
                    <div class="record-number">{wins}-{losses}</div>
                </div>
            </div>
        </div>

        <div class="section-title">Top Value Play: AI LIVE PROP</div>

        <div class="tabs-container">
            <button class="tab-button active" data-tab="all">🔥 Top 6 Plays</button>
            <button class="tab-button" data-tab="points">Points</button>
            <button class="tab-button" data-tab="assists">Assists</button>
            <button class="tab-button" data-tab="rebounds">Rebounds</button>
            <button class="tab-button" data-tab="threes">3 Points Made</button>
        </div>

        <div class="props-grid">
"""

        # Build set of top play identities for marking
        top_play_ids = set()
        for tp in top_plays:
            key = (tp.get('player_name', ''), tp.get('prop_type', ''), tp.get('betting_line', 0), tp.get('side', ''))
            top_play_ids.add(key)

        # Sort: Overs first, then Unders; within each by AI score descending
        display_props_order = sorted(
            sorted_props,
            key=lambda x: (0 if (x.get('side') or 'Over') == 'Over' else 1, -x.get('ai_score', 0))
        )

        # Generate cards for ALL props (not just top plays) so filtering works
        for prop in display_props_order:
            key = (prop.get('player_name', ''), prop.get('prop_type', ''), prop.get('betting_line', 0), prop.get('side', ''))
            html += self._generate_prop_card(prop, is_top_play=(key in top_play_ids))
        
        html += """
        </div>
        """
        # Daily Performance (overall) then Daily by Prop Type — on top
        html += self._generate_daily_performance_section(performance_data)
        # Model Performance (3 cards) — on bottom
        html += """
        <div class=\"section-title\">Model Performance</div>
        <div class=\"performance-grid\">
    """
        html += self._generate_performance_section(performance_data, total_props, value_props, win_rate)

        html += """
        </div>
    </div>

        <script>
        // Tab filtering functionality (no prop tracker logic)
        const tabButtons = document.querySelectorAll('.tab-button');
        const propCards = document.querySelectorAll('.prop-card');
        const propsGrid = document.querySelector('.props-grid');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all buttons
                tabButtons.forEach(btn => btn.classList.remove('active'));

                // Add active class to clicked button
                button.classList.add('active');

                // Get the selected tab
                const selectedTab = button.getAttribute('data-tab');

                // Toggle single-column layout for specific tabs
                if (selectedTab === 'all') {
                    propsGrid.classList.remove('single-column');
                } else {
                    propsGrid.classList.add('single-column');
                }

                // Filter prop cards
                if (selectedTab === 'all') {
                    // Show only the diverse top plays (marked server-side)
                    propCards.forEach(card => {
                        if (card.hasAttribute('data-top-play')) {
                            card.style.display = 'block';
                        } else {
                            card.style.display = 'none';
                        }
                    });
                } else {
                    // Filter by prop type
                    propCards.forEach(card => {
                        const propType = card.getAttribute('data-prop-type');
                        if (propType === selectedTab) {
                            card.style.display = 'block';
                        } else {
                            card.style.display = 'none';
                        }
                    });
                }
            });
        });

        // Initialize with top 6 plays
        document.addEventListener('DOMContentLoaded', () => {
            const allButton = document.querySelector('[data-tab="all"]');
            if (allButton) {
                allButton.click();
            }
        });
        </script>
</body>
</html>
"""
        return html
    
    def save_html(self, html_content, filename=OUTPUT_HTML):
        """Save HTML to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            if DEBUG_MODE:
                print(f"✅ Dashboard saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving HTML: {str(e)}")
