# Claustro PAU+25

App web local que actúa como un claustro de 6 catedráticos virtuales + un Jefe de Estudios, especializados en la prueba PAU+25 de la Universitat de València (rama Artes y Humanidades). Cada catedrático enseña una asignatura siguiendo el método Feynman + Socrático.

## Cómo empezar

### 1. Conseguir una API Key de Anthropic

1. Entra en https://console.anthropic.com/
2. Regístrate o inicia sesión.
3. Ve a **API Keys** y pulsa **Create Key**.
4. Copia la key (empieza por `sk-ant-api03-...`).

### 2. Pegar la key

Abre `.env.local` y pega tu key tras el `=`:

```
VITE_ANTHROPIC_API_KEY=sk-ant-api03-tu-key-aqui
```

### 3. Arrancar la app

```bash
npm install      # solo la primera vez
npm run dev
```

Abre la URL que te muestra Vite (normalmente http://localhost:5173).

## Stack

- Vite + React 18 (JavaScript)
- Llamadas directas a la API de Anthropic desde el navegador (uso personal local)
- Persistencia en `localStorage`
- Sin librerías UI externas, sin Tailwind, sin router

## Estructura

```
src/
├── data/         # Método pedagógico + 6 catedráticos + jefe + puentes
├── lib/          # Cliente API + storage + generador Anki
└── components/   # Home · TopicSelector · ChatView · HeadOfStudies · …
```

## Privacidad

Tu API key vive solo en `.env.local` (ignorado por git). Las conversaciones se envían a la API de Anthropic. El progreso se guarda únicamente en tu navegador.
