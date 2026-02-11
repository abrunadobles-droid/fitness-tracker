"""
Autenticación WHOOP con OAuth2
"""

import requests
import secrets
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlencode, parse_qs
import config

WHOOP_TOKENS_FILE = 'whoop_tokens.json'

class CallbackHandler(BaseHTTPRequestHandler):
    auth_code = None
    
    def do_GET(self):
        query = parse_qs(self.path.split('?')[1] if '?' in self.path else '')
        
        if 'code' in query:
            CallbackHandler.auth_code = query['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Autorizacion exitosa!</h1><p>Puedes cerrar esta ventana.</p></body></html>')
        elif 'error' in query:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error_msg = query.get('error', ['unknown'])[0]
            self.wfile.write(f'<html><body><h1>Error: {error_msg}</h1></body></html>'.encode())
        
    def log_message(self, format, *args):
        pass

class WhoopAuth:
    def __init__(self):
        self.client_id = config.WHOOP_CLIENT_ID
        self.client_secret = config.WHOOP_CLIENT_SECRET
        self.redirect_uri = config.WHOOP_REDIRECT_URI
        self.scopes = 'offline read:recovery read:sleep read:workout read:cycles read:profile'
        self.tokens = self._load_tokens()
    
    def _load_tokens(self):
        if os.path.exists(WHOOP_TOKENS_FILE):
            with open(WHOOP_TOKENS_FILE, 'r') as f:
                return json.load(f)
        return None
    
    def _save_tokens(self, tokens):
        with open(WHOOP_TOKENS_FILE, 'w') as f:
            json.dump(tokens, f)
        self.tokens = tokens
    
    def get_authorization_url(self):
        state = secrets.token_urlsafe(16)
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scopes,
            'state': state
        }
        return f"https://api.prod.whoop.com/oauth/oauth2/auth?{urlencode(params)}"
    
    def authorize(self):
        auth_url = self.get_authorization_url()
        
        print("\n" + "="*60)
        print("AUTENTICACIÓN WHOOP")
        print("="*60)
        print("\n1. Se abrirá tu navegador automáticamente")
        print("2. Inicia sesión en WHOOP si es necesario")
        print("3. Autoriza la aplicación")
        print(f"\nSi no se abre automáticamente, usa esta URL:\n{auth_url}\n")
        
        webbrowser.open(auth_url)
        
        print("Esperando autorización...")
        
        server = HTTPServer(('localhost', 8000), CallbackHandler)
        server.handle_request()
        
        if CallbackHandler.auth_code:
            print("\n✅ Autenticación exitosa!")
            print(f"Access token guardado en: {WHOOP_TOKENS_FILE}\n")
            tokens = self._exchange_code_for_tokens(CallbackHandler.auth_code)
            self._save_tokens(tokens)
            return tokens
        else:
            raise Exception("No se recibió código de autorización")
    
    def _exchange_code_for_tokens(self, code):
        url = "https://api.prod.whoop.com/oauth/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri
        }
        
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def refresh_access_token(self):
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
        return new_tokens
    
    def get_access_token(self):
        if not self.tokens:
            raise Exception("No hay tokens. Ejecuta authorize() primero.")
        return self.tokens['access_token']
    
    def is_authenticated(self):
        return self.tokens is not None and 'access_token' in self.tokens
