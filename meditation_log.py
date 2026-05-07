"""
Log de sesiones de meditacion. Persistencia local en meditation_log.json.
Esquema: lista de sesiones con date (YYYY-MM-DD), day_number (1-28), duration_min, completed (bool), notes.
"""
import json
from pathlib import Path
from datetime import datetime, date, timedelta

LOG_FILE = Path(__file__).parent / "meditation_log.json"


def _load():
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {"sessions": [], "current_day": 1}


def _save(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_state():
    """Devuelve el estado completo del log."""
    return _load()


def get_current_day():
    """Devuelve el numero de dia actual del programa (1-28). Avanza con cada sesion completada."""
    data = _load()
    return min(data.get("current_day", 1), 28)


def log_session(day_number, duration_min, completed=True, notes=""):
    """Registra una sesion completada y avanza el contador del programa."""
    data = _load()
    today = date.today().isoformat()

    data["sessions"].append({
        "date": today,
        "timestamp": datetime.now().isoformat(),
        "day_number": day_number,
        "duration_min": duration_min,
        "completed": completed,
        "notes": notes,
    })

    if completed:
        data["current_day"] = min(data.get("current_day", 1) + 1, 29)

    _save(data)
    return data


def reset_program():
    """Reinicia el programa al dia 1 sin borrar el historial."""
    data = _load()
    data["current_day"] = 1
    _save(data)
    return data


def sessions_in_month(year, month):
    """Devuelve lista de sesiones completadas en un mes."""
    data = _load()
    result = []
    for s in data["sessions"]:
        if not s.get("completed"):
            continue
        try:
            d = datetime.strptime(s["date"], "%Y-%m-%d").date()
            if d.year == year and d.month == month:
                result.append(s)
        except (ValueError, KeyError):
            continue
    return result


def monthly_stats(year, month):
    """Devuelve {sessions_count, minutes_total} para el mes."""
    sessions = sessions_in_month(year, month)
    return {
        "sessions_count": len(sessions),
        "minutes_total": sum(s.get("duration_min", 0) for s in sessions),
    }


def get_meditation_dates(days_back=90):
    """Devuelve set de fechas (YYYY-MM-DD) con al menos una sesion completada en los ultimos N dias."""
    data = _load()
    cutoff = date.today() - timedelta(days=days_back)
    result = set()
    for s in data["sessions"]:
        if not s.get("completed"):
            continue
        try:
            d = datetime.strptime(s["date"], "%Y-%m-%d").date()
            if d >= cutoff:
                result.add(s["date"])
        except (ValueError, KeyError):
            continue
    return result
