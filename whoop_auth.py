"""
Módulo de autenticación para WHOOP API
Maneja OAuth2 flow y refresh de tokens
"""

import json
import os
import webbrowser
import secrets
from urllib.parse import urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from config import WHOOP_CONFIG, WHOOP_TOKENS_FILE


class CallbackHandler(BaseHTTPRequestHandler):
    """Maneja el callback de OAuth"""
    auth_code = None
    
    def do_GET(self):
        if '/callback' in self.path:
            if 'code=' in self.path:
                CallbackHandler.auth_code = self.path.split('code=')[1].split('&')[0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"<html><body><h1>Autenticacion exitosa!</h1><p>Puedes cerrar esta ventana.</p></body></html>")
            else:
                self.send_response(400)
                self.end_headers()
        
    def log_message(self, format, *args):
        pass


class WhoopAuth:
    def __init__(self):
        self.client_id = WHOOP_CONFIG['client_id']
        self.client_secret = WHOOP_CONFIG['client_secret']
        self.redirect_uri = WHOOP_CONFIG['redirect_uri']
        self.scopes = ' '.join(WHOOP_CONFIG['scopes'])
        self.tokens_file = WHOOP_TOKENS_FILE
        self.tokens = self._load_tokens()
    
    def _load_tokens(self):
        if os.path.exists(self.tokens_file):
            with open(self.tokens_file, 'r') as f:
                return json.load(f)
        return None
    
    def _save_tokens(self, tokens):
        with open(self.tokens_file, 'w') as f:
            json.dump(tokens, f, indent=2)
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
        base_url = 'https://api.prod.whoop.com/oauth/oauth2/auth'
        return f"{base_url}?{urlencode(params)}"
    
    def authorize(self):
        print("\n" + "="*60)
        print("AUTENTICACIÓN WHOOP")
        print("="*60)
        
        auth_url = self.get_authorization_url()
        print(f"\n1. Se abrirá tu navegador automáticamente")
        print(f"2. Inicia sesión en WHOOP si es necesario")
        print(f"3. Autoriza la aplicación")
        print(f"\nSi no se abre automáticamente, usa esta URL:")
        print(f"{auth_url}\n")
        
        webbrowser.open(auth_url)
        
        print("Esperando autorización...")
        server = HTTPServer(('localhost', 8000), CallbackHandler)
        server.timeout = 120
        server.handle_request()
        
        if not CallbackHandler.auth_code:
            raise Exception("No se recibió código de autorización")
        
        tokens = self._exchange_code_for_tokens(CallbackHandler.auth_code)
        self._save_tokens(tokens)
        
        print("\n✅ Autenticación exitosa!")
        print(f"Access token guardado en: {self.tokens_file}")
        return tokens
    
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
        return self.tokens is not None


def get_whoop_token():
    auth = WhoopAuth()
    if not auth.is_authenticated():
        auth.authorize()
    return auth.get_access_token()
