#!/usr/bin/env python3
"""
get_refresh_token.py — Genera un nuevo refresh token para Gmail.
Ejecutar UNA SOLA VEZ. Abre el navegador automáticamente.

Uso:
    ~/miniconda3/bin/python get_refresh_token.py
"""
import json
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("❌ Falta google-auth-oauthlib")
    print("   Instala con: ~/miniconda3/bin/pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = ["https://mail.google.com/"]

# Leer credenciales desde client_secret.json
secret_file = Path(__file__).parent / "client_secret.json"
if not secret_file.exists():
    print(f"❌ No se encontró {secret_file}")
    print("   Descarga el JSON desde Google Cloud Console y ponlo en esta carpeta.")
    sys.exit(1)

data = json.loads(secret_file.read_text())
installed = data.get("installed", data.get("web", {}))
client_id = installed.get("client_id", "")
client_secret = installed.get("client_secret", "")

print(f"✅ Credenciales leídas de client_secret.json")
print(f"   client_id: {client_id[:40]}...")
print("\nAbriendo navegador para autorizar Gmail...\n")

flow = InstalledAppFlow.from_client_config(
    {"installed": {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uris": ["http://localhost"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }},
    SCOPES
)
creds = flow.run_local_server(port=0)

print("\n" + "=" * 65)
print("✅  REFRESH TOKEN OBTENIDO — copia estos 3 exports en la terminal")
print("=" * 65)
print()
print(f'export GMAIL_CLIENT_ID="{client_id}"')
print(f'export GMAIL_CLIENT_SECRET="{client_secret}"')
print(f'export GMAIL_REFRESH_TOKEN="{creds.refresh_token}"')
print()
print("=" * 65)
print("Luego ejecuta:")
print("  export ANTHROPIC_API_KEY=\"sk-ant-...\"")
print("  ~/miniconda3/bin/python gmail_cleaner.py")
