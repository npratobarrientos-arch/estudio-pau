#!/usr/bin/env python3
"""
Gmail Cleanup Agent — MODO DEMO
Simula un inbox real para mostrar el flujo completo sin credenciales de Gmail.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import gmail_config as cfg

LOG_FILE = Path("gmail_cleanup_log.txt")

# ──────────────────────────────────────────────────────────────────────────────
# BANDEJA DE ENTRADA SIMULADA (representa un inbox típico)
# ──────────────────────────────────────────────────────────────────────────────
FAKE_INBOX = [
    # 🟢 Newsletters viejas
    {"id": "msg_001", "from": "ofertas@amazon.es", "subject": "Ofertas del día — hasta 70% off en tecnología",
     "days_old": 95, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["CATEGORY_PROMOTIONS"]},
    {"id": "msg_002", "from": "newsletter@elcorteingles.es", "subject": "Newsletter — Rebajas de enero",
     "days_old": 78, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["CATEGORY_PROMOTIONS"]},
    {"id": "msg_003", "from": "newsletter@elcorteingles.es", "subject": "Newsletter — Colección primavera",
     "days_old": 62, "is_read": False, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["CATEGORY_PROMOTIONS"]},
    {"id": "msg_004", "from": "promo@zara.com", "subject": "Sale — Nueva colección disponible",
     "days_old": 110, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["CATEGORY_PROMOTIONS"]},
    # 🟢 Redes sociales
    {"id": "msg_005", "from": "notification@facebookmail.com", "subject": "Tienes 3 nuevas notificaciones",
     "days_old": 45, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": False, "user_replied": False, "labels": ["CATEGORY_SOCIAL"]},
    {"id": "msg_006", "from": "notification@facebookmail.com", "subject": "María comentó en tu publicación",
     "days_old": 52, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": False, "user_replied": False, "labels": ["CATEGORY_SOCIAL"]},
    {"id": "msg_007", "from": "noreply@linkedin.com", "subject": "Tienes 5 nuevas visitas a tu perfil",
     "days_old": 67, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": False, "user_replied": False, "labels": ["CATEGORY_SOCIAL"]},
    {"id": "msg_008", "from": "noreply@linkedin.com", "subject": "Juan García te envió una invitación",
     "days_old": 40, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": False, "user_replied": False, "labels": ["CATEGORY_SOCIAL"]},
    # 🟢 No-reply sin adjuntos
    {"id": "msg_009", "from": "no-reply@medium.com", "subject": "Tu resumen semanal de Medium",
     "days_old": 85, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["INBOX"]},
    {"id": "msg_010", "from": "noreply@duolingo.com", "subject": "¡Llevas 3 días sin practicar!",
     "days_old": 70, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["INBOX"]},
    # 🟡 Con adjuntos (revisar)
    {"id": "msg_011", "from": "contratos@pisocompartido.com", "subject": "Contrato de arrendamiento firmado",
     "days_old": 180, "is_read": True, "is_starred": False, "has_attachments": True,
     "list_unsubscribe": False, "user_replied": True, "labels": ["INBOX"]},
    {"id": "msg_012", "from": "facturacion@vodafone.es", "subject": "Factura de febrero 2026",
     "days_old": 90, "is_read": True, "is_starred": False, "has_attachments": True,
     "list_unsubscribe": False, "user_replied": False, "labels": ["INBOX"]},
    {"id": "msg_013", "from": "secretaria@universidad.es", "subject": "Constancia de matrícula adjunta",
     "days_old": 200, "is_read": True, "is_starred": False, "has_attachments": True,
     "list_unsubscribe": False, "user_replied": False, "labels": ["INBOX"]},
    # 🔴 Protegidos — genéricos
    {"id": "msg_014", "from": "mama@gmail.com", "subject": "Cena del domingo — confirmas?",
     "days_old": 5, "is_read": False, "is_starred": True, "has_attachments": False,
     "list_unsubscribe": False, "user_replied": False, "labels": ["INBOX"]},
    {"id": "msg_015", "from": "rrhh@empresa.com", "subject": "Re: Entrevista del martes",
     "days_old": 12, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": False, "user_replied": True, "labels": ["INBOX"]},
    {"id": "msg_016", "from": "banco@bbva.es", "subject": "Movimiento en tu cuenta",
     "days_old": 2, "is_read": False, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": False, "user_replied": False, "labels": ["INBOX"]},

    # 🟢 De la lista SAFE_TO_TRASH del usuario
    {"id": "msg_017", "from": "ofertas@groupon.es", "subject": "50% off en restaurantes hoy",
     "days_old": 20, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["CATEGORY_PROMOTIONS"]},
    {"id": "msg_018", "from": "deals@skyscanner.net", "subject": "Vuelos baratos desde Madrid",
     "days_old": 15, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["CATEGORY_PROMOTIONS"]},
    {"id": "msg_019", "from": "noreply@ryanair.com", "subject": "¡Ofertas de vuelos esta semana!",
     "days_old": 10, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["CATEGORY_PROMOTIONS"]},
    {"id": "msg_020", "from": "newsletter@getyourguide.com", "subject": "Actividades recomendadas en Barcelona",
     "days_old": 25, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["CATEGORY_PROMOTIONS"]},
    {"id": "msg_021", "from": "promo@bolt.eu", "subject": "5€ de descuento en tu próximo viaje",
     "days_old": 18, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["CATEGORY_PROMOTIONS"]},
    {"id": "msg_022", "from": "news@instantgaming.com", "subject": "Juegos en oferta esta semana",
     "days_old": 30, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": True, "user_replied": False, "labels": ["CATEGORY_PROMOTIONS"]},

    # 🔴 De la lista ALWAYS_PROTECT del usuario
    {"id": "msg_023", "from": "noreply@ticketmaster.es", "subject": "Tu entrada para el concierto",
     "days_old": 5, "is_read": True, "is_starred": False, "has_attachments": True,
     "list_unsubscribe": False, "user_replied": False, "labels": ["INBOX"]},
    {"id": "msg_024", "from": "service@paypal.es", "subject": "Has recibido un pago de 50€",
     "days_old": 3, "is_read": True, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": False, "user_replied": False, "labels": ["INBOX"]},
    {"id": "msg_025", "from": "info@agenciatributaria.gob.es", "subject": "Declaración de la Renta 2025",
     "days_old": 8, "is_read": False, "is_starred": False, "has_attachments": False,
     "list_unsubscribe": False, "user_replied": False, "labels": ["INBOX"]},
    {"id": "msg_026", "from": "soporte@revolut.com", "subject": "Tu extracto de abril",
     "days_old": 22, "is_read": True, "is_starred": False, "has_attachments": True,
     "list_unsubscribe": False, "user_replied": False, "labels": ["INBOX"]},

    # 🔴 Ryanair con confirmación de vuelo (keyword protegida en asunto)
    {"id": "msg_027", "from": "noreply@ryanair.com", "subject": "Confirmación de reserva FR1234",
     "days_old": 3, "is_read": True, "is_starred": False, "has_attachments": True,
     "list_unsubscribe": False, "user_replied": False, "labels": ["INBOX"]},
]


def classify_email(email: dict) -> tuple[str, str]:
    subject = (email.get("subject") or "").lower()
    sender = (email.get("from") or "").lower()

    # Capa 1: listas personalizadas del usuario (mayor prioridad)
    for protected in cfg.ALWAYS_PROTECT:
        if protected.lower() in sender:
            return "ROJO", f"Lista protegida del usuario: {protected}"
    for kw in cfg.PROTECT_SUBJECT_KEYWORDS:
        if kw.lower() in subject:
            return "ROJO", f"Asunto contiene término protegido: «{kw}»"
    for safe in cfg.SAFE_TO_TRASH:
        if safe.lower() in sender:
            return "VERDE", f"Lista segura del usuario: {safe}"

    # Capa 2: reglas genéricas
    has_attachments = bool(email.get("has_attachments"))
    has_list_unsub = bool(email.get("list_unsubscribe"))
    is_read = email.get("is_read", True)
    is_starred = bool(email.get("is_starred"))
    user_replied = bool(email.get("user_replied"))
    days_old = int(email.get("days_old") or 0)
    labels = [str(l).upper() for l in (email.get("labels") or [])]
    system_labels = {"INBOX", "SENT", "TRASH", "SPAM", "DRAFT",
                     "CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL",
                     "CATEGORY_UPDATES", "CATEGORY_FORUMS", "UNREAD"}
    has_manual_labels = any(l not in system_labels for l in labels)

    if is_starred:
        return "ROJO", "Marcado con estrella"
    if user_replied:
        return "ROJO", "El usuario respondió en este hilo"
    if not is_read and days_old < 30:
        return "ROJO", f"No leído y tiene {days_old} días (mínimo 30)"
    if has_manual_labels:
        return "ROJO", "Tiene etiquetas manuales"

    if has_attachments:
        return "AMARILLO", "Tiene adjuntos"
    important_kw = ["diploma", "certificado", "título", "constancia", "contrato",
                    "factura", "recibo", "reserva", "confirmación", "comprobante",
                    "curriculum", " cv ", "titulación", "matrícula"]
    if any(kw in subject for kw in important_kw):
        return "AMARILLO", "Asunto contiene término de documento importante"
    institution_kw = ["banco", "bank", "universidad", "edu.", ".gob", ".gov",
                      "hospital", "clinica", "hacienda", "seguro", "ministerio"]
    if any(kw in sender for kw in institution_kw):
        return "AMARILLO", "Remitente parece institución importante"

    if has_list_unsub and days_old > 60:
        return "VERDE", f"Newsletter con List-Unsubscribe, sin abrir {days_old} días"
    promo_kw = ["oferta", "descuento", "% off", " off ", "sale", "unsubscribe",
                "newsletter", "promocion", "promo", "deal", "gratis"]
    if any(kw in subject for kw in promo_kw):
        return "VERDE", "Asunto contiene términos promocionales"
    social_senders = ["facebook", "instagram", "linkedin", "twitter", "x.com",
                      "tiktok", "youtube", "noreply@linkedin", "notification@"]
    if any(sn in sender for sn in social_senders):
        return "VERDE", "Notificación automática de red social"
    if "no-reply" in sender or "noreply" in sender:
        if not has_attachments:
            return "VERDE", "Email de no-reply sin adjuntos"

    return "AMARILLO", "Clasificación incierta — requiere revisión manual"


def log_action(action: str, sender: str, subject: str, extra: str = "") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] ACCIÓN={action} | DE={sender} | ASUNTO={subject}"
    if extra:
        line += f" | {extra}"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _print_report(verde: list, amarillo: list, rojo: list) -> None:
    total = len(verde) + len(amarillo) + len(rojo)
    size_mb = total * 50 / 1024
    print(f"""
═══════════════════════════════════════════════════
📊 REPORTE DE ANÁLISIS — LIMPIEZA GMAIL (DEMO)
═══════════════════════════════════════════════════
📁 Carpetas analizadas : INBOX, Promotions, Social
📧 Total revisados     : {total} correos
💾 Espacio estimado    : ~{size_mb:.1f} MB
""")

    # 🟢 Verde — agrupar por dominio remitente
    groups: dict = defaultdict(list)
    for e in verde:
        domain = e["from"].split("@")[-1] if "@" in e["from"] else e["from"]
        groups[domain].append(e)

    verde_size = len(verde) * 50 / 1024
    print(f"──────────────────────────────────────────────────")
    print(f"🟢 CANDIDATOS A PAPELERA — {len(verde)} correos (~{verde_size:.1f} MB)")
    print(f"──────────────────────────────────────────────────")
    for i, (domain, emails) in enumerate(groups.items(), 1):
        sample = emails[0]
        max_age = max(e["days_old"] for e in emails)
        print(f"\n  Grupo {i}: {domain} ({len(emails)} correos)")
        print(f"  • Último hace {max_age} días")
        print(f"  • Razón: {sample['_reason']}")

    # 🟡 Amarillo
    print(f"\n──────────────────────────────────────────────────")
    print(f"🟡 REQUIEREN TU REVISIÓN — {len(amarillo)} correos")
    print(f"──────────────────────────────────────────────────")
    for e in amarillo:
        attach = "📎 adjunto" if e.get("has_attachments") else ""
        print(f"  • {e['from'][:35]}")
        print(f"    \"{e['subject'][:50]}\" {attach}")
        print(f"    ⚠️  {e['_reason']}")

    # 🔴 Rojo
    print(f"\n──────────────────────────────────────────────────")
    print(f"🔴 PROTEGIDOS — NO SE TOCARÁN — {len(rojo)} correos")
    print(f"──────────────────────────────────────────────────")
    for e in rojo:
        print(f"  • {e['from'][:35]} — {e['_reason']}")


def run_demo() -> None:
    print("\n" + "═" * 62)
    print("  AGENTE DE GESTIÓN DE GMAIL — MODO DEMO")
    print("  (inbox simulado — sin credenciales reales)")
    print("═" * 62)

    # ── Fase 1: Clasificar ──────────────────────────────────────
    print("\n🔍 Clasificando correos del inbox simulado...\n")

    for email in FAKE_INBOX:
        cat, reason = classify_email(email)
        email["_category"] = cat
        email["_reason"] = reason

    verde = [e for e in FAKE_INBOX if e["_category"] == "VERDE"]
    amarillo = [e for e in FAKE_INBOX if e["_category"] == "AMARILLO"]
    rojo = [e for e in FAKE_INBOX if e["_category"] == "ROJO"]

    # ── Fase 1b: Reporte local (sin API key requerida en demo) ──
    print("📊 Generando reporte de análisis...\n")
    print("─" * 62)
    _print_report(verde, amarillo, rojo)
    print("─" * 62)

    # ── Fase 2: Aprobación ──────────────────────────────────────
    print(f"\n📬 Resumen: {len(verde)} candidatos 🟢 | {len(amarillo)} a revisar 🟡 | {len(rojo)} protegidos 🔴")
    print("\n¿Qué deseas hacer?")
    print("  [1] Aprobar todos los grupos VERDES (mover a papelera)")
    print("  [2] Cancelar — no mover nada")

    while True:
        choice = input("\nTu elección (1/2): ").strip()
        if choice in ("1", "2"):
            break
        print("Por favor escribe 1 o 2.")

    if choice == "2":
        print("\n❌ Operación cancelada. No se movió ningún correo.")
        log_action("CANCELADO", "N/A", "N/A", "Demo: usuario canceló")
        return

    confirm = input(f"\n⚠️  ¿Confirmas mover {len(verde)} correos a la PAPELERA? (s/n): ").strip().lower()
    if confirm != "s":
        print("\n❌ Cancelado en confirmación final.")
        return

    # ── Fase 3: Ejecución (simulada en demo) ────────────────────
    print(f"\n" + "═" * 62)
    print("  FASE 3 — EJECUCIÓN (SIMULADA EN MODO DEMO)")
    print("═" * 62)
    print()

    moved = 0
    for email in verde:
        sender = email["from"]
        subject = email["subject"]
        print(f"  ✓ [DEMO] papelera ← {sender[:35]} — {subject[:40]}")
        log_action(
            "MOVIDO_A_PAPELERA (DEMO)", sender, subject,
            f"ID={email['id']} | Razón={email['_reason']}"
        )
        moved += 1

    size_kb = moved * 50
    print(f"\n{'═' * 62}")
    print(f"  RESUMEN FINAL")
    print(f"{'═' * 62}")
    print(f"\n✅ Correos movidos a papelera : {moved}")
    print(f"💾 Espacio liberado estimado  : ~{size_kb / 1024:.1f} MB")
    print(f"🟡 Correos a revisar           : {len(amarillo)}")
    print(f"🔴 Correos protegidos          : {len(rojo)}")
    print(f"📋 Log guardado en             : {LOG_FILE.absolute()}")
    print("\n💡 En modo REAL los correos irían a tu papelera de Gmail.")
    print("   Tienes 30 días para recuperarlos si fue un error.\n")

    log_action(
        "RESUMEN (DEMO)", "N/A", "N/A",
        f"Movidos={moved} | Revisar={len(amarillo)} | Protegidos={len(rojo)}"
    )


if __name__ == "__main__":
    run_demo()
