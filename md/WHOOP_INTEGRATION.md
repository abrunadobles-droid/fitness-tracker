# WHOOP Integration

## Overview
WHOOP provides: HR Zones 1-3, HR Zones 4-5, Sleep Duration, Recovery Score, Resting HR, Sleep Consistency.
Garmin provides: Steps, Activities, Strength Training.

## File: `whoop_streamlit.py`
- Saved copy: `md/whoop_streamlit.py`
- Lives at root: `/home/user/fitness-tracker/whoop_streamlit.py`

## How It Works

### Token Management
1. Loads WHOOP OAuth tokens from `st.secrets["whoop"]` (access_token, refresh_token, expires_at)
2. Falls back to `WHOOP_TOKENS_JSON` env var, then `whoop_tokens.json` local file
3. Tokens stored in `st.session_state.whoop_tokens` during session
4. Auto-refreshes tokens via `_refresh_tokens()` when they expire (5-min buffer)
5. Needs `client_id` and `client_secret` from secrets for refresh

### API Endpoints Used
- `activity/sleep` - Sleep stages, sleep consistency percentage
- `recovery` - Recovery score, resting heart rate
- `activity/workout` - HR zone durations (zones 1-5 in milliseconds)

### Data Flow
```
get_whoop_data(year, month)
  ├── Try: get_whoop_monthly_live(year, month)  → calls WHOOP API
  │     ├── _get_all_records('activity/sleep', ...)
  │     ├── _get_all_records('recovery', ...)
  │     └── _get_all_records('activity/workout', ...)
  │
  └── Fallback: load_whoop_cache()  → reads whoop_cache.json
```

### Return Format
```python
{
    'sleep_hours_avg': 7.2,          # avg sleep hours per night
    'hr_zones_1_3_hours': 18.5,      # total monthly hours in zones 1-3
    'hr_zones_4_5_hours': 3.1,       # total monthly hours in zones 4-5
    'avg_recovery_score': 55.0,      # avg recovery %
    'avg_resting_hr': 52.0,          # avg resting HR bpm
    'avg_sleep_consistency': 78.0,   # avg sleep consistency %
}
```

### How Dashboard Uses It
In `dashboard.py`, `get_monthly_data(year, month)`:
```python
from whoop_streamlit import get_whoop_data

whoop_data, whoop_source = get_whoop_data(year, month)
if whoop_data:
    data['sleep_hours_avg'] = whoop_data.get('sleep_hours_avg', 0)
    data['hr_zone_1_3'] = whoop_data.get('hr_zones_1_3_hours', 0)
    data['hr_zone_4_5'] = whoop_data.get('hr_zones_4_5_hours', 0)
    data['recovery_score'] = whoop_data.get('avg_recovery_score', 0)
    data['resting_hr'] = whoop_data.get('avg_resting_hr', 0)
    data['sleep_consistency'] = whoop_data.get('avg_sleep_consistency', 0)
```

## Required Secrets (`.streamlit/secrets.toml`)
```toml
[whoop]
client_id = "..."
client_secret = "..."
access_token = "..."
refresh_token = "..."
expires_at = 1234567890
```
