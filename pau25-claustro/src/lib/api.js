const API_URL = "https://api.anthropic.com/v1/messages";
const MODEL = "claude-sonnet-4-20250514";

export async function callClaude({ systemPrompt, messages, maxTokens = 1024 }) {
  const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error("Falta VITE_ANTHROPIC_API_KEY en .env.local");

  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
      "anthropic-dangerous-direct-browser-access": "true"
    },
    body: JSON.stringify({
      model: MODEL,
      max_tokens: maxTokens,
      system: systemPrompt,
      messages
    })
  });
  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    throw new Error(`API error ${res.status}: ${errText}`);
  }
  const data = await res.json();
  return data.content?.map(b => b.text || "").join("") || "";
}
