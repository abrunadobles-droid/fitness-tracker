# Fitness Tracker Automatizado

Dashboard personal de fitness que sincroniza datos de WHOOP y Garmin Connect, los presenta en un dashboard Streamlit con tema Dark Neon, y trackea progreso mensual contra metas personalizables.

**Usuario:** Antonio (macOS, MacBook Pro)
**Idioma:** Español (interfaz y documentación)

## Environment

- User's machine is macOS (MacBook Pro)
- Python command is `python3`, NOT `python` (no `python` alias on this Mac)
- Always use `python3` and `pip3` in any instructions or scripts for the user
- Python 3.11 en CI, Python 3.12 en la Mac del usuario (via Homebrew)
- garth >= 0.7.9 requerido (versiones anteriores tienen bug OAuth1 iOS→Android mismatch)

## Arquitectura

```
WHOOP API v2 ──┐                    ┌── whoop_cache.json ──┐
               ├── GitHub Actions ──┤                      ├── Streamlit Dashboard
Garmin API ────┘   (cron diario)    └── garmin_cache.json ──┘
```

- **Hybrid cloud + local:** GitHub Actions sincroniza datos diariamente, guarda en cache JSON, commitea al repo
- **Streamlit Cloud** lee caches + intenta APIs en vivo como fallback
- **Terminal local** para auth y sync manual (`whoop_sync.py`, `garmin_sync.py`)

## Archivos principales

### Dashboard & Vistas
- `dashboard.py` - Entry point Streamlit. Tema Dark Neon, navegación 4 tabs, gate de metas
- `views/mes_actual.py` - Vista mes actual: cards resumen, métricas fitness/sueño, comparación vs mes anterior
- `views/historico.py` - Vista histórica: promedios anuales, metas ajustadas, breakdown por mes

### Datos & Config
- `config.py` - Carga secrets (env vars → Streamlit secrets → .streamlit/secrets.toml)
- `data_loader.py` - Fetch mensual de Garmin (live + cache) y WHOOP (via whoop_streamlit.py)
- `goals_setup.py` - Gestión de metas en JSON local (goals.json), 9 métricas
- `constants.py` - Definiciones de métricas, traducciones de meses
- `helpers.py` - Utilidades: formateo, cálculo de %, status emojis, render de cards

### WHOOP
- `whoop_auth.py` - OAuth2 flow completo (browser → callback localhost:8000 → tokens)
- `whoop_client_v2_corrected.py` - Cliente API v2: sleep, recovery, HRV, HR zones, workouts
- `whoop_streamlit.py` - Cliente para Streamlit Cloud con fallback a whoop_cache.json
- `whoop_sync.py` - CLI sync: `--auth`, `--all`, `--month N`
- `whoop_cache.json` - Cache de datos mensuales (commiteado al repo)

### Garmin
- `garmin_client.py` - Cliente Garmin Connect (tokens → email/password con MFA)
- `garmin_setup_auth.py` - Setup interactivo: login, guarda tokens, exporta para CI
- `garmin_auth.py` - SSO authentication con soporte MFA
- `garmin_sync.py` - CLI sync: `--all`, `--month N --year Y`
- `garmin_cache.json` - Cache de datos mensuales

### CI/CD
- `.github/workflows/whoop-sync.yml` - Cron diario 7AM Costa Rica, sync all months, actualiza tokens en GitHub Secrets
- `.github/workflows/auto-merge.yml` - Auto-merge branches `claude/**` a main

### Otros
- `auth.py`, `crypto.py` - Legacy (Supabase auth, no se usa actualmente)
- `style_demo.py`, `preview_*.html`, `screenshot_*.png` - Demo de 4 temas de diseño
- `.streamlit/config.toml` - Tema Dark Neon (cyan #06b6d4, fondo #0a0a0f)
- `.streamlit/secrets.toml` - Credenciales locales (NO commitear, en .gitignore)

## 9 Métricas trackeadas

| Métrica | Fuente | Tipo | Meta default |
|---------|--------|------|-------------|
| Steps Daily Avg | Garmin | promedio | 10,000 |
| Activities/Mes | Garmin | total | 28 |
| Strength Training | Garmin | total | 10 |
| HR Zones 1-3 | WHOOP | total (hrs) | 19.3 |
| HR Zones 4-5 | WHOOP | total (hrs) | 2.9 |
| Sleep Duration | WHOOP | promedio (hrs) | 7.5 |
| Recovery Score | WHOOP | promedio (%) | 50% |
| Resting HR | WHOOP | promedio_inverted (bpm) | 55 |
| Sleep Consistency | WHOOP | promedio (%) | 80% |

## Decisiones tomadas

- **Config hierarchy:** env vars (CI) > Streamlit secrets (cloud) > secrets.toml (terminal) - arreglado para que scripts de terminal lean TOML directamente
- **Cache protection:** No sobreescribir cache con datos vacíos de API
- **Error propagation:** Errores de API propagan para que workflow de CI falle visiblemente
- **Naps excluidos:** Promedios de sueño solo cuentan noches, no siestas
- **HR Zones de cycles:** Se usan cycles endpoint en vez de solo workouts para HR zones completas
- **Dark Neon theme:** Seleccionado como tema definitivo del dashboard
- **Goals local:** Migrado de Supabase auth a JSON local (simplificación)
- **Auto-merge:** Branches `claude/*` se mergean automáticamente a main

## Reglas de sesión

1. **Guardar contexto antes de compresión:** Cuando el contexto llegue al 70% de capacidad, antes de comprimir, guardar un resumen en la sección "Última sesión" de este archivo con:
   - Qué estábamos haciendo
   - Qué archivos tocamos
   - Qué decisiones tomamos
   - Próximos pasos

2. **Actualizar después de cambios relevantes:** Después de cada cambio relevante de código o decisión importante, actualizar la sección "Última sesión" de este archivo.

## Última sesión

**Fecha:** 2026-03-18
**Qué hicimos:**
- Resolvimos la causa raíz del Garmin OAuth1 401 Unauthorized
- garth 0.7.9 (lanzado 18-mar-2026) corrigió mismatch iOS→Android en los identificadores OAuth1
- garth 0.4.47 tenía este bug; 0.5+ requiere Python 3.10+
- Creamos `garmin_setup_auth.py` para setup interactivo de auth
- Simplificamos `garmin_client.py` (eliminados workarounds y debug helpers)
- Eliminamos scripts de diagnóstico (`garmin_debug.py`, `garmin_signing_test.py`, `garmin_curl_test.py`)

**Próximos pasos para Antonio:**
1. `brew install python@3.12`
2. `python3.12 -m pip install garth>=0.7.9 garminconnect requests`
3. `python3.12 garmin_setup_auth.py` (login interactivo, guarda tokens)
4. `python3.12 garmin_setup_auth.py --export` (exportar tokens para GitHub Secrets)
5. `python3.12 garmin_sync.py` (sincronizar datos)
