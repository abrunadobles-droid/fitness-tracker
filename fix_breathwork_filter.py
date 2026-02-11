# Agregar filtro de breathwork en garmin_client.py

with open('garmin_client.py', 'r') as f:
    lines = f.readlines()

# Buscar la función count_strength_training y agregar filtro general
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Después de obtener activities, agregar filtro
    if 'def get_activities(self, start_date=None, end_date=None, limit=10):' in line:
        # Agregar comentario sobre filtro
        indent = '        '
        insert_at = i + 10  # Después de la definición
        
# Reescribir el archivo con filtro mejorado
with open('garmin_client.py', 'r') as f:
    content = f.read()

# Buscar y reemplazar la parte donde se filtran actividades
old_code = '''        for activity in activities:
            # Buscar actividades de tipo fuerza/resistencia
            activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
            if any(keyword in activity_type for keyword in ['strength', 'training', 'gym', 'weights']):
                strength_count += 1'''

new_code = '''        for activity in activities:
            activity_type = activity.get('activityType', {}).get('typeKey', '').lower()
            
            # Ignorar breathwork (meditación)
            if 'breath' in activity_type:
                continue
            
            # Buscar actividades de tipo fuerza/resistencia
            if any(keyword in activity_type for keyword in ['strength', 'training', 'gym', 'weights', 'weight']):
                strength_count += 1'''

if old_code in content:
    content = content.replace(old_code, new_code)
    
    with open('garmin_client.py', 'w') as f:
        f.write(content)
    
    print("✅ Filtro de breathwork agregado")
    print("   Ahora ignora automáticamente actividades de breathwork")
else:
    print("⚠️  No se encontró el código exacto, aplicando manualmente...")
    # Aplicar de forma más general
    
