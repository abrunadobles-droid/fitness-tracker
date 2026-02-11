# 🚀 GUÍA DE INICIO RÁPIDO
## Para Antonio - Paso a Paso

## ⚡ INSTALACIÓN EN 3 PASOS

### 1️⃣ Copiar archivos a tu Mac

Copia toda la carpeta `fitness_tracker` a tu escritorio:
```
/Users/AntonioXBruna/Desktop/fitness_tracker/
```

### 2️⃣ Configurar credenciales Garmin

Edita `config.py` y agrega:
```python
GARMIN_CONFIG = {
    'email': 'tu_email@ejemplo.com',      # ← TU EMAIL
    'password': 'tu_password_de_garmin'   # ← TU PASSWORD
}
```

### 3️⃣ Ejecutar setup

```bash
cd /Users/AntonioXBruna/Desktop/fitness_tracker
python3 setup.py
```

¡Eso es todo! El script de setup hará el resto.

---

## 🎯 USO DIARIO

### Opción 1: Ver estadísticas de HOY
```bash
cd /Users/AntonioXBruna/Desktop/fitness_tracker
python3 tracker_updater.py
```

Esto te muestra:
- Recovery de WHOOP
- HRV, Resting HR
- Sueño
- Pasos
- Calorías
- Distancia

### Opción 2: Actualizar Excel
```bash
cd /Users/AntonioXBruna/Desktop/fitness_tracker
python3 tracker_updater.py update
```

Esto:
1. Obtiene datos del mes actual
2. Te muestra qué va a actualizar
3. Te pide confirmación
4. Actualiza el Excel

---

## 🔐 AUTENTICACIÓN WHOOP (Solo 1ra vez)

La primera vez que uses WHOOP:

```bash
python3 whoop_client.py
```

Esto va a:
1. Abrir tu navegador automáticamente
2. Pedirte que autorices la app en WHOOP
3. Guardar los tokens automáticamente en `whoop_tokens.json`
4. Hacer una prueba de conexión

**IMPORTANTE**: Solo necesitas hacer esto UNA VEZ. Los tokens se guardan y se renuevan automáticamente.

---

## 📊 MÉTRICAS QUE SE ACTUALIZAN

| Métrica en Excel          | Fuente      | Descripción                    |
|---------------------------|-------------|--------------------------------|
| Steps (Ave Daily)         | Garmin      | Promedio de pasos diarios      |
| Active Calories           | Garmin      | Calorías activas totales       |
| Ave Sleep Duration (H)    | WHOOP       | Promedio horas de sueño        |
| Strenght Training         | Garmin      | Sesiones de entrenamiento      |
| Activities Mes            | WHOOP       | Total de workouts registrados  |

---

## ❓ PREGUNTAS FRECUENTES

### ¿Qué pasó con el problema de WHOOP?

**RESUELTO** ✅

El problema era que el token no tenía los "scopes" (permisos) correctos. 

La nueva solución:
- Genera automáticamente la URL con TODOS los scopes necesarios
- Maneja todo el flujo OAuth2 automáticamente
- Guarda y renueva tokens automáticamente
- No más errores 401/404

### ¿Tengo que autenticarme cada vez?

**NO**. Solo la primera vez.

- WHOOP: Los tokens se guardan en `whoop_tokens.json` y se renuevan automáticamente
- Garmin: El login se hace automáticamente con email/password de config.py

### ¿Puedo ejecutarlo automáticamente cada día?

**SÍ**. Puedes crear un cronjob en macOS:

```bash
# Editar crontab
crontab -e

# Agregar esta línea para ejecutar todos los días a las 11 PM
0 23 * * * cd /Users/AntonioXBruna/Desktop/fitness_tracker && /usr/bin/python3 tracker_updater.py update
```

### ¿Qué pasa si cambio de computadora?

Solo necesitas copiar:
1. La carpeta `fitness_tracker` completa
2. El archivo `whoop_tokens.json` (para no volver a autenticar)

### ¿Puedo ver más detalles de un día específico?

Sí, edita `tracker_updater.py` y en la función `get_current_stats()` puedes cambiar la fecha.

---

## 🛠️ SOLUCIÓN DE PROBLEMAS RÁPIDA

### Error: "No module named 'garminconnect'"
```bash
pip3 install garminconnect --break-system-packages
```

### Error: "FileNotFoundError" con Excel
Actualiza la ruta en `config.py`:
```python
EXCEL_FILE = '/ruta/correcta/a/tu/archivo.xlsx'
```

### WHOOP: "Authorization was not valid"
```bash
rm whoop_tokens.json
python3 whoop_client.py
```
Vuelve a autorizar la app.

### Garmin: "Authentication failed"
Verifica email y password en `config.py`

---

## 📞 COMANDOS DE EMERGENCIA

Ver solo stats de WHOOP:
```bash
python3 whoop_client.py
```

Ver solo stats de Garmin:
```bash
python3 garmin_client.py
```

Volver a autenticar WHOOP desde cero:
```bash
rm whoop_tokens.json
python3 whoop_client.py
```

---

## ✅ CHECKLIST POST-INSTALACIÓN

- [ ] Carpeta copiada a Desktop
- [ ] config.py editado con credenciales Garmin
- [ ] setup.py ejecutado exitosamente
- [ ] WHOOP autenticado (whoop_tokens.json creado)
- [ ] Garmin probado y funcionando
- [ ] Excel actualizado con datos del mes actual

---

## 🎉 ¡LISTO!

Ya tienes tu tracker automatizado funcionando.

Comandos que vas a usar frecuentemente:
```bash
# Ver stats de hoy
python3 tracker_updater.py

# Actualizar Excel del mes actual
python3 tracker_updater.py update
```

¡Disfruta! 🏃‍♂️💪
