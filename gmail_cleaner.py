#!/usr/bin/env python3
"""
Gmail Cleanup Agent — usa Google API directamente (sin MCP, sin npm)
Flujo: Analizar → Clasificar → Proponer → Aprobar → Ejecutar

Dependencias (ya instaladas con Miniconda):
    google-auth  google-auth-oauthlib  google-api-python-client  anthropic

Uso:
    export GMAIL_CLIENT_ID="..."
    export GMAIL_CLIENT_SECRET="..."
    export GMAIL_REFRESH_TOKEN="..."
    export ANTHROPIC_API_KEY="..."
    ~/miniconda3/bin/python gmail_cleaner.py
"""

import os
import sys
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import anthropic

import gmail_config as cfg

LOG_FILE = Path(__file__).parent / "gmail_cleanup_log.txt"
MODEL    = "claude-opus-4-7"
SCOPES   = ["https://mail.google.com/"]

SYSTEM_LABELS = {
    "INBOX", "SENT", "TRASH", "SPAM", "DRAFT", "UNREAD", "STARRED",
    "IMPORTANT", "CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL",
    "CATEGORY_UPDATES", "CATEGORY_FORUMS",
}


# ─────────────────────────────────────────────────────────────────────────────
# LOG
# ─────────────────────────────────────────────────────────────────────────────

def log_action(action: str, sender: str, subject: str, extra: str = "") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] ACCIÓN={action} | DE={sender} | ASUNTO={subject}"
    if extra:
        line += f" | {extra}"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# GMAIL API
# ─────────────────────────────────────────────────────────────────────────────

def get_gmail_service():
    """Conecta a Gmail usando las credenciales OAuth2 de las variables de entorno."""
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def get_message_metadata(service, msg_id: str) -> dict:
    """Descarga los metadatos de un correo: remitente, asunto, fecha, cabeceras."""
    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="metadata",
        metadataHeaders=["From", "Subject", "Date", "List-Unsubscribe"],
    ).execute()

    headers = {
        h["name"].lower(): h["value"]
        for h in msg.get("payload", {}).get("headers", [])
    }

    # Antigüedad en días
    internal_date = int(msg.get("internalDate", 0)) / 1000
    days_old = int((datetime.now(timezone.utc).timestamp() - internal_date) / 86400)

    # Detectar adjuntos en las partes del payload
    has_attachments = any(
        part.get("filename")
        for part in msg.get("payload", {}).get("parts", [])
    )

    label_ids = msg.get("labelIds", [])
    has_manual_labels = any(l not in SYSTEM_LABELS for l in label_ids)

    return {
        "id": msg_id,
        "from":                  headers.get("from", ""),
        "subject":               headers.get("subject", "(sin asunto)"),
        "date":                  headers.get("date", ""),
        "days_old":              days_old,
        "is_read":               "UNREAD" not in label_ids,
        "is_starred":            "STARRED" in label_ids,
        "has_attachments":       has_attachments,
        "has_list_unsubscribe":  bool(headers.get("list-unsubscribe")),
        "user_replied":          False,   # simplificación: se requeriría buscar en SENT
        "labels":                label_ids,
        "is_manually_labeled":   has_manual_labels,
    }


# ─────────────────────────────────────────────────────────────────────────────
# CLASIFICACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def classify_with_user_config(email: dict) -> tuple[str, str] | None:
    """Capa 1: listas personalizadas de gmail_config.py (mayor prioridad)."""
    subject = (email.get("subject") or "").lower()
    sender  = (email.get("from")    or "").lower()

    for p in cfg.ALWAYS_PROTECT:
        if p.lower() in sender:
            return "ROJO", f"Lista protegida: {p}"

    for kw in cfg.PROTECT_SUBJECT_KEYWORDS:
        if kw.lower() in subject:
            return "ROJO", f"Término protegido en asunto: «{kw}»"

    for s in cfg.SAFE_TO_TRASH:
        if s.lower() in sender:
            return "VERDE", f"Lista segura del usuario: {s}"

    return None


def classify_email(email: dict) -> tuple[str, str]:
    """Clasificación completa: config personalizado + reglas genéricas."""
    result = classify_with_user_config(email)
    if result:
        return result

    subject          = (email.get("subject") or "").lower()
    sender           = (email.get("from")    or "").lower()
    has_attachments  = email.get("has_attachments",  False)
    has_list_unsub   = email.get("has_list_unsubscribe", False)
    is_starred       = email.get("is_starred",  False)
    user_replied     = email.get("user_replied", False)
    days_old         = email.get("days_old",     0)
    is_read          = email.get("is_read",      True)
    has_manual       = email.get("is_manually_labeled", False)

    # 🔴 Protegidos
    if is_starred:                    return "ROJO",    "Marcado con estrella"
    if user_replied:                  return "ROJO",    "El usuario respondió en este hilo"
    if not is_read and days_old < 30: return "ROJO",    f"No leído, {days_old} días (mínimo 30)"
    if has_manual:                    return "ROJO",    "Tiene etiquetas manuales"

    # 🟡 Revisar primero
    if has_attachments:               return "AMARILLO", "Tiene adjuntos"

    important_kw = ["diploma", "certificado", "título", "constancia", "contrato",
                    "factura", "recibo", "reserva", "confirmación", "comprobante",
                    "curriculum", " cv ", "titulación", "matrícula"]
    if any(kw in subject for kw in important_kw):
        return "AMARILLO", "Término importante en asunto"

    institution_kw = ["banco", "bank", "universidad", ".edu", ".gob", ".gov",
                      "hospital", "hacienda", "seguro social", "ministerio"]
    if any(kw in sender for kw in institution_kw):
        return "AMARILLO", "Remitente institucional"

    # 🟢 Candidatos a papelera
    if has_list_unsub and days_old > 60:
        return "VERDE", f"Newsletter sin abrir {days_old} días"

    promo_kw = ["oferta", "descuento", "% off", " off ", "sale", "newsletter",
                "promo", "deal", "gratis", "black friday", "cyber monday"]
    if any(kw in subject for kw in promo_kw):
        return "VERDE", "Términos promocionales en asunto"

    social_senders = ["facebook", "instagram", "linkedin", "twitter", "x.com",
                      "tiktok", "youtube", "pinterest", "snapchat"]
    if any(sn in sender for sn in social_senders):
        return "VERDE", "Notificación de red social"

    if any(x in sender for x in ["no-reply", "noreply", "no_reply", "donotreply"]):
        if not has_attachments:
            return "VERDE", "No-reply sin adjuntos"

    return "AMARILLO", "Clasificación incierta — revisión manual"


# ─────────────────────────────────────────────────────────────────────────────
# ESCANEO
# ─────────────────────────────────────────────────────────────────────────────

def scan_gmail(service) -> tuple[list, list, list]:
    """Ejecuta las queries de cfg.SCAN_QUERIES y clasifica todos los correos."""
    verde, amarillo, rojo = [], [], []
    seen_ids = set()

    for q_cfg in cfg.SCAN_QUERIES:
        query = q_cfg["query"]
        label = q_cfg["label"]
        print(f"\n  📁 {label}  ({query})")

        page_token = None
        total = 0

        while True:
            params: dict = {"userId": "me", "q": query, "maxResults": 100}
            if page_token:
                params["pageToken"] = page_token

            result   = service.users().messages().list(**params).execute()
            messages = result.get("messages", [])
            if not messages:
                break

            for msg in messages:
                mid = msg["id"]
                if mid in seen_ids:
                    continue
                seen_ids.add(mid)
                total += 1

                try:
                    email        = get_message_metadata(service, mid)
                    cat, reason  = classify_email(email)
                    email["_category"] = cat
                    email["_reason"]   = reason

                    if cat == "VERDE":       verde.append(email)
                    elif cat == "AMARILLO":  amarillo.append(email)
                    else:                    rojo.append(email)
                except Exception:
                    pass  # Seguir con el siguiente

                print(f"     procesados: {total}", end="\r", flush=True)

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        print(f"     {total} correos procesados en {label}         ")

    return verde, amarillo, rojo


# ─────────────────────────────────────────────────────────────────────────────
# REPORTE
# ─────────────────────────────────────────────────────────────────────────────

def print_report(verde: list, amarillo: list, rojo: list) -> None:
    total    = len(verde) + len(amarillo) + len(rojo)
    size_mb  = total * 50 / 1024

    print(f"""
{'═'*62}
📊 REPORTE DE ANÁLISIS — LIMPIEZA GMAIL
{'═'*62}
📧 Total revisados  : {total} correos
💾 Espacio estimado : ~{size_mb:.1f} MB
""")

    # 🟢 Agrupar por dominio del remitente
    groups: dict = defaultdict(list)
    for e in verde:
        raw    = e["from"]
        domain = raw.split("@")[-1].split(">")[0].strip() if "@" in raw else raw
        groups[domain].append(e)

    verde_mb = len(verde) * 50 / 1024
    print(f"{'─'*62}")
    print(f"🟢 CANDIDATOS A PAPELERA — {len(verde)} correos (~{verde_mb:.1f} MB)")
    print(f"{'─'*62}")
    if verde:
        for i, (domain, emails) in enumerate(groups.items(), 1):
            max_age = max(e["days_old"] for e in emails)
            print(f"\n  Grupo {i}: {domain} ({len(emails)} correo{'s' if len(emails)>1 else ''})")
            print(f"  • Más antiguo : hace {max_age} días")
            print(f"  • Razón       : {emails[0]['_reason']}")
    else:
        print("  (ninguno)")

    print(f"\n{'─'*62}")
    print(f"🟡 REQUIEREN TU REVISIÓN — {len(amarillo)} correos")
    print(f"{'─'*62}")
    for e in amarillo[:15]:
        attach = " 📎" if e.get("has_attachments") else ""
        print(f"  • {e['from'][:42]}")
        print(f"    \"{e['subject'][:52]}\"{attach}")
        print(f"    ⚠️  {e['_reason']}")
    if len(amarillo) > 15:
        print(f"  … y {len(amarillo) - 15} más")

    print(f"\n{'─'*62}")
    print(f"🔴 PROTEGIDOS — NO SE TOCARÁN — {len(rojo)} correos")
    print(f"{'─'*62}")
    reasons: dict = defaultdict(int)
    for e in rojo:
        reasons[e["_reason"]] += 1
    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  • {count:>3} correo{'s' if count>1 else ''}: {reason}")


# ─────────────────────────────────────────────────────────────────────────────
# AGENTE PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def run_agent() -> None:
    print(f"\n{'═'*62}")
    print("  AGENTE DE GESTIÓN DE GMAIL — LIMPIEZA SEGURA")
    print(f"{'═'*62}")

    # Validar variables de entorno
    required = ["GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN", "ANTHROPIC_API_KEY"]
    missing  = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"\n❌ Faltan variables de entorno: {', '.join(missing)}")
        print("   Consulta get_refresh_token.py y oauth_setup.md")
        sys.exit(1)

    log_action("INICIO", "N/A", "N/A", "Agente iniciado")

    # ── Conectar a Gmail ───────────────────────────────────────────────────
    print("\nConectando con Gmail...")
    try:
        service = get_gmail_service()
        profile = service.users().getProfile(userId="me").execute()
        print(f"✅ Conectado como  : {profile['emailAddress']}")
        print(f"   Total mensajes  : {profile['messagesTotal']:,}")
    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")
        print("   Regenera el refresh token con: ~/miniconda3/bin/python get_refresh_token.py")
        sys.exit(1)

    # ── FASE 1: ANÁLISIS ───────────────────────────────────────────────────
    print(f"\n{'─'*62}")
    print("FASE 1 — ANÁLISIS Y CLASIFICACIÓN")
    print(f"{'─'*62}")

    verde, amarillo, rojo = scan_gmail(service)
    print_report(verde, amarillo, rojo)

    # ── FASE 2: APROBACIÓN ────────────────────────────────────────────────
    print(f"\n{'═'*62}")
    print("FASE 2 — APROBACIÓN")
    print(f"{'═'*62}")
    print(f"\nIdentificados {len(verde)} candidatos 🟢 para mover a papelera.")
    print("\n  [1] Aprobar todos los grupos VERDES")
    print("  [2] Aprobar remitentes/dominios específicos")
    print("  [3] Cancelar — no mover nada")

    approved: list = []
    while True:
        choice = input("\nTu elección (1/2/3): ").strip()

        if choice == "1":
            approved = list(verde)
            print(f"\n✅ Aprobados {len(approved)} correos.")
            break

        elif choice == "2":
            raw      = input("Escribe dominios a aprobar (separados por coma): ").strip()
            selected = [s.strip().lower() for s in raw.split(",") if s.strip()]
            approved = [e for e in verde if any(s in e["from"].lower() for s in selected)]
            print(f"\n✅ Seleccionados {len(approved)} correos.")
            break

        elif choice == "3":
            print("\n❌ Operación cancelada. No se movió nada.")
            log_action("CANCELADO", "N/A", "N/A", "Usuario canceló")
            return

        else:
            print("   Por favor escribe 1, 2 o 3.")

    if not approved:
        print("\nNada que procesar.")
        return

    confirm = input(
        f"\n⚠️  ¿Confirmas mover {len(approved)} correos a la PAPELERA? (s/n): "
    ).strip().lower()

    if confirm != "s":
        print("\n❌ Cancelado en confirmación final.")
        log_action("CANCELADO", "N/A", "N/A", "No confirmó ejecución")
        return

    # ── FASE 3: EJECUCIÓN ─────────────────────────────────────────────────
    print(f"\n{'═'*62}")
    print("FASE 3 — EJECUCIÓN")
    print(f"{'═'*62}\n")

    moved  = 0
    errors = 0

    for i in range(0, len(approved), cfg.BATCH_SIZE):
        batch = approved[i : i + cfg.BATCH_SIZE]
        for email in batch:
            sender  = email.get("from",    "desconocido")
            subject = email.get("subject", "(sin asunto)")
            try:
                service.users().messages().trash(userId="me", id=email["id"]).execute()
                moved += 1
                log_action(
                    "MOVIDO_A_PAPELERA", sender, subject,
                    f"ID={email['id']} | Razón={email['_reason']}",
                )
                print(f"  ✓ {sender[:36]} — {subject[:46]}")
            except Exception as exc:
                errors += 1
                log_action("ERROR", sender, subject, str(exc))
                print(f"  ✗ Error: {str(exc)[:70]}")

    # ── RESUMEN ───────────────────────────────────────────────────────────
    print(f"\n{'═'*62}")
    print("RESUMEN FINAL")
    print(f"{'═'*62}")
    print(f"\n✅ Movidos a papelera  : {moved}")
    if errors:
        print(f"⚠️  Errores             : {errors}")
    print(f"📋 Log guardado en     : {LOG_FILE}")
    print("\n💡 Tienes 30 días para recuperarlos desde la papelera de Gmail.\n")
    log_action("RESUMEN", "N/A", "N/A", f"Movidos={moved} | Errores={errors} | Total={len(approved)}")


if __name__ == "__main__":
    run_agent()
