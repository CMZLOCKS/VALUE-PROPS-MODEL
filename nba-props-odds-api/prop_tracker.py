"""
Prop Tracker - Track value plays, grade with actual stats, aggregate daily performance.
Feeds performance.json daily/daily_by_type for the dashboard.
"""

import os
import json
import time
from datetime import datetime, timedelta
from config import (
    DATA_DIR,
    TRACKING_FILE,
    PERFORMANCE_FILE,
    UNITS_PER_BET,
    GRADING_HOURS_AFTER_GAME,
    DEBUG_MODE,
)

# Prop type (from analysis) -> stat key for NBA API
PROP_TYPE_TO_STAT = {
    'points': 'PTS',
    'assists': 'AST',
    'rebounds': 'REB',
    'threes': 'FG3M',
    '3pt': 'FG3M',
    'three_pointers': 'FG3M',
    '3-pointers': 'FG3M',
}


def _prop_type_key(prop):
    """Return canonical key: points, assists, rebounds, threes."""
    t = (prop.get('prop_type') or 'points').lower()
    if '3' in t or 'three' in t:
        return 'threes'
    for k in ('points', 'assists', 'rebounds', 'threes'):
        if k in t:
            return k
    return 'points'


def load_tracking_data():
    """Load tracking JSON. Structure: { 'picks': [ ... ] }."""
    try:
        if os.path.exists(TRACKING_FILE):
            with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            data.setdefault('picks', [])
            return data
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ Could not load tracking: {e}")
    return {'picks': []}


def save_tracking_data(data):
    """Save tracking JSON."""
    try:
        os.makedirs(os.path.dirname(TRACKING_FILE) or '.', exist_ok=True)
        with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        if DEBUG_MODE:
            print("✅ Tracking data saved")
    except Exception as e:
        print(f"❌ Error saving tracking: {e}")


def _pick_id(prop):
    """Unique id for a pick (same player/line/side/date = same pick)."""
    return "{}|{}|{}|{}|{}".format(
        (prop.get('player_name') or '').strip(),
        _prop_type_key(prop),
        prop.get('betting_line', 0),
        prop.get('side', 'Over'),
        prop.get('game_date', ''),
    )


def _profit_loss_cents(win, odds_american):
    """Profit in cents (1 unit = 100 cents). Uses opening_odds."""
    if win:
        if odds_american > 0:
            return int(odds_american)  # e.g. +150 -> 150 cents
        return int((100.0 / abs(odds_american)) * 100)  # e.g. -110 -> 91 cents
    return -100  # loss = -1 unit


def track_new_picks(value_props, top_play_keys, data_fetcher):
    """
    Add today's value plays to tracking. Skip if pick_id already exists.
    top_play_keys: set of (player_name, prop_type, line, side) for top 6.
    """
    tracking = load_tracking_data()
    existing_ids = {p.get('pick_id') for p in tracking['picks'] if p.get('pick_id')}
    today = datetime.now().strftime('%Y-%m-%d')
    added = 0
    updated = 0

    for prop in value_props:
        pid = _pick_id(prop)
        if pid in existing_ids:
            continue
        game_date = prop.get('game_date') or today
        # Only track picks for today's games (or future); don't backfill old days
        if game_date < today:
            continue
        existing_ids.add(pid)
        key = (
            prop.get('player_name', ''),
            _prop_type_key(prop),
            prop.get('betting_line', 0),
            prop.get('side', ''),
        )
        is_top6 = key in top_play_keys
        odds = prop.get('odds', -110)
        try:
            odds = int(odds)
        except (TypeError, ValueError):
            odds = -110

        pick = {
            'pick_id': pid,
            'player_name': prop.get('player_name', ''),
            'prop_type_key': _prop_type_key(prop),
            'is_top6': is_top6,
            'line': prop.get('betting_line', 0),
            'side': prop.get('side', 'Over'),
            'odds': odds,
            'opening_odds': odds,
            'game_date': game_date,
            'start_time': prop.get('start_time', ''),
            'tracked_at': datetime.now().isoformat(),
            'status': 'pending',
            'result': None,
            'actual_stat': None,
            'profit_loss': None,
            'updated_at': None,
        }
        tracking['picks'].append(pick)
        added += 1

    if added > 0:
        save_tracking_data(tracking)
        if DEBUG_MODE:
            print(f"📋 Tracked {added} new picks for {today}")
    return added


def grade_pending_picks(tracking_data, data_fetcher):
    """
    Grade pending picks whose game_date is in the past using actual stats.
    Updates status, result, actual_stat, profit_loss.
    """
    pending = [p for p in tracking_data['picks'] if p.get('status') == 'pending']
    today = datetime.now().strftime('%Y-%m-%d')
    graded = 0

    for pick in pending:
        game_date = pick.get('game_date', '')
        if not game_date or game_date >= today:
            continue
        stat_key = PROP_TYPE_TO_STAT.get(pick.get('prop_type_key', 'points'), 'PTS')
        actual = data_fetcher.fetch_player_stat_for_date(
            pick['player_name'],
            game_date,
            stat_key,
        )
        if actual is None:
            continue
        time.sleep(0.6)  # rate limit nba_api
        line = pick.get('line', 0)
        side = (pick.get('side') or 'Over').lower()
        if side == 'over':
            if actual > line:
                win = True
            elif actual < line:
                win = False
            else:
                win = None  # push
        else:
            if actual < line:
                win = True
            elif actual > line:
                win = False
            else:
                win = None
        odds = pick.get('opening_odds') or pick.get('odds', -110)
        if win is None:
            pick['status'] = 'push'
            pick['result'] = 'PUSH'
            pick['actual_stat'] = actual
            pick['profit_loss'] = 0
        else:
            pick['status'] = 'win' if win else 'loss'
            pick['result'] = 'WIN' if win else 'LOSS'
            pick['actual_stat'] = actual
            pick['profit_loss'] = _profit_loss_cents(win, odds)
        pick['updated_at'] = datetime.now().isoformat()
        graded += 1
        if DEBUG_MODE:
            print(f"   Graded: {pick['player_name']} {pick['result']} (actual {stat_key}={actual}, line={line})")

    if graded > 0:
        save_tracking_data(tracking_data)
        if DEBUG_MODE:
            print(f"✅ Graded {graded} pending picks")
    return graded


def backfill_profit_loss(tracking_data):
    """Set profit_loss for any graded pick missing it."""
    updated = 0
    for pick in tracking_data['picks']:
        if pick.get('status') in ('win', 'loss') and pick.get('profit_loss') is None:
            odds = pick.get('opening_odds') or pick.get('odds', -110)
            win = pick.get('status') == 'win'
            pick['profit_loss'] = _profit_loss_cents(win, odds)
            updated += 1
    if updated > 0:
        save_tracking_data(tracking_data)
        if DEBUG_MODE:
            print(f"✅ Backfilled profit_loss for {updated} picks")
    return updated


def aggregate_to_performance(tracking_data):
    """
    Compute daily and daily_by_type from completed picks (win/loss/push).
    Returns (daily_dict, daily_by_type_dict) for merging into performance.json.
    """
    daily = {}
    daily_by_type = {}
    completed = [p for p in tracking_data['picks'] if p.get('status') in ('win', 'loss', 'push')]

    for pick in completed:
        date_str = pick.get('game_date', '')
        if not date_str:
            continue
        is_push = pick.get('status') == 'push'
        wins = 1 if pick.get('status') == 'win' else 0
        losses = 0 if is_push else (0 if pick.get('status') == 'win' else 1)
        pushes = 1 if is_push else 0
        pl = pick.get('profit_loss') or 0
        units = pl / 100.0
        settled = wins + losses
        roi = (units / settled * 100) if settled > 0 else 0.0

        # Overall daily
        if date_str not in daily:
            daily[date_str] = {'wins': 0, 'losses': 0, 'pushes': 0, 'units': 0.0, 'roi': 0.0}
        d = daily[date_str]
        d['wins'] += wins
        d['losses'] += losses
        d['pushes'] += pushes
        d['units'] += units
        total_settled = d['wins'] + d['losses']
        d['roi'] = (d['units'] / total_settled * 100) if total_settled > 0 else 0.0

        # By type
        if date_str not in daily_by_type:
            daily_by_type[date_str] = {
                'top6': {'wins': 0, 'losses': 0, 'pushes': 0, 'units': 0.0, 'roi': 0.0},
                'points': {'wins': 0, 'losses': 0, 'pushes': 0, 'units': 0.0, 'roi': 0.0},
                'assists': {'wins': 0, 'losses': 0, 'pushes': 0, 'units': 0.0, 'roi': 0.0},
                'rebounds': {'wins': 0, 'losses': 0, 'pushes': 0, 'units': 0.0, 'roi': 0.0},
                'threes': {'wins': 0, 'losses': 0, 'pushes': 0, 'units': 0.0, 'roi': 0.0},
            }
        type_key = pick.get('prop_type_key', 'points')
        t = daily_by_type[date_str].get(type_key)
        if t is None:
            daily_by_type[date_str][type_key] = {'wins': 0, 'losses': 0, 'pushes': 0, 'units': 0.0, 'roi': 0.0}
            t = daily_by_type[date_str][type_key]
        t['wins'] += wins
        t['losses'] += losses
        t['pushes'] += pushes
        t['units'] += units
        ts = t['wins'] + t['losses']
        t['roi'] = (t['units'] / ts * 100) if ts > 0 else 0.0

        if pick.get('is_top6'):
            top = daily_by_type[date_str]['top6']
            top['wins'] += wins
            top['losses'] += losses
            top['pushes'] += pushes
            top['units'] += units
            tst = top['wins'] + top['losses']
            top['roi'] = (top['units'] / tst * 100) if tst > 0 else 0.0

    return daily, daily_by_type


def merge_and_save_performance(tracking_data):
    """
    Aggregate from tracking, merge into performance.json, save.
    Also updates overall wins/losses/units/roi from all completed picks.
    """
    daily, daily_by_type = aggregate_to_performance(tracking_data)
    completed = [p for p in tracking_data['picks'] if p.get('status') in ('win', 'loss')]
    wins = sum(1 for p in completed if p.get('status') == 'win')
    losses = sum(1 for p in completed if p.get('status') == 'loss')
    total_units = sum((p.get('profit_loss') or 0) / 100.0 for p in completed)
    total_bets = wins + losses
    roi = (total_units / total_bets * 100) if total_bets > 0 else 0.0

    try:
        if os.path.exists(PERFORMANCE_FILE):
            with open(PERFORMANCE_FILE, 'r', encoding='utf-8') as f:
                perf = json.load(f)
        else:
            perf = {
                'wins': 0, 'losses': 0, 'units': 0.0, 'roi': 0.0, 'total_bets': 0,
                'daily': {}, 'daily_by_type': {},
            }
        perf['wins'] = wins
        perf['losses'] = losses
        perf['units'] = round(total_units, 2)
        perf['roi'] = round(roi, 2)
        perf['total_bets'] = total_bets
        perf['daily'] = daily
        perf['daily_by_type'] = daily_by_type
        os.makedirs(os.path.dirname(PERFORMANCE_FILE) or '.', exist_ok=True)
        with open(PERFORMANCE_FILE, 'w', encoding='utf-8') as f:
            json.dump(perf, f, indent=2)
        if DEBUG_MODE:
            print("✅ Performance.json updated (daily + daily_by_type)")
    except Exception as e:
        print(f"❌ Error saving performance: {e}")
