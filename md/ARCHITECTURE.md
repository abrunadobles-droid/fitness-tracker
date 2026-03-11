# Fitness Tracker - Architecture & History

## Current State (March 2026)

The dashboard was rewritten in commit `60da1c3` ("Split dashboard into Fitness Habits & Sleep Habits sections") which replaced the original dashboard with a new version. Several features were lost in this rewrite.

### What Works Now
- **Garmin**: Steps, Activities, Strength Training
- **WHOOP** (via `whoop_streamlit.py`): HR Zones 1-3, HR Zones 4-5, Sleep Duration, Recovery Score, Resting HR, Sleep Consistency
- **Mes Actual tab**: metrics with progress bars, big stats summary, Proyeccion Fin de Mes, VS previous month comparison
- **Historico tab**: Promedio General, Detalle por Mes, Comparativa Mensual table
- **Actualizar button**: cache refresh

### What Was Lost in the Rewrite
1. **Login/Auth** (`auth.py`) - Supabase email/password auth, user sessions
2. **METAS tab** (`goals_setup.py`) - UI to configure personal goals
3. **Metas Ajustadas** - Adjusted goals calculation for remaining months to hit annual targets
4. **Logout button**
5. **Multi-user support** - per-user Garmin credentials and goals stored in Supabase
6. **SVG ring progress indicators** - replaced with flat progress bars

### Files That Still Exist But Are Not Used
- `auth.py` - Supabase auth (login/register/logout)
- `goals_setup.py` - Goals configuration UI with Supabase persistence
- `garmin_setup.py` - Garmin account connection form
- `crypto.py` - Encryption utilities for Garmin credentials

---

## Key Commits

| Commit | Description |
|--------|-------------|
| `f8c8091` | **Last version with ALL features** (auth, metas, metas ajustadas, SVG rings) |
| `60da1c3` | **The rewrite** - Split into Fitness/Sleep Habits, lost features |
| `5407e7a` | Added live WHOOP API integration |
| `2a4ff76` | Added projections and month-over-month comparison |

---

## Data Flow

### Current (WHOOP + Garmin)
```
dashboard.py
  ├── garmin_client.py → Steps, Activities, Strength
  └── whoop_streamlit.py → HR Zones, Sleep, Recovery, Resting HR, Consistency
```

### Old (Garmin only, with auth)
```
dashboard.py
  ├── auth.py → Supabase login/logout, get_user_id()
  ├── goals_setup.py → Per-user goals from Supabase
  ├── garmin_setup.py → Per-user Garmin connection
  ├── garmin_client.py → ALL metrics (steps, activities, strength, sleep, HR zones)
  └── crypto.py → Encrypt/decrypt Garmin credentials
```

---

## How to Restore Features

To bring back the lost features, you need to:

1. **Auth**: Import `auth.py` at the top of dashboard, call `show_auth_page()` before showing dashboard, gate with `st.stop()` if not logged in
2. **Goals**: Import `goals_setup.py`, add METAS tab to navigation, load goals with `get_user_goals()` instead of hardcoded dict
3. **Metas Ajustadas**: Add the calculation section back to the HISTORICO view (code in `md/dashboard_old_with_all_features.py` lines 618-681)
4. **Multi-user**: Pass `user_id` to data fetching functions

The key is to merge the OLD auth/goals/metas-ajustadas features WITH the NEW WHOOP data source and new features (projections, comparisons).

---

## Saved Code Files in This Folder

| File | Description |
|------|-------------|
| `dashboard_old_with_all_features.py` | Dashboard at commit `f8c8091` with auth, goals, metas ajustadas, SVG rings |
| `dashboard_current_whoop.py` | Current dashboard with WHOOP integration |
| `whoop_streamlit.py` | WHOOP API integration module |
| `WHOOP_INTEGRATION.md` | How WHOOP integration works |
| `METAS_AJUSTADAS.md` | The metas ajustadas feature code and logic |
