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

## 11 Métricas trackeadas

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
| Meditación (días) | WHOOP | total (días/mes) | 20 |
| Sauna (días) | WHOOP | total (días/mes) | 8 |

Las últimas dos cuentan **días distintos del mes** con ≥1 workout de WHOOP cuyo `sport_name` contiene "meditation"/"sauna" (fecha local vía `timezone_offset`). Verificar nombres reales con `python whoop_sync.py --sports`.

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

## Expediente médico / Asistente de salud

Antonio también usa este repo como memoria de su información de salud (laboratorios, presión arterial, VO2max, medicamentos, nutrición). **Leer `medical/INSTRUCCIONES_ASISTENTE.md` en cualquier sesión que toque temas de salud, exámenes o biomarcadores.** Resumen de reglas:

- No reemplazar a los médicos. Separar siempre: resultado objetivo / interpretación médica documentada / recomendación médica / inferencia de Claude.
- No inventar resultados. Documento original > historial. Rangos del laboratorio primero.
- Tendencias, no reacciones a una medición aislada.
- Historial maestro en `medical/HISTORIAL_MEDICO.md` (**gitignored, el repo es público**). Actualizarlo con cada dato nuevo usando la tabla `FECHA | RESULTADO | CAMBIO VS ANTERIOR | RANGO LAB | TENDENCIA`.
- Originales en iCloud Drive → carpeta `MEDICO` (`~/Library/Mobile Documents/com~apple~CloudDocs/MEDICO/`), accesible solo cuando Claude Code corre en la Mac.
- **Nunca commitear datos personales de salud** mientras el repo sea público.

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

**Fecha:** 2026-09-07 (parte 2)
**Qué hicimos:**
- Antonio ya creó `WHOOP_CLIENT_SECRET`, re-autorizó y resincronizó (commit "Resync WHOOP"). El cron de las 21:47 UTC volvió a modificar `whoop_cache.json` → **el sync automático de WHOOP funciona de nuevo.** Cache completo ene–sep 2026.
- Pregunta de Antonio: por qué cayó tanto el tiempo en zonas 4-5. Con el cache (solo resumen mensual) se ve la tendencia: 3.3h ene → pico 5.9h may → 2.7h jun → 1.5h jul → 0.5h ago, con zonas 1-3 y # workouts estables (~54/mes). También subió el RHR (47.5 → 52-54) y bajó el HRV (103 → 65-75) desde mayo. Para saber *qué* deportes dejaron de aportar zona 4-5 hace falta detalle por workout, que el cache no guarda.
- **Nuevo comando de diagnóstico** en `whoop_sync.py`: `--zones` (tabla por mes con z1-3, z4-5, HR máx promedio/pico de los workouts y top deportes por zona 4-5, más totales por deporte del año) y `--zones --month N` (detalle workout por workout). Imprime el `max_heart_rate` del perfil de WHOOP (`user/measurement/body`), porque las zonas son % de ese valor (Z4 = 80-90%, Z5 = 90-100%): si cambió, el mismo esfuerzo cae en otra zona.
- Hipótesis a verificar con `--zones`: (a) menos cardio intenso / más fuerza-sauna-meditación desde junio; (b) WHOOP subió el HR máximo del perfil (los workouts siguen llegando a ~170+ bpm pero ya no cuentan como Z4); (c) cardio a menor intensidad (HR máx pico mensual baja junto con las zonas).

- **Análisis del export oficial de WHOOP** (zip con `workouts.csv`, `physiological_cycles.csv`, `sleeps.csv`, `journal_entries.csv`, ene-2024 → sep-2026; NO se commitea, es data personal). Conclusiones:
  1. **El umbral de zonas NO cambió**: en todos los meses la zona 4 arranca en ~170 bpm (HR máx de perfil ≈ 212-214). Descartada la hipótesis (b).
  2. **Toda la zona 4-5 de 2026 viene del running** (Running + Trail Running). Weightlifting, Activity, Walking, etc. aportan ~0.
  3. **Corres igual de seguido (11-12/mes) pero a menor intensidad**: HR promedio en carrera 151 (may) → 143 (jun) → 136 (ago); % del tiempo de carrera en zona 4: 25% (abr-may) → 15% (jun) → 2% (ago). Abr-may tuvo 3-4 carreras ≥150 min y tempos con 50-77% en zona 4; agosto tiene 3 carreras ≥150 min pero todas en zona 1-2.
  4. No parece "mejor fitness a igual ritmo": desde mayo el RHR subió (47.5 → 52-54) y el HRV bajó (103 → 63-76), Day Strain bajó (13 → 10.5). Cambios concurrentes en el journal: dejó la creatina (30/30 jun → 0 jul-ago), 10 días de viaje en julio, cafeína casi cero en julio, niño en el cuarto 25/31 en agosto. No hay pace en el export ni en el cache de Garmin para confirmar ritmo.
  5. Perspectiva: 2025 entero estuvo en 0.4-2.6h/mes; abr-may 2026 fue el pico histórico del running, no agosto la anomalía. En 2024 la zona 4-5 (4-10h/mes) venía de Pádel/Paddle Tennis (52h en el año), no de running.
- Dato: el export de WHOOP NO incluye Meditation/Sauna (ene: 33 workouts en el csv vs 66 en la API), pero las horas de zonas coinciden con el cache (±0.1h).

- **Hipótesis de Antonio: el mensaje in-app "we recently improved heart rate accuracy".** Según búsqueda web (no pude leer los artículos, red bloqueada): WHOOP publicó una revisión mayor del algoritmo de HR en **febrero 2026** (running: mejor separación señal/ruido de movimiento, menos picos espurios) y otra el **6 de julio de 2026** (pesas, functional fitness, HIIT, ciclismo, golf). Fuentes: the5krunner.com/2026/02/28 y /2026/07/31, whoop.com/thelocker/improving-heart-rate-accuracy. La data histórica NO se recalcula.
  - Evidencia en la data de Antonio: los picos de HR máx ≥195 (16 casos abr-2025 → 2-jun-2026, incluyendo 200 bpm en Weightlifting y 202 en Activity, claros artefactos) **desaparecen del todo después del 2 de junio de 2026**; el techo de HR máx en carrera bajó de 195-203 a 178-185. Las pesas NO bajaron de HR (subieron: HR máx prom 137 → 148 → 157 jun→ago→sep, consistente con el update de julio). Escalón de HR en carrera en la semana del 9 de junio.
  - Pero el update NO explica agosto por sí solo: en julio (9, 11, 13) WHOOP siguió registrando 23-53% de zona 4 en carreras duras (HR prom 152-157). Agosto simplemente tiene carreras con HR prom 117-147 (ninguna dura).
  - Conclusión: los 25% de zona 4 de abr-may probablemente estaban algo inflados por artefactos (cadence lock), y además desde junio corres más suave. Dos causas superpuestas; la proporción exacta no se puede sacar solo de WHOOP.
- **Nuevo comando** `garmin_sync.py --runs [--month N] [--year Y]`: lista carreras según Garmin (min, km, pace, HR avg/max de su propio sensor, cadencia, desnivel). Es la prueba definitiva: comparar HR de Garmin vs WHOOP para las mismas carreras de mayo y agosto. Si Garmin también baja → real; si Garmin se mantiene y WHOOP baja → algoritmo.

**Pendiente (Antonio, en la Mac):**
```bash
source .venv/bin/activate
python garmin_sync.py --runs --month 5   # HR y pace reales de mayo
python garmin_sync.py --runs --month 8   # HR y pace reales de agosto
```
Y en la app de WHOOP: Settings → Profile → ver el "Max HR" y si el update aparece con fecha en "What's New".

- **Cierre del tema (Antonio confirma):** "un poco de todo": ene-may las zonas 4-5 le parecían muy altas incluso en fondos (artefacto), y desde junio bajó el entrenamiento (viajes en julio, retomando fondos en agosto). Benchmark de longevidad: Attia = ~4h/sem de zona 2 (3 sesiones) + 1 sesión/sem de VO2max tipo 4x4 (≈16-20 min/sem en Z4-5 ≈ 1.2-1.5h/mes); Seiler 80/20 por sesiones. La meta de 2.9h/mes equivale a ~2 sesiones 4x4 por semana, más de lo que Attia pide; 1.5h/mes ya cumple. Semanal real de Antonio (WHOOP Z4-5 min/sem): ene-mar ~40, abr-may 67-79, jun 37, jul 20, ago 6, sep 18. Z2-3 h/sem: 1.6-3.2 (por debajo de las 3-4h de Attia).

- **Meta definida por Antonio: 30 min/semana de zona 4-5** → `goals.json` `hr_zone_4_5` = 2.2 h/mes (antes 2.9).
- **CORRECCIÓN importante:** WHOOP NO calcula las zonas como % del HR máximo sino con **reserva cardíaca (Karvonen)**: zona = RHR + %·(MaxHR − RHR), con Z1 40%, Z2 60%, Z3 70%, Z4 80%, Z5 90%. Perfil real de Antonio (screenshot app): RHR baseline 51, MaxHR 195 → Z1 109, Z2 138, Z3 153, **Z4 167**, **Z5 182**. Eso coincide exactamente con el umbral ~167-171 inferido de la data; el "máximo ≈ 212" que deduje antes era un artefacto de la fórmula equivocada. El 195 no es reciente: los workouts de todo el año son consistentes con él. Nota: 167 bpm es el 86% del máximo y 182 el 93%, así que la zona 4-5 de WHOOP es más exigente que un "80% del máximo" simple; un 4x4 al 90-95% (176-185 bpm) cuenta entero. Como el RHR baseline se ajusta solo, los umbrales se mueven ±2 bpm mes a mes (RHR 47.5 en mayo → Z4 165.5; RHR 54.5 en julio → Z4 167). Los workouts viejos no se recalculan.
- `whoop_sync.py --zones` corregido: ahora estima el RHR baseline (promedio de recovery 30 días) y muestra los umbrales con la fórmula de reserva cardíaca.
- Con el umbral real, semanas que cumplían 30 min: ene-jun sí; jul (20), ago (6), sep (18) no.

- **Análisis strain/entreno/sueño → recovery** (export, deltas vs baseline propio de 28 días, era running abr-2025→sep-2026, 522 ciclos). Nota: en el export el "Cycle start time" es la noche anterior; el strain del ciclo es del día siguiente. Hallazgos:
  1. Strain diario hasta ~16 no cuesta recovery. 16-19: −6 pts; ≥19: −13 pts, HRV −9 ms, RHR +3.
  2. **Los fondos ≥120 min cuestan −14 de recovery al día siguiente** (28% de rojos), HRV −9, RHR +3; rebote +8 al día +2. Las **carreras duras <120 min con ≥15 min Z4-5 no cuestan nada** (+1), igual que las pesas (+1). La intensidad sale gratis, la duración no → la meta de 30 min Z4-5 conviene hacerla en sesiones cortas, no en fondos.
  3. Los fondos son los sábados (19 de 25). El sábado por la mañana es la **peor recovery de la semana (53)** porque la noche del viernes es la más corta (6.6h). Mejor día: miércoles (69).
  4. Entrena igual con recovery roja que verde (strain 11.3 vs 12.8; 26% de días rojos con strain ≥14; fondo/dura en 18% de rojos vs 8% de verdes).
  5. Sueño <5.5h: −19 recovery. Dormirse después de 23:30: −11. ≥7.5h: +4. Duro→duro: −6.
  6. Volumen semanal vs HRV de la semana siguiente: sin señal clara (n chico).

**Pendiente (Antonio):** decidir si la meta de 2.9h/mes de zona 4-5 sigue vigente. Para cumplirla con 12 carreras/mes hacen falta ~15 min de zona 4 por carrera (1-2 sesiones de tempo/intervalos por semana, como el 5 y 12 de mayo). Opcional: `python whoop_sync.py --zones` reproduce este análisis desde la API.

---

**Sesión anterior — Fecha:** 2026-09-07
**Qué hicimos:**
- Antonio reportó HR Zones en 0 en el dashboard. Causa directa: `whoop_cache.json` no tiene 2026-08 ni 2026-09 (todo sigue con `synced_at` 2026-07-09, el último sync local). El cron falla en WHOOP todos los días desde junio con `401` en `oauth/oauth2/token`; Garmin sí sincroniza a diario.
- **Causa raíz nueva (confirmada en logs de Actions):** el secret `WHOOP_CLIENT_SECRET` de GitHub **no existe / está vacío**. En el header `env:` del step "Run WHOOP sync" aparece `WHOOP_CLIENT_SECRET:` sin `***`, tanto en el run del 2026-09-06 como en el del 2026-06-09 (el último que "funcionó"). WHOOP exige `client_secret` en el refresh → sin él el refresh SIEMPRE da 401 aunque el refresh token sea válido. El run del 09-jun pasó solo porque el access token recién subido aún no había expirado (dura ~1h); al día siguiente ya necesitaba refresh y murió. Esto explica por qué cada re-auth "duraba un día".
- La teoría anterior (dashboard rotando el refresh token) pudo contribuir, pero sin `WHOOP_CLIENT_SECRET` en CI nada funciona: **hay que crear ese secret primero**.
- Tocado: `whoop_auth.py` (refresh lanza error claro si client_secret vacío), `whoop_sync.py` (sale con exit 1 y mensaje si `WHOOP_CLIENT_SECRET` vacío, antes de tocar la API), `.github/workflows/whoop-sync.yml` (mensaje `::error::` menciona el secret).
- Dato: `GH_PAT` sigue funcionando (el step "Save updated Garmin tokens" hace `gh secret set` OK a diario).

**Pendiente (Antonio, en la Mac) — en este orden:**
```bash
source .venv/bin/activate
# 1. Crear el secret que falta (valor en .streamlit/secrets.toml → [whoop] client_secret)
gh secret set WHOOP_CLIENT_SECRET --body "PEGAR_CLIENT_SECRET_AQUI"
# 2. Re-autorizar WHOOP y resincronizar
python whoop_sync.py --auth
python whoop_sync.py --all
# 3. Subir tokens DESPUÉS del --all (el sync puede rotar el refresh token)
gh secret set WHOOP_TOKENS_JSON --body "$(cat whoop_tokens.json)"
git add whoop_cache.json && git commit -m "Resync WHOOP" && git push
# 4. Verificar: correr el workflow a mano dos veces con >1h de diferencia (la 2da fuerza refresh)
gh workflow run whoop-sync.yml
```
El paso 4 es la prueba real: si el segundo run pasa, el refresh con client_secret funciona y el cron queda estable.

---

**Sesión anterior — Fecha:** 2026-07-09 (parte 2)
**Qué hicimos:**
- **Nuevas métricas: Meditación (días/mes) y Sauna (días/mes) desde WHOOP.** Se cuentan días distintos con ≥1 workout cuyo `sport_name` contiene "meditation"/"sauna" (fecha local por `timezone_offset`, cubre "Infrared Sauna").
- Tocado: `constants.py` (RECOVERY_METRICS + DASHBOARD_METRICS), `whoop_client_v2_corrected.py` (conteo + helpers), `whoop_sync.py` (campos en cache + comando `--sports` para listar sport_names reales), `whoop_streamlit.py` (live), `data_loader.py`, `helpers.py`, `goals_setup.py` (metas default: meditación 20, sauna 8 + sección en form), `views/mes_actual.py` (sección RECOVERY HABITS + ritmo días/semana), `views/historico.py`, `pdf_export.py`.
- El cache viejo no tiene los campos nuevos → muestran 0 hasta el próximo sync. El cron diario hace `--all` (todo 2026), así que se backfillea solo; o manual: `python whoop_sync.py --all`.
- Nota: estas métricas son independientes del log manual de meditación de la pestaña Mente (`meditation_log.json`); posible unificación futura.

---

**Sesión anterior — Fecha:** 2026-07-09
**Qué hicimos:**
- Diagnóstico de "datos de junio no coinciden con la app de WHOOP": el cache de WHOOP está congelado desde el 2026-06-09 (junio = solo 9 noches / 15 workouts, la primera semana). El cron falla con 401 en el refresh de WHOOP desde el 10 de junio, pero salía verde.
- Tres causas encontradas:
  1. `whoop_sync.py` hacía `return` (exit 0) con tokens muertos → el step de CI salía "success" y ni el guard "ambos fallaron" podía dispararse. **Fix:** ahora `sys.exit(1)`.
  2. El workflow solo fallaba si AMBOS syncs fallaban. **Fix:** ahora falla si falla CUALQUIERA, con `::error::` indicando cuál.
  3. Causa raíz del 401: WHOOP rota el refresh token en cada refresh. `whoop_streamlit.py` (dashboard) refrescaba y guardaba el token nuevo solo en `st.session_state` (efímero) → invalidaba la copia del secret del cron. **Fix:** el dashboard ya NO refresca nunca; si el access token expiró, cae al cache. El cron de CI es el único dueño del refresh token.
- Además: los steps "Save tokens" ahora solo corren si el sync fue exitoso (antes re-subían tokens muertos al secret en cada run fallido). Y `whoop_sync.py` avisa al final si el run local rotó el token (hay que actualizar el secret con `gh secret set WHOOP_TOKENS_JSON`).
- Dato: `GH_PAT` SÍ funciona actualmente (los `gh secret set` del cron pasan) — la nota anterior de que estaba expirado ya no aplica.

**Estado actual:**
- WHOOP: ❌ tokens muertos desde 2026-06-10 — **requiere re-auth manual de Antonio** (ver pendiente). Cache OK hasta 2026-06-09.
- Garmin: ✅ cron sincroniza bien a diario (cache al día, incluye julio).
- Cron: ✅ ahora fallará visiblemente (rojo) si WHOOP o Garmin fallan.

**Pendiente (Antonio, en la Mac):**
```bash
source .venv/bin/activate
python whoop_sync.py --auth   # abre browser, re-autorizar
python whoop_sync.py --all    # resincroniza (junio completo + julio)
gh secret set WHOOP_TOKENS_JSON --body "$(cat whoop_tokens.json)"  # DESPUÉS del --all, no antes
git add whoop_cache.json && git commit -m "Resync WHOOP" && git push
```
IMPORTANTE: subir el secret DESPUÉS de `--all` (el sync puede rotar el token). Y no abrir el dashboard con tokens locales frescos antes de subir el secret.

---

**Sesión anterior — Fecha:** 2026-06-09
**Qué hicimos:**
- Diagnóstico: el cron salía "verde" pero era falso positivo (los `continue-on-error` enmascaraban que WHOOP fallaba internamente). WHOOP refresh token revocado (401), cache estancado en may-07, junio sin datos.
- Causa de fondo del WHOOP roto: el cron rota el refresh token en cada uso pero `GH_PAT` (expirado) no puede salvar el token nuevo al secret → al día siguiente carga uno ya consumido → 401.
- Re-auth WHOOP en browser (flujo OAuth localhost:8000) → tokens nuevos, secret actualizado.
- Re-auth Garmin con credenciales en `secrets.toml` (sí estaban configuradas) → login limpio SIN 429 ni MFA → tokens en `~/.garmin_tokens/`.
- Ambos caches resincronizados a 6 meses (ene-jun 2026). Junio: WHOOP 9 noches, Garmin 12,501 pasos/día.
- **Arreglado el auto-sync de Garmin en CI** (3 bugs):
  1. `garmin_client.py` ahora restaura `GARMIN_TOKENS_JSON` del env al tokenstore antes del login (mismo patrón que WHOOP, vía `_restore_tokens_from_env()`). No agrega métodos de auth nuevos.
  2. Workflow llamaba `_export_tokens_json` (inexistente) → cambiado a `GarminClient().get_tokens_json()`.
  3. `GARMIN_TOKENS_JSON` secret subido con formato correcto `{"garmin_tokens.json": {...}}`.
- Round-trip Garmin verificado localmente (export → restaurar desde env → login → fetch real data).

**Estado actual:**
- WHOOP: ✅ tokens válidos ~6 meses, cache hasta junio, cron auto-sync OK
- Garmin: ✅ tokens en `~/.garmin_tokens/` + secret en CI, cache hasta junio, cron auto-sync OK
- Cron diario: ✅ ahora sincroniza AMBAS fuentes solo
- `GH_PAT`: ⚠️ sigue expirado — los token-save steps fallan (continue-on-error, inofensivo). Garmin oauth1 dura ~1 año sin rotar, así que el secret aguanta. WHOOP refresh token rota: cuando expire (~6 meses) hay que re-auth manual con `whoop_sync.py --auth` + `gh secret set WHOOP_TOKENS_JSON`.

**Pendiente (opcional):**
- Renovar `GH_PAT` (PAT clásico, scope `repo`) y subirlo como secret para que el cron auto-rote los WHOOP tokens y no haya que re-auth manual cada ~6 meses.

**Para sincronizar datos futuros (manual, si hace falta):**
```bash
source .venv/bin/activate
python whoop_sync.py --all    # WHOOP — el cron lo hace solo a 7AM CR
python garmin_sync.py --all   # Garmin — el cron lo hace solo; usa ~/.garmin_tokens/
```
