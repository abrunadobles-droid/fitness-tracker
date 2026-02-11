# Agregar meditation al filtro

with open('garmin_client.py', 'r') as f:
    content = f.read()

# Actualizar filtro
old_filter = "if 'breath' in activity_type:"
new_filter = "if 'breath' in activity_type or 'meditation' in activity_type:"

content = content.replace(old_filter, new_filter)

with open('garmin_client.py', 'w') as f:
    f.write(content)

print("✅ Filtro actualizado: ahora ignora breathwork Y meditation")
