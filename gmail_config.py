"""
gmail_config.py — Configuración personalizada del agente de limpieza Gmail.

Edita este archivo para adaptar el agente a tus preferencias.
Los cambios aquí se aplican automáticamente al ejecutar gmail_agent.py.
"""

# ──────────────────────────────────────────────────────────────────────────────
# 🟢 REMITENTES SEGUROS — se mueven a papelera SIN pedir aprobación
#    Añade dominios completos (ejemplo.com) o palabras parciales del remitente.
# ──────────────────────────────────────────────────────────────────────────────
SAFE_TO_TRASH: list[str] = [
    # Viajes y transporte
    "skyscanner",
    "ryanair",
    "civitatis",
    "getyourguide",
    "omio",
    "trainline",

    # Comercio electrónico y ofertas
    "groupon",
    "aliexpress",
    "bolt",         # Bolt food / rides newsletters
    "adidas",
    "instant gaming",

    # Servicios financieros (solo newsletters, no transacciones)
    "fintonic",     # Solo alertas de marketing, no extractos

    # Ocio y entretenimiento
    "live nation",
    "kinepolis",
    "ilusiona",
    "goiko",
    "nvidia gaming",

    # Empleo
    "infojobs",
]

# ──────────────────────────────────────────────────────────────────────────────
# 🔴 REMITENTES PROTEGIDOS — NUNCA se tocan, aunque cumplan criterios de borrado
#    Tienen prioridad absoluta sobre SAFE_TO_TRASH y sobre las reglas genéricas.
# ──────────────────────────────────────────────────────────────────────────────
ALWAYS_PROTECT: list[str] = [
    # Entradas y eventos (pueden tener tickets adjuntos)
    "ticketmaster",

    # Pagos y finanzas
    "paypal",
    "revolut",

    # Administración pública
    "agencia tributaria",
    "aeat",
    "sede.gob",
    "correos.es",   # Puede traer notificaciones de Hacienda

    # Bancos (cualquier banco — añade los tuyos)
    "bbva",
    "santander",
    "caixabank",
    "sabadell",
    "bankinter",
    "ing.es",
    "openbank",

    # Viajes confirmados (tickets, reservas, boarding passes)
    "vueling",
    "iberia",
    "renfe",
    "booking.com",
    "airbnb",

    # Palabras clave en asunto que activan protección
    # (aunque el remitente esté en SAFE_TO_TRASH)
]

# Palabras clave en el ASUNTO que siempre activan protección 🔴
# aunque el remitente esté en SAFE_TO_TRASH
PROTECT_SUBJECT_KEYWORDS: list[str] = [
    "factura",
    "recibo",
    "confirmación de reserva",
    "boarding pass",
    "tarjeta de embarque",
    "tu vuelo",
    "tu pedido",
    "extracto",
    "contrato",
    "comprobante",
    "ticket",
    "entrada",
    "evento",
]

# ──────────────────────────────────────────────────────────────────────────────
# 📁 QUERIES DE ESCANEO — orden y filtros de búsqueda en Gmail
#    Gmail search syntax: https://support.google.com/mail/answer/7190
# ──────────────────────────────────────────────────────────────────────────────
SCAN_QUERIES: list[dict] = [
    {
        "label": "Promociones (+7 días)",
        "query": "category:promotions older_than:7d",
        "description": "Emails de la pestaña Promociones con más de 7 días",
    },
    {
        "label": "Actualizaciones (+30 días)",
        "query": "category:updates older_than:30d",
        "description": "Emails de la pestaña Actualizaciones con más de 30 días",
    },
    {
        "label": "Social (+30 días)",
        "query": "category:social older_than:30d",
        "description": "Emails de la pestaña Social con más de 30 días",
    },
]

# ──────────────────────────────────────────────────────────────────────────────
# ⚙️  AJUSTES GENERALES
# ──────────────────────────────────────────────────────────────────────────────
BATCH_SIZE: int = 100           # Correos por lote de procesamiento
AUTO_TRASH_SAFE: bool = True    # True = mover SAFE_TO_TRASH sin pedir aprobación
                                # False = mostrar igualmente para aprobación manual
