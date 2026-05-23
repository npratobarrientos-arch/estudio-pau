#!/usr/bin/env python3
"""
Agente de Gestión de Gmail - Limpieza Segura del Inbox
Flujo obligatorio: Analizar → Clasificar → Proponer → Aprobar → Ejecutar

Uso:
    python gmail_agent.py

Variables de entorno requeridas:
    GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN, ANTHROPIC_API_KEY

Consulta oauth_setup.md para instrucciones de configuración.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import gmail_config as cfg

LOG_FILE = Path("gmail_cleanup_log.txt")
BATCH_SIZE = cfg.BATCH_SIZE
MODEL = "claude-opus-4-7"

_SYSTEM_PROMPT_TEMPLATE = """Eres un asistente especializado en limpieza segura de Gmail. Tu idioma es el español.

FLUJO OBLIGATORIO (nunca lo saltees):
1. ANALIZAR — escanear inbox y carpetas con las herramientas disponibles
2. CLASIFICAR — aplicar criterios de seguridad a cada correo
3. PROPONER — presentar reporte agrupado al usuario
4. ESPERAR — el sistema pedirá aprobación antes de ejecutar
5. EJECUTAR — solo mover a papelera lo aprobado

REGLAS CRÍTICAS:
- NUNCA borres permanentemente. Solo mueves a la papelera (trash).
- Si hay duda sobre clasificación, siempre escala al nivel más cauteloso.
- Trabaja en lotes de máximo {batch_size} correos por llamada de herramienta.
- Explica claramente POR QUÉ propones mover cada grupo.

CATEGORÍAS DE CLASIFICACIÓN:

🟢 CANDIDATOS A MOVER A PAPELERA (alta confianza):
- Newsletters no abiertas hace más de 60 días (List-Unsubscribe presente)
- Emails promocionales de tiendas o marketplaces
- Notificaciones automáticas de redes sociales (Facebook, Instagram, LinkedIn, Twitter/X)
- Emails de "no-reply" sin adjuntos y sin respuesta del usuario
- Asunto con: oferta, descuento, % off, sale, unsubscribe, newsletter
- Remitentes en lista SAFE_TO_TRASH del usuario (ver abajo)

🟡 REQUIEREN REVISIÓN ANTES DE PROPONER:
- Cualquier correo con adjuntos (PDF, DOC, DOCX, JPG, PNG, ZIP)
- Correos de instituciones: bancos, universidades, gobierno, salud
- Asunto con: diploma, certificado, título, constancia, contrato, factura, recibo,
  reserva, confirmación, comprobante, curriculum, CV

🔴 NUNCA TOCAR SIN PERMISO EXPLÍCITO:
- Remitentes en lista ALWAYS_PROTECT del usuario (ver abajo) — PRIORIDAD MÁXIMA
- Asunto contiene palabras clave protegidas del usuario (ver abajo)
- Correos donde el usuario respondió (hilos con mensajes salientes)
- Correos no leídos de menos de 30 días
- Emails con etiquetas manuales del usuario
- Correos marcados con estrella

CONFIGURACIÓN PERSONALIZADA DEL USUARIO:

🟢 REMITENTES SEGUROS (borrar sin pedir aprobación adicional):
{safe_list}

🔴 REMITENTES SIEMPRE PROTEGIDOS (nunca tocar, prioridad absoluta):
{protect_list}

🔴 PALABRAS EN ASUNTO QUE SIEMPRE PROTEGEN (aunque el remitente sea seguro):
{protect_keywords}

QUERIES DE ESCANEO (usa estas búsquedas en este orden):
{scan_queries}

FORMATO DEL REPORTE (usa exactamente esta estructura):

═══════════════════════════════════════
📊 REPORTE DE ANÁLISIS - LIMPIEZA GMAIL
═══════════════════════════════════════

📁 Queries ejecutadas: {scan_labels}
📧 Total de correos revisados: N
💾 Espacio estimado a liberar: X MB

────────────────────────────────────────
🟢 CANDIDATOS A PAPELERA — N correos (~X MB)
────────────────────────────────────────
Grupo 1: [nombre del grupo] (N correos)
  • remitente@ejemplo.com — último: hace X días
  • Razón: [explicación clara]

────────────────────────────────────────
🟡 REQUIEREN TU REVISIÓN — N correos
────────────────────────────────────────
  • remitente — "asunto" — motivo

────────────────────────────────────────
🔴 PROTEGIDOS — NO SE TOCARÁN — N correos
────────────────────────────────────────
  • N correos con estrella / N en lista protegida / etc.

Al terminar el reporte, di exactamente: "REPORTE_COMPLETO" en una línea separada.
Esto le indica al sistema que puede continuar con el proceso de aprobación."""


def _build_system_prompt() -> str:
    """Construye el system prompt con la configuración personalizada del usuario."""
    safe_list = "\n".join(f"  - {s}" for s in cfg.SAFE_TO_TRASH)
    protect_list = "\n".join(f"  - {p}" for p in cfg.ALWAYS_PROTECT)
    protect_keywords = "\n".join(f"  - {k}" for k in cfg.PROTECT_SUBJECT_KEYWORDS)
    scan_queries = "\n".join(
        f"  {i+1}. {q['label']}: {q['query']} — {q['description']}"
        for i, q in enumerate(cfg.SCAN_QUERIES)
    )
    scan_labels = ", ".join(q["label"] for q in cfg.SCAN_QUERIES)
    return _SYSTEM_PROMPT_TEMPLATE.format(
        batch_size=cfg.BATCH_SIZE,
        safe_list=safe_list,
        protect_list=protect_list,
        protect_keywords=protect_keywords,
        scan_queries=scan_queries,
        scan_labels=scan_labels,
    )


def classify_with_user_config(email: dict) -> tuple[str, str] | None:
    """
    Primera capa de clasificación usando listas personalizadas del usuario.
    Devuelve (categoría, razón) si el email coincide, o None para continuar
    con la clasificación genérica.

    Prioridad: ALWAYS_PROTECT > PROTECT_SUBJECT_KEYWORDS > SAFE_TO_TRASH
    """
    subject = (email.get("subject") or "").lower()
    sender = (email.get("from") or email.get("sender") or "").lower()

    # 🔴 Protección absoluta — lista del usuario
    for protected in cfg.ALWAYS_PROTECT:
        if protected.lower() in sender:
            return "ROJO", f"En lista protegida del usuario: {protected}"

    # 🔴 Palabras clave protegidas en asunto — aunque el remitente sea seguro
    for kw in cfg.PROTECT_SUBJECT_KEYWORDS:
        if kw.lower() in subject:
            return "ROJO", f"Asunto contiene término protegido: «{kw}»"

    # 🟢 Remitentes seguros — lista del usuario
    for safe in cfg.SAFE_TO_TRASH:
        if safe.lower() in sender:
            return "VERDE", f"Remitente en lista segura del usuario: {safe}"

    return None  # Continuar con clasificación genérica


def log_action(action: str, sender: str, subject: str, extra: str = "") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] ACCIÓN={action} | DE={sender} | ASUNTO={subject}"
    if extra:
        line += f" | {extra}"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def classify_email(email: dict) -> tuple[str, str]:
    """Clasificación local: primero listas personalizadas, luego reglas genéricas."""
    # Capa 1: lista personalizada del usuario (mayor prioridad)
    user_result = classify_with_user_config(email)
    if user_result is not None:
        return user_result

    # Capa 2: reglas genéricas de seguridad
    subject = (email.get("subject") or "").lower()
    sender = (email.get("from") or email.get("sender") or "").lower()
    has_attachments = bool(email.get("has_attachments") or email.get("attachments"))
    has_list_unsub = bool(email.get("list_unsubscribe") or email.get("has_list_unsubscribe"))
    is_read = email.get("is_read", True)
    is_starred = bool(email.get("starred") or email.get("is_starred"))
    user_replied = bool(email.get("user_replied") or email.get("thread_has_reply"))
    days_old = int(email.get("days_old") or 0)
    labels = [str(l).upper() for l in (email.get("labels") or [])]
    system_labels = {"INBOX", "SENT", "TRASH", "SPAM", "DRAFT",
                     "CATEGORY_PROMOTIONS", "CATEGORY_SOCIAL",
                     "CATEGORY_UPDATES", "CATEGORY_FORUMS", "UNREAD"}
    has_manual_labels = any(l not in system_labels for l in labels)

    # 🔴 Máxima prioridad — protegidos
    if is_starred:
        return "ROJO", "Marcado con estrella"
    if user_replied:
        return "ROJO", "El usuario respondió en este hilo"
    if not is_read and days_old < 30:
        return "ROJO", f"No leído y tiene {days_old} días (mínimo 30)"
    if has_manual_labels:
        return "ROJO", "Tiene etiquetas manuales del usuario"

    # 🟡 Segunda prioridad — revisar primero
    if has_attachments:
        return "AMARILLO", "Tiene adjuntos"
    important_kw = [
        "diploma", "certificado", "título", "constancia", "contrato",
        "factura", "recibo", "reserva", "confirmación", "comprobante",
        "curriculum", " cv ", "titulación", "matrícula", "beca",
    ]
    if any(kw in subject for kw in important_kw):
        return "AMARILLO", "Asunto contiene término de documento importante"
    institution_kw = [
        "banco", "bank", "universidad", "edu.", ".edu", ".gob.", ".gov.",
        "hospital", "clinica", "clinic", "hacienda", "seguro social",
        "imss", "issste", "insurance", "ministerio", "secretaría",
    ]
    if any(kw in sender for kw in institution_kw):
        return "AMARILLO", "Remitente parece ser institución importante"

    # 🟢 Candidatos a papelera
    if has_list_unsub and days_old > 60:
        return "VERDE", f"Newsletter con List-Unsubscribe, sin abrir {days_old} días"
    promo_kw = [
        "oferta", "descuento", "% off", " off ", "sale", "unsubscribe",
        "newsletter", "promocion", "promo", "deal", "gratis", "free",
        "exclusivo para ti", "black friday", "cyber monday",
    ]
    if any(kw in subject for kw in promo_kw):
        return "VERDE", "Asunto contiene términos promocionales"
    social_senders = [
        "facebook", "instagram", "linkedin", "twitter", "x.com",
        "tiktok", "youtube", "pinterest", "snapchat", "telegram",
    ]
    if any(sn in sender for sn in social_senders):
        return "VERDE", "Notificación automática de red social"
    if ("no-reply" in sender or "noreply" in sender or "no_reply" in sender
            or "donotreply" in sender):
        if not has_attachments:
            return "VERDE", "Email de no-reply sin adjuntos"

    return "AMARILLO", "Clasificación incierta — requiere revisión manual"


def _tools_to_anthropic(mcp_tools: list) -> list[dict]:
    """Convierte herramientas MCP al formato que acepta la API de Anthropic."""
    result = []
    for t in mcp_tools:
        schema = t.inputSchema if hasattr(t, "inputSchema") else {}
        result.append({
            "name": t.name,
            "description": t.description or "",
            "input_schema": schema or {"type": "object", "properties": {}},
        })
    return result


def _print_separator(title: str = "") -> None:
    if title:
        print(f"\n{'═' * 60}")
        print(f"  {title}")
        print("═" * 60)
    else:
        print("─" * 60)


async def _run_analysis_phase(
    session: ClientSession,
    client: anthropic.Anthropic,
    tools_anthropic: list[dict],
) -> list[dict]:
    """
    Fase 1: Claude analiza y clasifica todos los correos.
    Devuelve la lista de emails clasificados como VERDE disponibles para aprobación.
    """
    queries_str = "\n".join(
        f"  {i+1}. {q['label']}: {q['query']}"
        for i, q in enumerate(cfg.SCAN_QUERIES)
    )
    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                f"Analiza mi Gmail ejecutando estas búsquedas en este orden:\n{queries_str}\n\n"
                f"Trabaja en lotes de {BATCH_SIZE} correos por búsqueda. "
                "Para cada correo identifica: remitente (from), asunto (subject), "
                "fecha, días desde envío, si tiene adjuntos, si tiene cabecera "
                "List-Unsubscribe, si fue respondido por mí, si está marcado "
                "con estrella, y sus etiquetas. "
                "Muestra el recuento de correos encontrados por query ANTES de clasificar. "
                "Luego clasifica según las categorías 🟢/🟡/🔴 del sistema prompt, "
                "aplicando primero las listas personalizadas del usuario. "
                "Genera el reporte completo con los grupos y tamaño estimado."
            ),
        }
    ]

    green_emails: list[dict] = []
    report_done = False

    while not report_done:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8192,
            system=_build_system_prompt(),
            tools=tools_anthropic,
            messages=messages,
        )

        assistant_blocks: list[Any] = []
        tool_calls: list[Any] = []

        for block in response.content:
            if block.type == "text":
                print(block.text)
                assistant_blocks.append({"type": "text", "text": block.text})
                if "REPORTE_COMPLETO" in block.text:
                    report_done = True
            elif block.type == "tool_use":
                tool_calls.append(block)
                assistant_blocks.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
                print(f"\n  🔧 {block.name}({json.dumps(block.input, ensure_ascii=False)[:80]}...)")

        messages.append({"role": "assistant", "content": assistant_blocks})

        if response.stop_reason == "end_turn" and not tool_calls:
            break

        if not tool_calls:
            continue

        # Ejecutar herramientas MCP y recopilar emails para clasificación local
        tool_results: list[dict] = []
        for tc in tool_calls:
            try:
                result = await session.call_tool(tc.name, tc.input or {})
                raw = result.content[0].text if result.content else "{}"
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": raw,
                })
                # Intentar extraer emails para clasificación local
                try:
                    data = json.loads(raw)
                    emails = data if isinstance(data, list) else data.get("messages", [])
                    for email in emails:
                        cat, reason = classify_email(email)
                        email["_category"] = cat
                        email["_reason"] = reason
                        if cat == "VERDE":
                            green_emails.append(email)
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass
            except Exception as exc:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": f"Error al llamar herramienta: {exc}",
                    "is_error": True,
                })

        messages.append({"role": "user", "content": tool_results})

    return green_emails


async def _run_execution_phase(
    session: ClientSession,
    client: anthropic.Anthropic,
    tools_anthropic: list[dict],
    approved_emails: list[dict],
) -> tuple[int, int]:
    """
    Fase 3: Claude mueve a papelera los correos aprobados.
    Devuelve (movidos, errores).
    """
    if not approved_emails:
        return 0, 0

    ids = [e.get("id") or e.get("message_id") for e in approved_emails if e.get("id") or e.get("message_id")]
    if not ids:
        print("\n⚠️  Los correos aprobados no tienen IDs accesibles para mover.")
        print("   Intenta con la opción [2] seleccionando remitentes específicos.")
        return 0, 0

    moved = 0
    errors = 0

    for i in range(0, len(ids), BATCH_SIZE):
        batch_ids = ids[i:i + BATCH_SIZE]
        batch_emails = approved_emails[i:i + BATCH_SIZE]

        messages: list[dict] = [
            {
                "role": "user",
                "content": (
                    f"Mueve a la papelera (trash) los siguientes {len(batch_ids)} correos. "
                    "Usa la herramienta apropiada para hacer trash de cada mensaje. "
                    f"IDs: {json.dumps(batch_ids)}. "
                    "Confirma cuántos moviste con éxito."
                ),
            }
        ]

        while True:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=_build_system_prompt(),
                tools=tools_anthropic,
                messages=messages,
            )

            assistant_blocks: list[Any] = []
            tool_calls: list[Any] = []

            for block in response.content:
                if block.type == "text":
                    print(block.text)
                    assistant_blocks.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    tool_calls.append(block)
                    assistant_blocks.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            messages.append({"role": "assistant", "content": assistant_blocks})

            if response.stop_reason == "end_turn" and not tool_calls:
                break

            if not tool_calls:
                continue

            tool_results: list[dict] = []
            for j, tc in enumerate(tool_calls):
                email = batch_emails[j] if j < len(batch_emails) else {}
                sender = email.get("from") or email.get("sender") or "desconocido"
                subject = email.get("subject") or "(sin asunto)"
                try:
                    result = await session.call_tool(tc.name, tc.input or {})
                    raw = result.content[0].text if result.content else "{}"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": raw,
                    })
                    moved += 1
                    log_action(
                        "MOVIDO_A_PAPELERA", sender, subject,
                        f"ID={tc.input.get('message_id', 'N/A')} | Razón={email.get('_reason', 'N/A')}",
                    )
                    print(f"  ✓ {sender[:35]} — {subject[:45]}")
                except Exception as exc:
                    errors += 1
                    log_action("ERROR", sender, subject, f"Error: {exc}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc.id,
                        "content": f"Error: {exc}",
                        "is_error": True,
                    })
                    print(f"  ✗ Error: {sender[:35]} — {str(exc)[:60]}")

            messages.append({"role": "user", "content": tool_results})

    return moved, errors


async def run_agent() -> None:
    _print_separator("AGENTE DE GESTIÓN DE GMAIL — LIMPIEZA SEGURA")

    # Validar variables de entorno
    required = ["GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET", "GMAIL_REFRESH_TOKEN"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        print(f"\n❌ Faltan variables de entorno: {', '.join(missing)}")
        print("   Consulta oauth_setup.md para configurar la autenticación OAuth2.")
        sys.exit(1)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n❌ Falta la variable de entorno: ANTHROPIC_API_KEY")
        print("   Obtén tu clave en https://console.anthropic.com/")
        sys.exit(1)

    log_action("INICIO", "N/A", "N/A", "Agente iniciado")
    print("\nConectando con Gmail via MCP...")

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-gmail"],
        env={
            **os.environ,
            "GMAIL_CLIENT_ID": os.environ["GMAIL_CLIENT_ID"],
            "GMAIL_CLIENT_SECRET": os.environ["GMAIL_CLIENT_SECRET"],
            "GMAIL_REFRESH_TOKEN": os.environ["GMAIL_REFRESH_TOKEN"],
        },
    )

    client = anthropic.Anthropic()

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            tools_anthropic = _tools_to_anthropic(tools_result.tools)

            print(f"✅ Conexión MCP establecida — {len(tools_anthropic)} herramientas disponibles")
            for t in tools_anthropic:
                print(f"   • {t['name']}")

            # ──────────────────────────────────────────────────────
            # FASE 1: ANÁLISIS Y CLASIFICACIÓN
            # ──────────────────────────────────────────────────────
            _print_separator("FASE 1 — ANÁLISIS Y CLASIFICACIÓN")
            print("Escaneando correos (puede tardar unos minutos)...\n")

            green_emails = await _run_analysis_phase(session, client, tools_anthropic)

            # ──────────────────────────────────────────────────────
            # FASE 2: APROBACIÓN DEL USUARIO
            # ──────────────────────────────────────────────────────
            _print_separator("FASE 2 — APROBACIÓN")
            print(f"\nEl agente identificó {len(green_emails)} correos candidatos (🟢).")
            print("\nOpciones:")
            print("  [1] Aprobar todos los grupos VERDES (recomendado)")
            print("  [2] Aprobar remitentes específicos (escribir manualmente)")
            print("  [3] Cancelar — no mover nada")

            approved: list[dict] = []

            while True:
                choice = input("\nTu elección (1/2/3): ").strip()

                if choice == "1":
                    approved = list(green_emails)
                    print(f"\n✅ Aprobados {len(approved)} correos para mover a papelera.")
                    break

                elif choice == "2":
                    print("\nEscribe remitentes a aprobar, separados por coma.")
                    print("Ejemplo: newsletter@ejemplo.com, promos@tienda.com")
                    raw = input("> ").strip()
                    selected = [s.strip().lower() for s in raw.split(",") if s.strip()]
                    approved = [
                        e for e in green_emails
                        if any(
                            sel in (e.get("from") or e.get("sender") or "").lower()
                            for sel in selected
                        )
                    ]
                    print(f"\n✅ Seleccionados {len(approved)} correos para mover a papelera.")
                    break

                elif choice == "3":
                    print("\n❌ Operación cancelada. No se realizaron cambios.")
                    log_action("CANCELADO", "N/A", "N/A", "Usuario canceló la operación")
                    return

                else:
                    print("Por favor escribe 1, 2 o 3.")

            if not approved:
                print("\nNo hay correos aprobados para procesar. Saliendo.")
                return

            # Confirmación final antes de ejecutar
            confirm = input(
                f"\n⚠️  ¿Confirmas mover {len(approved)} correos a la PAPELERA? (s/n): "
            ).strip().lower()

            if confirm != "s":
                print("\n❌ Operación cancelada.")
                log_action("CANCELADO", "N/A", "N/A", "Usuario no confirmó la ejecución")
                return

            # ──────────────────────────────────────────────────────
            # FASE 3: EJECUCIÓN
            # ──────────────────────────────────────────────────────
            _print_separator("FASE 3 — EJECUCIÓN")
            print(f"\nMoviendo {len(approved)} correos a la papelera...\n")

            moved, errors = await _run_execution_phase(
                session, client, tools_anthropic, approved
            )

            # ──────────────────────────────────────────────────────
            # RESUMEN FINAL
            # ──────────────────────────────────────────────────────
            _print_separator("RESUMEN FINAL")
            print(f"\n✅ Correos movidos a papelera : {moved}")
            if errors:
                print(f"⚠️  Errores encontrados       : {errors}")
            print(f"📋 Log guardado en           : {LOG_FILE.absolute()}")
            print(
                "\n💡 Los correos están en la papelera de Gmail. "
                "Tienes 30 días para recuperarlos si fue un error.\n"
            )
            log_action(
                "RESUMEN", "N/A", "N/A",
                f"Movidos={moved} | Errores={errors} | Total aprobados={len(approved)}",
            )


if __name__ == "__main__":
    asyncio.run(run_agent())
