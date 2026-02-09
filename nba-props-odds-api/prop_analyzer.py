"""
Prop Analyzer Module - Precise Props Model
Uses per-36 efficiency, opponent defense factors, consistency scoring,
and proper EV calculation based on odds-implied probability.
"""

import math
from config import *

# Minimum edge requirements by prop type (for OVER / UNDER)
MIN_EDGE = {
    'points':  {'over': 2.0, 'under': 1.5},
    'assists': {'over': 1.5, 'under': 1.0},
    'rebounds': {'over': 1.5, 'under': 1.0},
    'threes':  {'over': 1.0, 'under': 0.8},
    '3-pointers': {'over': 1.0, 'under': 0.8},
}

# Per-36 thresholds for bonus scoring
PER36_THRESHOLDS = {
    'points':  [(25.0, 1.5), (20.0, 1.0)],
    'assists': [(8.0, 1.5), (6.0, 1.0)],
    'rebounds': [(10.0, 1.5), (7.0, 1.0)],
    'threes':  [(3.5, 1.5), (2.5, 1.0)],
    '3-pointers': [(3.5, 1.5), (2.5, 1.0)],
}


class PropAnalyzer:
    """Analyzes player props to find betting value using precise model"""

    def __init__(self):
        if DEBUG_MODE:
            print("✅ Prop Analyzer initialized")

    def calculate_ai_score(self, player_stats, prop_type, betting_line, side='Over',
                           opponent_defense=None):
        """
        Calculate AI score (0-10) using multi-factor analysis.

        Factors:
        - Edge vs season average (granular thresholds by prop type)
        - Recent form (L10 avg vs line)
        - Per-36 minute efficiency
        - Consistency multiplier
        - Opponent defense factor
        - Shooting efficiency (for points/threes)
        """
        try:
            season_avg = player_stats.get('season_avg', 0)
            last_10_avg = player_stats.get('last_10_avg', 0)
            minutes = player_stats.get('minutes', 0)
            games_played = player_stats.get('games_played', 0)
            fg_pct = player_stats.get('fg_pct', 0)
            fg3_pct = player_stats.get('fg3_pct', 0)

            # Minimum qualifications
            if games_played < MIN_GAMES_PLAYED or minutes < 15:
                return 0.0

            # Calculate edge based on side
            if side == 'Under':
                edge_season = betting_line - season_avg
                edge_recent = betting_line - last_10_avg
            else:
                edge_season = season_avg - betting_line
                edge_recent = last_10_avg - betting_line

            # Check minimum edge requirement
            prop_lower = prop_type.lower()
            min_edges = MIN_EDGE.get(prop_lower, {'over': 1.0, 'under': 0.8})
            min_edge_req = min_edges['under'] if side == 'Under' else min_edges['over']
            if edge_season < min_edge_req * 0.3 and edge_recent < min_edge_req * 0.3:
                return 0.0  # Not enough edge

            # === START SCORING (base 4.0) ===
            score = 4.0

            # --- Factor 1: Edge vs season average (up to +3.5) ---
            edge_thresholds = self._get_edge_thresholds(prop_lower)
            for threshold, bonus in edge_thresholds:
                if edge_season >= threshold:
                    score += bonus
                    break

            # --- Factor 2: Recent form bonus (up to +2.5) ---
            if edge_recent >= 1.2:
                score += 2.5
            elif edge_recent >= 1.0:
                score += 1.5
            elif edge_recent >= 0.5:
                score += 0.8

            # --- Factor 3: Per-36 minute efficiency (up to +1.5) ---
            if minutes > 0:
                per_36 = (season_avg / minutes) * 36.0
                thresholds = PER36_THRESHOLDS.get(prop_lower, [(20.0, 1.0)])
                for threshold, bonus in thresholds:
                    if per_36 >= threshold:
                        score += bonus
                        break

            # --- Factor 4: Consistency multiplier (up to +0.8) ---
            # Use coefficient of variation: lower = more consistent
            if season_avg > 0:
                # Approximate consistency from how close L10 is to season avg
                consistency = 1.0 - min(abs(last_10_avg - season_avg) / season_avg, 1.0)
                score += consistency * 0.8

            # --- Factor 5: Opponent defense factor (up to +1.0 / -0.5) ---
            if opponent_defense:
                def_rating = opponent_defense.get('DEF_RATING', 110.0)
                pace = opponent_defense.get('PACE', 100.0)
                defense_factor = (def_rating / 110.0) * (pace / 100.0)

                if side == 'Over':
                    # Weak defense (high DEF_RATING) = good for OVER
                    if defense_factor > 1.05:
                        score += 1.0
                    elif defense_factor > 1.02:
                        score += 0.5
                    # Strong defense = penalty
                    elif defense_factor < 0.95:
                        score -= 0.5
                else:
                    # Strong defense = good for UNDER
                    if defense_factor < 0.95:
                        score += 1.0
                    elif defense_factor < 0.98:
                        score += 0.5
                    # Weak defense = penalty for under
                    elif defense_factor > 1.05:
                        score -= 0.5

            # --- Factor 6: Shooting efficiency bonus (up to +0.5) ---
            if prop_lower in ('points', 'threes', '3-pointers'):
                if fg_pct >= 0.48:
                    score += 0.5
                elif fg_pct >= 0.45:
                    score += 0.3

                if prop_lower in ('threes', '3-pointers') and fg3_pct >= 0.37:
                    score += 0.3

            # Cap between 0 and 10
            score = max(0.0, min(score, 10.0))
            return round(score, 1)

        except Exception as e:
            if DEBUG_MODE:
                print(f"⚠️ Error calculating AI score: {e}")
            return 0.0

    def _get_edge_thresholds(self, prop_type):
        """Get edge threshold/bonus pairs by prop type (descending order)"""
        if prop_type == 'points':
            return [(2.0, 3.5), (1.5, 2.5), (1.0, 1.5), (0.5, 0.5)]
        elif prop_type == 'assists':
            return [(1.5, 3.5), (1.0, 2.5), (0.5, 1.5), (0.3, 0.5)]
        elif prop_type == 'rebounds':
            return [(1.5, 3.5), (1.0, 2.5), (0.5, 1.5), (0.3, 0.5)]
        elif prop_type in ('threes', '3-pointers'):
            return [(1.0, 3.5), (0.8, 2.5), (0.5, 1.5), (0.3, 0.5)]
        return [(1.5, 3.0), (1.0, 2.0), (0.5, 1.0), (0.2, 0.5)]

    def calculate_expected_value(self, ai_score, edge, odds=-110, side='Over'):
        """
        Calculate EV using odds-implied probability vs model true probability.

        true_prob = base + AI multiplier + edge factor + recent factor
        EV = (true_prob × payout_ratio) - (1 - true_prob)
        """
        try:
            # Convert odds to implied probability
            if odds < 0:
                implied_prob = abs(odds) / (abs(odds) + 100)
                payout_ratio = 100 / abs(odds)
            else:
                implied_prob = 100 / (odds + 100)
                payout_ratio = odds / 100

            # Calculate true probability from our model
            base_prob = 0.50

            # AI score multiplier: scores above 9.0 add up to 15%
            ai_multiplier = max(0, (ai_score - 7.0) / 3.0) * 0.15

            # Edge factor: larger edge adds up to 15%
            edge_factor = min(abs(edge) / 2.0, 1.0) * 0.15

            true_prob = base_prob + ai_multiplier + edge_factor
            true_prob = max(0.40, min(true_prob, 0.70))  # Clamp 40-70%

            # EV = (win_prob × profit) - (lose_prob × stake)
            ev = (true_prob * payout_ratio) - (1 - true_prob)
            ev_percentage = ev * 100

            return round(ev_percentage, 1), round(true_prob * 100)

        except Exception as e:
            if DEBUG_MODE:
                print(f"⚠️ Error calculating EV: {e}")
            return 0.0, 50

    def calculate_prediction(self, player_stats, prop_type, side='Over',
                             opponent_defense=None):
        """
        Calculate model prediction (what we think the player will score).

        Uses weighted blend of season avg, L10 avg, and opponent-adjusted projection.
        """
        season_avg = player_stats.get('season_avg', 0)
        last_10_avg = player_stats.get('last_10_avg', 0)
        minutes = player_stats.get('minutes', 0)

        # Weighted blend: 40% season, 60% recent
        base_prediction = (season_avg * 0.40) + (last_10_avg * 0.60)

        # Per-36 adjustment: if player is playing more/fewer minutes than avg
        if minutes > 0:
            per_36_rate = (season_avg / minutes) * 36.0
            # Slight per-36 nudge (5% weight)
            base_prediction = base_prediction * 0.95 + per_36_rate * 0.05

        # Opponent adjustment
        if opponent_defense:
            def_rating = opponent_defense.get('DEF_RATING', 110.0)
            pace = opponent_defense.get('PACE', 100.0)
            # Defense factor relative to league average
            defense_factor = (def_rating / 110.0) * (pace / 100.0)
            # Apply as a multiplier (capped ±10%)
            opp_multiplier = max(0.90, min(defense_factor, 1.10))
            base_prediction *= opp_multiplier

        return round(base_prediction, 1)

    def analyze_prop(self, player_info, player_stats, prop_type, betting_line,
                     odds=-110, side='Over', opponent_defense=None):
        """
        Complete analysis of a single prop bet with precise model.
        """
        try:
            # Model prediction
            prediction = self.calculate_prediction(
                player_stats, prop_type, side, opponent_defense)

            # AI Score (multi-factor)
            ai_score = self.calculate_ai_score(
                player_stats, prop_type, betting_line, side, opponent_defense)

            # Edge calculation
            if side == 'Under':
                edge = betting_line - prediction
            else:
                edge = prediction - betting_line

            # EV and win probability (using odds-implied math)
            ev, win_prob = self.calculate_expected_value(ai_score, edge, odds, side)

            prop_analysis = {
                'player_name': player_info.get('name', 'Unknown'),
                'team': player_info.get('team', 'Unknown'),
                'opponent': player_info.get('opponent', 'Unknown'),
                'game_time': player_info.get('game_time', 'TBD'),

                'prop_type': prop_type,
                'betting_line': betting_line,
                'odds': odds,
                'direction': side.upper(),
                'side': side,

                'prediction': prediction,
                'edge': round(edge, 1),
                'ai_score': ai_score,
                'ev': ev,
                'win_probability': win_prob,

                'season_avg': player_stats.get('season_avg', 0),
                'last_10_avg': player_stats.get('last_10_avg', 0),
                'last_5_avg': player_stats.get('last_5_avg', 0),
                'games_played': player_stats.get('games_played', 0),

                'is_value_play': ai_score >= MIN_AI_SCORE_BY_TYPE.get(
                    prop_type.lower(), MIN_AI_SCORE_THRESHOLD),
                'insights': self._generate_insights(
                    player_stats, betting_line, edge, prediction, side,
                    opponent_defense)
            }

            return prop_analysis

        except Exception as e:
            if DEBUG_MODE:
                print(f"❌ Error analyzing prop: {e}")
            return None

    def _generate_insights(self, player_stats, betting_line, edge, prediction,
                           side='Over', opponent_defense=None):
        """Generate contextual insight tags for the prop card"""
        insights = []
        last_10 = player_stats.get('last_10_avg', 0)
        season = player_stats.get('season_avg', 0)

        # Hot/Cold tag
        if side == 'Over':
            if last_10 > season * 1.10:
                insights.append("🔥 Hot Streak")
            elif last_10 < season * 0.90:
                insights.append("❄️ Cold Streak")
        else:
            if last_10 < season * 0.90:
                insights.append("📉 Trending Down")

        # Edge insight
        if abs(edge) >= 1.5:
            insights.append(f"Edge: {edge:+.1f}")

        # Prediction insight
        insights.append(f"Model: {prediction:.1f}")

        # Opponent insight
        if opponent_defense:
            def_rating = opponent_defense.get('DEF_RATING', 110.0)
            if def_rating >= 114:
                insights.append("Weak DEF Matchup")
            elif def_rating <= 106:
                insights.append("Tough DEF Matchup")

        return insights
