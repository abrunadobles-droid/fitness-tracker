# 🏃‍♂️ Fitness Tracker Automatizado
## Integración WHOOP + Garmin Connect → Excel

Este proyecto automatiza la extracción de datos de WHOOP y Garmin Connect para actualizar tu Excel tracker de fitness y wellness.

---

## 📋 Características

- ✅ Autenticación OAuth2 con WHOOP API
- ✅ Integración con Garmin Connect
- ✅ Actualización automática de Excel
- ✅ Manejo de tokens y refresh automático
- ✅ Resúmenes mensuales
- ✅ Estadísticas diarias

---

## 🚀 Instalación Rápida

### 1. Instalar dependencias

```bash
cd /Users/AntonioXBruna/Desktop/fitness_tracker
pip install -r requirements.txt --break-system-packages
```

### 2. Configurar credenciales

Edita `config.py` y agrega tus credenciales de Garmin:

```python
GARMIN_CONFIG = {
    'email': 'tu_email@ejemplo.com',
    'password': 'tu_password'
}
```

Las credenciales de WHOOP ya están configuradas.

### 3. Configurar ruta del Excel

Asegúrate de que la ruta en `config.py` apunta a tu archivo Excel:

```python
EXCEL_FILE = '/Users/AntonioXBruna/Desktop/Data_Fitness___Wellness_Tracker.xlsx'
```

---

## 🔐 WHOOP: Solución al Problema de Scopes

### El Problema
La App WHOOP original tenía los permisos configurados pero el token no los arrastraba (error 401/404).

### La Solución
El nuevo código:

1. **Genera automáticamente la URL de autorización** con todos los scopes necesarios:
   - `offline` (para refresh token)
   - `read:recovery`
   - `read:sleep`
   - `read:workout`
   - `read:cycles`
   - `read:profile`

2. **Abre el navegador automáticamente** para que autorices la app

3. **Captura el código** de autorización mediante un servidor local

4. **Intercambia el código por tokens** y los guarda en `whoop_tokens.json`

5. **Maneja el refresh automático** cuando el token expira

### Primera autenticación WHOOP

```bash
python whoop_client.py
```

Esto:
- Abrirá tu navegador
- Te pedirá que autorices la aplicación
- Guardará los tokens automáticamente
- Hará una prueba de conexión

**IMPORTANTE**: Solo necesitas hacer esto UNA VEZ. Los tokens se guardan y se refrescan automáticamente.

---

## 📊 Uso

### Ver estadísticas del día actual

```bash
python tracker_updater.py
```

Muestra:
- Recovery score de WHOOP
- HRV, Resting HR
- Horas de sueño
- Pasos de Garmin
- Calorías activas
- Distancia

### Actualizar Excel (Dry Run)

```bash
python tracker_updater.py update
```

Esto:
1. Obtiene datos del mes actual de WHOOP y Garmin
2. Muestra qué se actualizaría
3. Te pide confirmación antes de guardar

### Pruebas individuales

Probar solo WHOOP:
```bash
python whoop_client.py
```

Probar solo Garmin:
```bash
python garmin_client.py
```

---

## 📁 Estructura del Proyecto

```
fitness_tracker/
├── config.py              # Configuración y credenciales
├── whoop_auth.py          # Autenticación OAuth2 WHOOP
├── whoop_client.py        # Cliente WHOOP API
├── garmin_client.py       # Cliente Garmin Connect
├── tracker_updater.py     # Actualizador principal Excel
├── requirements.txt       # Dependencias Python
├── whoop_tokens.json      # Tokens WHOOP (generado automáticamente)
└── README.md             # Este archivo
```

---

## 🔧 Solución de Problemas

### WHOOP: Error 401

**Problema**: "Authorization was not valid"

**Solución**: 
1. Elimina `whoop_tokens.json`
2. Ejecuta `python whoop_client.py`
3. Vuelve a autorizar la app

### Garmin: Error de autenticación

**Problema**: No puede iniciar sesión

**Solución**:
1. Verifica que email y password en `config.py` sean correctos
2. Si usas 2FA en Garmin, puede requerir pasos adicionales
3. Intenta iniciar sesión manualmente en connect.garmin.com para verificar credenciales

### Excel: No encuentra el archivo

**Problema**: `FileNotFoundError`

**Solución**: Actualiza `EXCEL_FILE` en `config.py` con la ruta correcta

### Advertencia LibreSSL en macOS

**No es un error**. Es solo una advertencia informativa de urllib3 sobre LibreSSL vs OpenSSL. No afecta el funcionamiento.

---

## 📝 Mapeo de Datos

### Desde WHOOP
- ✅ Recovery Score
- ✅ HRV (Heart Rate Variability)
- ✅ Resting Heart Rate
- ✅ Sleep Duration
- ✅ Sleep Performance
- ✅ Total Workouts (Activities Mes)

### Desde Garmin
- ✅ Daily Steps → "Steps (Ave Daily)"
- ✅ Active Calories → "Active Calories"
- ✅ Sleep Duration → "Ave Sleep Duration (H)" (si WHOOP no disponible)
- ✅ Strength Training Sessions → "Strenght Training"

---

## 🎯 Próximos Pasos / Mejoras Futuras

- [ ] Agregar validación de expiración de tokens WHOOP
- [ ] Implementar logging a archivo
- [ ] Agregar gráficas automáticas en Excel
- [ ] Crear cronjob para actualización automática diaria
- [ ] Agregar más métricas (peso, meditación, etc.)
- [ ] Dashboard web con Streamlit
- [ ] Notificaciones cuando recovery < 50%

---

## 🆘 Soporte

Si tienes problemas:

1. **Verifica tu autenticación**:
   ```bash
   python whoop_client.py
   python garmin_client.py
   ```

2. **Revisa los mensajes de error** - son descriptivos

3. **Tokens expirados**: Simplemente vuelve a ejecutar el script, se refrescan automáticamente

---

## 📧 Credenciales Actuales

### WHOOP (ya configuradas)
- Client ID: `2c927896-2dd0-4cdc-8a99-f6a3af89992a`
- Client Secret: (en config.py)
- Scopes: Todos los necesarios incluidos

### Garmin (PENDIENTE DE CONFIGURAR)
- Email: ❌ FALTA AGREGAR
- Password: ❌ FALTA AGREGAR

---

## 🎉 Diferencias con el Intento Anterior

### ❌ Antes (con la otra herramienta)
- URL de autorización manual
- Intercambio de tokens manual con curl
- Tokens hardcodeados en el código
- Sin manejo de refresh
- Error 401/404 en endpoints de salud

### ✅ Ahora (con esta solución)
- URL de autorización automática con scopes correctos
- Flujo OAuth2 completo automatizado
- Tokens guardados en archivo JSON
- Refresh automático
- Servidor local para capturar callback
- Integración completa con Excel
- Bonus: Garmin Connect también integrado

---

## 🔑 Conceptos Clave Técnicos

### OAuth2 Flow
1. **Authorization URL** → Usuario autoriza la app
2. **Authorization Code** → Código temporal recibido
3. **Token Exchange** → Código → Access Token + Refresh Token
4. **API Calls** → Access Token en header
5. **Token Refresh** → Cuando expira, usar Refresh Token

### WHOOP API Scopes
- `offline`: Permite refresh tokens
- `read:recovery`: Datos de recuperación
- `read:sleep`: Datos de sueño
- `read:workout`: Workouts
- `read:cycles`: Ciclos completos
- `read:profile`: Perfil de usuario

---

¡Listo para usar! 🚀
