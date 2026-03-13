# Guia: Adaptar este proyecto de WHOOP a Oura Ring

Este proyecto usa **WHOOP** para datos de sueno, recovery y HR zones.
Si usas **Oura Ring**, aqui tienes lo que necesitas cambiar.

## Que datos da Oura Ring (equivalentes a WHOOP)

| Metrica            | WHOOP                    | Oura Ring                      |
|--------------------|--------------------------|--------------------------------|
| Sleep Duration     | Sleep stages (ms)        | `total_sleep_duration` (seg)   |
| Recovery Score     | Recovery Score (0-100%)  | `readiness.score` (0-100)      |
| Resting HR         | `resting_heart_rate`     | `lowest_heart_rate` (sleep)    |
| Sleep Consistency  | `sleep_consistency_%`    | No directo - calcular manual   |
| HR Zones 1-3       | Workout zone durations   | No directo - usar Garmin       |
| HR Zones 4-5       | Workout zone durations   | No directo - usar Garmin       |
| HRV                | `hrv_rmssd_milli`        | `average_hrv` (sleep)          |

**Nota:** Oura Ring NO tiene HR zones de workouts. Esos datos siguen viniendo de Garmin.

---

## Archivos a modificar

### 1. `whoop_streamlit.py` -> renombrar a `oura_streamlit.py`

Este es el archivo principal. Reemplazar las llamadas a WHOOP API por Oura API v2.

**Oura API base URL:** `https://api.ouraring.com/v2/usercollection`

**Endpoints que necesitas:**
- `GET /daily_sleep?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- `GET /daily_readiness?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- `GET /heartrate?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

**Autenticacion:** Oura usa Personal Access Token (mas simple que WHOOP OAuth).
- Ir a https://cloud.ouraring.com/personal-access-tokens
- Crear token
- Header: `Authorization: Bearer TU_TOKEN`

**Ejemplo de funcion equivalente:**

```python
import requests

OURA_API = 'https://api.ouraring.com/v2/usercollection'

def get_oura_monthly(year, month, token):
    headers = {'Authorization': f'Bearer {token}'}
    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month:02d}-{monthrange(year, month)[1]}"

    result = {
        'sleep_hours_avg': 0,
        'avg_recovery_score': 0,  # readiness score
        'avg_resting_hr': 0,
        'avg_sleep_consistency': 0,
    }

    # Sleep
    resp = requests.get(f"{OURA_API}/daily_sleep",
        headers=headers,
        params={'start_date': start, 'end_date': end})
    sleeps = resp.json().get('data', [])

    if sleeps:
        total_hours = sum(s['contributors']['total_sleep'] / 3600 for s in sleeps)
        result['sleep_hours_avg'] = round(total_hours / len(sleeps), 2)

    # Readiness (= Recovery en WHOOP)
    resp = requests.get(f"{OURA_API}/daily_readiness",
        headers=headers,
        params={'start_date': start, 'end_date': end})
    readiness = resp.json().get('data', [])

    if readiness:
        total_score = sum(r['score'] for r in readiness)
        result['avg_recovery_score'] = round(total_score / len(readiness), 1)
        # Resting HR viene en readiness contributors
        rhr_values = [r['contributors'].get('resting_heart_rate', 0) for r in readiness]
        rhr_valid = [v for v in rhr_values if v > 0]
        result['avg_resting_hr'] = round(sum(rhr_valid) / len(rhr_valid), 1) if rhr_valid else 0

    return result
```

### 2. `data_loader.py` - lineas 71-88

Cambiar la seccion `# --- WHOOP ---` para importar de `oura_streamlit` en vez de `whoop_streamlit`:

```python
# --- OURA RING ---
from oura_streamlit import get_oura_data
oura, source = get_oura_data(year, month)
data['whoop_source'] = source  # puedes renombrar a 'oura_source'

if oura:
    data['sleep_hours_avg'] = round(oura.get('sleep_hours_avg', 0), 1)
    data['recovery_score'] = round(oura.get('avg_recovery_score', 0), 1)
    data['resting_hr'] = round(oura.get('avg_resting_hr', 0), 1)
    # HR zones 1-3 y 4-5 NO vienen de Oura, vienen de Garmin
    # Si no usas Garmin, puedes quitar esas metricas
```

### 3. `.streamlit/secrets.toml` - Configurar token de Oura

```toml
[oura]
personal_access_token = "TU_TOKEN_AQUI"
```

### 4. Archivos que puedes ELIMINAR (son exclusivos de WHOOP)

- `whoop_streamlit.py` (reemplazado por `oura_streamlit.py`)
- `whoop_client_v2_corrected.py`
- `whoop_auth.py`
- `whoop_sync.py`
- `whoop_cache.json`
- `.github/workflows/whoop-sync.yml`

### 5. `requirements.txt`

No necesitas dependencias extra. Oura API usa `requests` que ya esta instalado.
Puedes quitar `supabase` y `cryptography` si no los usas.

---

## Resumen rapido

1. Crear token en https://cloud.ouraring.com/personal-access-tokens
2. Ponerlo en `.streamlit/secrets.toml`
3. Crear `oura_streamlit.py` con las funciones de arriba
4. Cambiar el import en `data_loader.py`
5. Borrar archivos de WHOOP
6. HR Zones siguen viniendo de Garmin (o quitar esas metricas si no usa Garmin)

---

## API Docs

- Oura API v2: https://cloud.ouraring.com/v2/docs
- Autenticacion: https://cloud.ouraring.com/docs/authentication
