"""
Exporta tus tokens locales de Garmin como JSON para guardar en GitHub Secrets.

Uso:
    python3 export_garmin_tokens.py

Copia el output y guardalo como secret GARMIN_TOKENS_JSON en GitHub:
    Settings > Secrets and variables > Actions > New repository secret
"""
import json
import os

TOKENSTORE = os.path.expanduser("~/.garmin_tokens")

if not os.path.isdir(TOKENSTORE):
    print("No se encontraron tokens en ~/.garmin_tokens/")
    print("Corre primero: python3 garmin_sync.py")
    exit(1)

tokens = {}
for filename in os.listdir(TOKENSTORE):
    filepath = os.path.join(TOKENSTORE, filename)
    if os.path.isfile(filepath):
        try:
            with open(filepath, 'r') as f:
                tokens[filename] = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

if tokens:
    print(json.dumps(tokens))
else:
    print("No se encontraron archivos de tokens validos")
    exit(1)
