# Fitness Tracker Automatizado

Dashboard personal de fitness que sincroniza datos de WHOOP y Garmin Connect, los presenta en un dashboard Streamlit con tema Dark Neon, y trackea progreso mensual contra metas personalizables.

**Usuario:** Antonio (macOS, MacBook Pro)
**Idioma:** Español (interfaz y documentación)

## Environment

- User's machine is macOS (MacBook Pro)
- **Python venv:** `.venv/` en el root del proyecto (Python 3.12 via Homebrew)
- Activar siempre: `source .venv/bin/activate` antes de cualquier comando
- Python 3.12 está en `/opt/homebrew/bin/python3.12` (NO está en PATH por default)
- El system Python es 3.9 — NO usar, garth moderno requiere >= 3.10
- garminconnect >= 0.3.1 (usa curl_cffi para bypass Cloudflare)
- garth está DEPRECADO pero garminconnect lo usa internamente

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
- `garmin_client.py` - Cliente Garmin Connect (garminconnect 0.3.1, token persistence en ~/.garmin_tokens/)
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
- **Dark Neon theme:** Seleccionado como tema definitivo del dashboard
- **Goals local:** Migrado de Supabase auth a JSON local (simplificación)
- **Auto-merge:** Branches `claude/*` se mergean automáticamente a main
- **Venv obligatorio:** Usar siempre `.venv/` (Python 3.12). System Python 3.9 no sirve.
- **HR Zones de workouts:** API v2 de WHOOP tiene `zone_durations` en workouts, NO en cycles
- **Garmin token persistence:** Una vez logueado, tokens en `~/.garmin_tokens/` se refrescan sin tocar SSO (sin 429)
- **Garmin fail-fast:** data_loader no intenta Garmin live si no hay tokens guardados
- **Garmin browser fallback:** Si garmin_sync.py da 429, se puede extraer data desde Chrome con sesión activa usando gc-api + CSRF token (ver Troubleshooting)

## Reglas de sesión

1. **Guardar contexto antes de compresión:** Cuando el contexto llegue al 70% de capacidad, antes de comprimir, guardar un resumen en la sección "Última sesión" de este archivo con:
   - Qué estábamos haciendo
   - Qué archivos tocamos
   - Qué decisiones tomamos
   - Próximos pasos

2. **Actualizar después de cambios relevantes:** Después de cada cambio relevante de código o decisión importante, actualizar la sección "Última sesión" de este archivo.

## Troubleshooting

### WHOOP tokens expirados
```bash
source .venv/bin/activate && python whoop_sync.py --auth
# Abre browser, login en WHOOP, autorizar app
# Luego: python whoop_sync.py --all
```
Si el refresh token aún funciona (expiran en ~6 meses), el sync los renueva automáticamente.

### Garmin 429 (Too Many Requests)
Garmin bloquea login programático si se intentó muchas veces. El bloqueo dura horas/días.

**Solución 1: Esperar y reintentar**
```bash
source .venv/bin/activate && python garmin_sync.py --all
```

**Solución 2: Extraer data desde Chrome (bypass 429)**
El browser NO está bloqueado — solo el login programático. Pasos:
1. Estar logueado en https://connect.garmin.com en Chrome
2. Navegar a la página Daily Summary
3. Abrir DevTools Console (F12)
4. La API interna usa: `/gc-api/usersummary-service/usersummary/daily/{username}?calendarDate=YYYY-MM-DD`
5. Headers requeridos: `NK: NT` + `Connect-Csrf-Token` (capturar de network tab)
6. Claude Code con Chrome MCP puede automatizar esto completamente

**Solución 3: Service ticket desde browser**
1. Navegar a: `https://sso.garmin.com/sso/embed?clientId=GarminConnect&locale=en&consumeServiceTicket=false`
2. Si estás logueado, redirige a URL con `?ticket=ST-xxxxx`
3. Ese ticket se puede usar para generar tokens OAuth

### HR Zones muestran 0.0h
- WHOOP API v2: `zone_durations` está en **workouts** (`activity/workout`), NO en cycles (`cycle`)
- Verificar que `whoop_client_v2_corrected.py` y `whoop_streamlit.py` buscan zones en workouts

### Dashboard se cuelga al cargar
- Probablemente `data_loader.py` está intentando Garmin live API sin tokens
- `data_loader.py` tiene guard `_garmin_has_tokens()` que evita esto
- Si se quitó el guard, re-agregar: no intentar login sin `~/.garmin_tokens/`

### Python: garth no instala o da error
- **NO usar system Python 3.9** — garth >= 0.5 requiere Python >= 3.10
- Usar siempre: `source .venv/bin/activate` (Python 3.12)
- El venv está en `.venv/` creado con `/opt/homebrew/bin/python3.12`
- Para recrear: `/opt/homebrew/bin/python3.12 -m venv .venv && source .venv/bin/activate && pip install garth garminconnect requests streamlit`

## Última sesión

**Fecha:** 2026-05-07
**Qué hicimos:**
- Diagnóstico: cron diario fallando 30 días seguidos. Causas raíz:
  1. `WHOOP_TOKENS_JSON` secret corrupto (refresh token expirado)
  2. `GARMIN_TOKENS_JSON` inválido + `GARMIN_EMAIL/PASSWORD` vacíos
  3. Cualquier falla cascadaba — workflow exit 1 saltaba el commit
  4. `GITHUB_TOKEN` faltaba `contents: write` (push 403)
  5. `GH_PAT` expirado (ya no rota tokens automáticamente)
- Re-auth WHOOP en browser → tokens nuevos guardados en `whoop_tokens.json`
- WHOOP cache resincronizado: 5 meses (ene-may 2026), mayo con 7 noches
- `WHOOP_TOKENS_JSON` secret actualizado en GitHub
- Workflow `.github/workflows/whoop-sync.yml` rediseñado:
  - `permissions: contents: write` para que pueda commitear
  - `continue-on-error: true` en cada sync y cada save-tokens
  - `if: always()` en commit step
  - Job solo falla si **ambos** syncs caen
- Workflow validado: corre verde end-to-end (Garmin no sync, pero no bloquea WHOOP)

**Estado actual:**
- WHOOP: ✅ funcionando (tokens válidos por ~6 meses, cache hasta mayo)
- Garmin: ⚠️ cache fijo en abr-2026 (ene-abr OK, no mayo) — falta re-auth
- Cron diario: ✅ verde, commitea cache de WHOOP automáticamente
- `GH_PAT`: ⚠️ expirado, no es crítico — solo significa que cuando el WHOOP refresh token rote, hay que actualizar el secret manualmente

**Pendiente (próxima sesión):**
- Re-auth Garmin: necesita o credenciales (`GARMIN_EMAIL`/`PASSWORD` como secrets) o tokens generados desde browser. Opción más simple: generar tokens localmente con `garminconnect` y subirlos como `GARMIN_TOKENS_JSON`.
- Renovar `GH_PAT` si quieres que el workflow auto-actualice los tokens (sin esto, hay que correr `whoop_sync.py --auth` manualmente cuando expiren).

**Para sincronizar datos futuros:**
```bash
source .venv/bin/activate
python whoop_sync.py --all    # WHOOP — el cron lo hace solo a 7AM CR
python garmin_sync.py --all   # Garmin — requiere tokens en ~/.garmin_tokens/
```
