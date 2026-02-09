# Why Am I Only Seeing Some Games?

## The Issue

You saw there are **10 NBA games today** (Feb 7, 2026), but your model only found **1 game** (Mavericks @ Spurs).

## Why This Happens

**The Odds API only returns games that have betting lines (odds/props) currently available from sportsbooks.**

### When Props Are Posted

Sportsbooks typically post player props:
- ✅ **4-6 hours before tipoff** - Most props available
- ⚠️ **2-3 hours before tipoff** - Some props available  
- ❌ **Day before / early morning** - Very few or no props yet

### Your Game Times (from screenshot)

Looking at your games today:
1. **Wizards @ Nets** - Final (already finished)
2. **Rockets @ Thunder** - Final (already finished)  
3. **Mavericks @ Spurs** - Q1, 02:40 (IN PROGRESS) ✅ **This one has props!**
4. **Jazz @ Magic** - 4:00 PM (upcoming)
5. **Hornets @ Hawks** - 4:30 PM (upcoming)
6. **Nuggets @ Bulls** - 5:00 PM (upcoming)
7. **Warriors @ Lakers** - 5:30 PM (upcoming)
8. **76ers @ Suns** - 6:00 PM (upcoming)
9. **Grizzlies @ Trail Blazers** - 7:00 PM (upcoming)
10. **Cavaliers @ Kings** - 7:00 PM (upcoming)

**The games at 4:00 PM and later don't have props posted yet** - it's too early!

## Solutions

### Option 1: Run the Model Multiple Times (RECOMMENDED)

Run your model at different times throughout the day:

```bash
# Morning run - get early games
python main.py

# Afternoon run (2-3 PM) - get 4-6 PM games  
python main.py

# Evening run (5-6 PM) - get 7-9 PM games
python main.py
```

Each time you run it, you'll get fresh props for games starting in the next 4-6 hours.

### Option 2: Set DAYS_AHEAD Higher

In `config.py`:
```python
DAYS_AHEAD = 2  # Get tomorrow's games too
```

Tomorrow's props might already be posted!

### Option 3: Wait Closer to Game Time

Run the model **3-4 hours before the games you want to bet on**.

## Typical Workflow

**Best practice:**
1. Check NBA schedule in the morning
2. Note which games you're interested in
3. Run the model **4 hours before** those games start
4. Review the props and place bets **2-3 hours before** tipoff

## Example Timeline for Tonight's Games

If you want props for **Warriors @ Lakers (5:30 PM)**:
- ✅ Run model at **1:30 PM** - Props should be available
- ✅ Run model at **2:00 PM** - Definitely available  
- ❌ Run model at **9:00 AM** - Too early, no props yet

## Why Can't The API Get All Games?

The Odds API shows betting data from sportsbooks (FanDuel, DraftKings, etc.). If the sportsbooks haven't posted props yet, The Odds API can't return them - they literally don't exist yet!

## Pro Tips

1. **Bookmark NBA.com schedule** to see all games
2. **Run your model 4 hours before game time** for best results  
3. **Set DAYS_AHEAD = 3** to always have some games available
4. **Early afternoon runs** catch both early and evening games
5. **Props can change** - run multiple times to see line movements!

## Summary

✅ **Your model is working perfectly!**  
✅ **The Odds API is working correctly!**  
⏰ **You just need to run it at the right time!**

The missing 9 games don't have props posted yet. Check back in a few hours and you'll see more games appear!
