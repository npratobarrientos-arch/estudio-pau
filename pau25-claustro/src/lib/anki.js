import { callClaude } from "./api.js";

const ANKI_PROMPT = `Eres el mismo catedrático que ha estado enseñando. Basándote en la conversación que ha ocurrido, genera EXACTAMENTE 3 fichas Anki sobre el punto trabajado:

FICHA 1 — CONCEPTO CENTRAL: definición clara del concepto principal del punto.
FICHA 2 — APLICACIÓN AL EXAMEN: si sale esto en el examen, qué tienes que escribir.
FICHA 3 — CONEXIÓN O CONTRASTE: relaciona con otro concepto del temario o contrasta con un autor/idea contraria.

Devuelve SOLO un JSON válido sin texto adicional, sin bloques de código, con este formato exacto:
{"cards":[{"title":"...","q":"...","a":"..."},{"title":"...","q":"...","a":"..."},{"title":"...","q":"...","a":"..."}]}`;

export async function generateAnkiCards(subject, topic, messages) {
  const userPrompt = `Tema trabajado: punto ${topic.id} — ${topic.title} (${topic.sub}).
Genera las 3 fichas Anki ahora en JSON estricto, sin más texto.`;
  const conversationContext = messages.map(m => `${m.role}: ${m.content}`).join("\n\n");
  const fullSystem = subject.systemPrompt + "\n\n" + ANKI_PROMPT + "\n\nCONVERSACIÓN RECIENTE:\n" + conversationContext;
  const raw = await callClaude({
    systemPrompt: fullSystem,
    messages: [{ role: "user", content: userPrompt }],
    maxTokens: 1500
  });
  const clean = raw.replace(/```json|```/g, "").trim();
  try {
    return JSON.parse(clean).cards;
  } catch {
    return [{ title: "Error", q: "No se pudieron generar las fichas", a: raw }];
  }
}

export function formatForAnki(cards) {
  return cards.map(c => `${c.title}: ${c.q}\t${c.a}`).join("\n");
}

export function formatForText(cards) {
  return cards.map((c, i) =>
    `FICHA ${i + 1} — ${c.title}\n\nPregunta:\n${c.q}\n\nRespuesta:\n${c.a}`
  ).join("\n\n---\n\n");
}
