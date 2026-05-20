import { useState, useEffect } from "react";
import { generateAnkiCards, formatForAnki, formatForText } from "../lib/anki.js";

const overlay = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)",
  display: "flex", alignItems: "center", justifyContent: "center",
  zIndex: 100, padding: 20
};
const panel = {
  background: "#13132a", border: "1px solid #2d2d4e", borderRadius: 14,
  padding: 26, width: "min(720px, 96vw)", maxHeight: "90vh",
  overflowY: "auto", color: "#e8e0d4",
  fontFamily: "'Segoe UI', system-ui, sans-serif"
};
const header = { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 };
const title = { fontFamily: "Georgia, serif", fontSize: 22, margin: 0 };
const closeX = { background: "transparent", border: "none", color: "#888", fontSize: 24, cursor: "pointer" };
const card = (color) => ({
  background: "#1a1a2e", border: `1px solid ${color}55`, borderLeft: `4px solid ${color}`,
  borderRadius: 10, padding: 16, marginBottom: 12
});
const cardTitle = (color) => ({ color, fontSize: 13, fontWeight: 700, letterSpacing: 0.5, marginBottom: 8 });
const q = { color: "#e8e0d4", fontSize: 14, fontWeight: 600, marginBottom: 6 };
const a = { color: "#cccccc", fontSize: 14, lineHeight: 1.6 };
const buttons = { display: "flex", gap: 10, marginTop: 18, flexWrap: "wrap" };
const btn = (color) => ({
  background: color, color: "#fff", border: "none",
  padding: "10px 18px", borderRadius: 8, cursor: "pointer", fontWeight: 600, fontSize: 14
});
const btnSec = (color) => ({
  background: "transparent", color, border: `1px solid ${color}`,
  padding: "10px 18px", borderRadius: 8, cursor: "pointer", fontWeight: 600, fontSize: 14
});
const loading = { color: "#888", textAlign: "center", padding: 40 };

export default function AnkiModal({ subject, topic, messages, onClose }) {
  const [cards, setCards] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const c = await generateAnkiCards(subject, topic, messages);
        if (!cancelled) setCards(c);
      } catch (e) {
        if (!cancelled) setError(e.message || "Error generando fichas");
      }
    })();
    return () => { cancelled = true; };
  }, [subject, topic, messages]);

  function copyAnki() {
    navigator.clipboard.writeText(formatForAnki(cards));
    setCopied("anki");
    setTimeout(() => setCopied(""), 2000);
  }
  function copyText() {
    navigator.clipboard.writeText(formatForText(cards));
    setCopied("text");
    setTimeout(() => setCopied(""), 2000);
  }

  return (
    <div style={overlay} onClick={onClose}>
      <div style={panel} onClick={e => e.stopPropagation()}>
        <div style={header}>
          <h2 style={title}>📇 Fichas Anki · {topic.title}</h2>
          <button style={closeX} onClick={onClose}>×</button>
        </div>

        {!cards && !error && (
          <div style={loading}>
            <div style={{ fontSize: 28 }}>⏳</div>
            <div>Generando 3 fichas con {subject.professor.name}…</div>
          </div>
        )}

        {error && (
          <div style={{ color: "#e74c3c", padding: 20, background: "#2a1818", borderRadius: 8 }}>
            Error: {error}
          </div>
        )}

        {cards && cards.map((c, i) => (
          <div key={i} style={card(subject.color)}>
            <div style={cardTitle(subject.color)}>FICHA {i + 1} — {c.title}</div>
            <div style={q}>{c.q}</div>
            <div style={a}>{c.a}</div>
          </div>
        ))}

        {cards && (
          <div style={buttons}>
            <button style={btn(subject.color)} onClick={copyAnki}>
              {copied === "anki" ? "✓ Copiado" : "📋 Copiar para Anki (tab)"}
            </button>
            <button style={btnSec(subject.color)} onClick={copyText}>
              {copied === "text" ? "✓ Copiado" : "📝 Copiar como texto"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
