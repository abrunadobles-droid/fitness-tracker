# Leer el archivo
with open('whoop_auth.py', 'r') as f:
    lines = f.readlines()

# Encontrar y reemplazar la función _exchange_code_for_tokens
new_lines = []
skip_until_next_def = False
inside_function = False

for i, line in enumerate(lines):
    if 'def _exchange_code_for_tokens(self, code):' in line:
        inside_function = True
        # Agregar la nueva versión de la función
        new_lines.append(line)
        new_lines.append('        url = "https://api.prod.whoop.com/oauth/oauth2/token"\n')
        new_lines.append('        headers = {"Content-Type": "application/x-www-form-urlencoded"}\n')
        new_lines.append('        data = {\n')
        new_lines.append('            "grant_type": "authorization_code",\n')
        new_lines.append('            "code": code,\n')
        new_lines.append('            "client_id": self.client_id,\n')
        new_lines.append('            "client_secret": self.client_secret,\n')
        new_lines.append('            "redirect_uri": self.redirect_uri\n')
        new_lines.append('        }\n')
        new_lines.append('        response = requests.post(url, headers=headers, data=data)\n')
        new_lines.append('        response.raise_for_status()\n')
        new_lines.append('        return response.json()\n')
        skip_until_next_def = True
        continue
    
    if skip_until_next_def:
        if line.strip().startswith('def ') and 'def _exchange_code_for_tokens' not in line:
            skip_until_next_def = False
            new_lines.append('\n')
            new_lines.append(line)
        continue
    
    new_lines.append(line)

# Guardar
with open('whoop_auth.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Función de intercambio actualizada!")
