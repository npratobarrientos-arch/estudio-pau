# Configuración OAuth2 para Gmail API

## Requisitos previos
- Cuenta de Google
- Node.js instalado (`node --version` debe mostrar ≥ 18)
- Python ≥ 3.11

---

## Paso 1 — Crear proyecto en Google Cloud Console

1. Ve a https://console.cloud.google.com/
2. Haz clic en **"Seleccionar proyecto"** → **"Nuevo proyecto"**
3. Nombre: `gmail-cleanup-agent` (o el que prefieras)
4. Haz clic en **"Crear"**

---

## Paso 2 — Habilitar la Gmail API

1. En el menú lateral: **"APIs y servicios"** → **"Biblioteca"**
2. Busca **"Gmail API"**
3. Haz clic en **"Habilitar"**

---

## Paso 3 — Crear credenciales OAuth2

1. Ve a **"APIs y servicios"** → **"Credenciales"**
2. Haz clic en **"+ Crear credenciales"** → **"ID de cliente OAuth"**
3. Si se pide configurar la pantalla de consentimiento:
   - Tipo de usuario: **Externo**
   - Nombre de la app: `Gmail Cleanup Agent`
   - Correo de soporte: tu email
   - Guarda y continúa (puedes omitir los campos opcionales)
   - En "Alcances", añade: `https://mail.google.com/`
   - En "Usuarios de prueba", añade tu propio email de Gmail
4. Vuelve a **"Credenciales"** → **"+ Crear credenciales"** → **"ID de cliente OAuth"**
5. Tipo de aplicación: **Aplicación de escritorio**
6. Nombre: `gmail-cleanup-agent-desktop`
7. Haz clic en **"Crear"**
8. Descarga el JSON de credenciales (botón de descarga)
9. Guarda el archivo como `client_secret.json` en la carpeta del proyecto

---

## Paso 4 — Obtener el refresh_token

Ejecuta este script una sola vez para obtener el token:

```bash
pip install google-auth-oauthlib google-auth-httplib2

python3 - << 'EOF'
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
]

flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
creds = flow.run_local_server(port=0)

print("\n=== COPIA ESTOS VALORES ===")
print(f"GMAIL_CLIENT_ID={creds.client_id}")
print(f"GMAIL_CLIENT_SECRET={creds.client_secret}")
print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
print("===========================\n")
EOF
```

Se abrirá el navegador para que autorices el acceso. Acepta todos los permisos.

---

## Paso 5 — Configurar variables de entorno

**Opción A — Exportar en la terminal (sesión actual):**
```bash
export GMAIL_CLIENT_ID="tu_client_id_aqui"
export GMAIL_CLIENT_SECRET="tu_client_secret_aqui"
export GMAIL_REFRESH_TOKEN="tu_refresh_token_aqui"
export ANTHROPIC_API_KEY="tu_api_key_de_anthropic"
```

**Opción B — Archivo .env (recomendado para uso frecuente):**
```bash
cat > .env << 'EOF'
GMAIL_CLIENT_ID=tu_client_id_aqui
GMAIL_CLIENT_SECRET=tu_client_secret_aqui
GMAIL_REFRESH_TOKEN=tu_refresh_token_aqui
ANTHROPIC_API_KEY=tu_api_key_de_anthropic
EOF

# Cargar antes de ejecutar:
source .env  # o: set -a && source .env && set +a
```

> ⚠️ Añade `.env` a tu `.gitignore` para no subir credenciales al repositorio.

---

## Paso 6 — Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Paso 7 — Ejecutar el agente

```bash
python gmail_agent.py
```

El agente:
1. Se conecta a Gmail via MCP
2. Escanea tu inbox y carpetas
3. Presenta un reporte clasificado en 🟢/🟡/🔴
4. Te pide aprobación ANTES de mover nada
5. Mueve a la papelera solo lo aprobado
6. Guarda un log en `gmail_cleanup_log.txt`

---

## Permisos OAuth2 utilizados

| Permiso | Uso |
|---------|-----|
| `gmail.readonly` | Leer y listar correos para análisis |
| `gmail.modify` | Mover correos a la papelera (trash) |

> El agente **nunca** elimina correos permanentemente. Tienes 30 días para recuperarlos desde la papelera de Gmail.

---

## Solución de problemas

**Error: `GMAIL_CLIENT_ID no configurado`**
→ Asegúrate de haber exportado las variables de entorno antes de ejecutar.

**Error: `npx: command not found`**
→ Instala Node.js: https://nodejs.org/

**Error: `403 Forbidden` o `Access denied`**
→ Asegúrate de que tu email está en "Usuarios de prueba" en la pantalla de consentimiento de OAuth.

**El navegador no se abre al obtener el token**
→ Copia la URL que aparece en la terminal y pégala manualmente en el navegador.
