# Arreglar la función de refresh en whoop_auth.py

with open('whoop_auth.py', 'r') as f:
    content = f.read()

# Encontrar y reemplazar la función refresh_access_token
old_func = '''    def refresh_access_token(self):
        if not self.tokens or 'refresh_token' not in self.tokens:
            raise Exception("No hay refresh token disponible. Ejecuta authorize() primero.")
        
        url = 'https://api.prod.whoop.com/oauth/oauth2/token'
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.tokens['refresh_token'],
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(url, json=data)
        response.raise_for_status()
        
        new_tokens = response.json()
        self._save_tokens(new_tokens)
        return new_tokens'''

new_func = '''    def refresh_access_token(self):
        if not self.tokens or 'refresh_token' not in self.tokens:
            raise Exception("No hay refresh token disponible. Ejecuta authorize() primero.")
        
        url = 'https://api.prod.whoop.com/oauth/oauth2/token'
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.tokens['refresh_token'],
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        new_tokens = response.json()
        self._save_tokens(new_tokens)
        return new_tokens'''

content = content.replace(old_func, new_func)

with open('whoop_auth.py', 'w') as f:
    f.write(content)

print("✅ Refresh token arreglado - ahora se renovará automáticamente cada hora")
