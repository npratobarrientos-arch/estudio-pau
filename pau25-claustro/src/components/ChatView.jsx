import { useState, useEffect, useRef } from "react";
import { callClaude } from "../lib/api.js";
import { setTopicStatus, loadSettings } from "../lib/storage.js";
import { FACTORY_MODE_ADDON, SESSION_TIME_ADDON } from "../data/method.js";
import AnkiModal from "./AnkiModal.jsx";

const page = {
  minHeight: "100vh", background: "#0f0f23", color: "#e8e0d4",
  fontFamily: "'Segoe UI', system-ui, sans-serif",
  display: "flex", flexDirection: "column"
};
const header = (color) => ({
  background: "#13132a", borderBottom: `1px solid ${color}55`,
  padding: "14px 20px", display: "flex", alignItems: "center", gap: 14,
  position: "sticky", top: 0, zIndex: 10
});
const headerAvatar = (color) => ({
  background: `${color}33`, color, width: 44, height: 44, borderRadius: 22,
  display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22,
  flexShrink: 0
});
const backBtn = {
  background: "transparent", color: "#888", border: "1px solid #2d2d4e",
  padding: "6px 12px", borderRadius: 8, cursor: "pointer", fontSize: 12
};
const messages = {
  flex: 1, overflowY: "auto", padding: "20px 16px",
  maxWidth: 900, width: "100%", margin: "0 auto"
};
const msgRow = (role) => ({
  display: "flex", justifyContent: role === "user" ? "flex-end" : "flex-start",
  marginBottom: 14
});
const msgBubble = (role, color) => ({
  maxWidth: "78%", padding: "12px 16px", borderRadius: 14,
  background: role === "user" ? color : "#1e1e3a",
  color: role === "user" ? "#fff" : "#e8e0d4",
  fontSize: 15, lineHeight: 1.55, whiteSpace: "pre-wrap", wordBreak: "break-word",
  boxShadow: role === "user" ? `0 2px 8px ${color}33` : "0 2px 8px rgba(0,0,0,0.2)"
});
const chips = {
  display: "flex", gap: 8, flexWrap: "wrap",
  padding: "10px 16px 0", maxWidth: 900, margin: "0 auto", width: "100%"
};
const chip = (color) => ({
  background: `${color}22`, color, border: `1px solid ${color}44`,
  padding: "6px 12px", borderRadius: 16, cursor: "pointer", fontSize: 12,
  whiteSpace: "nowrap"
});
const inputBar = {
  display: "flex", gap: 10, padding: 16, borderTop: "1px solid #2d2d4e",
  background: "#0f0f23", maxWidth: 900, margin: "0 auto", width: "100%", boxSizing: "border-box"
};
const textarea = {
  flex: 1, background: "#1a1a2e", color: "#e8e0d4",
  border: "1px solid #2d2d4e", borderRadius: 10, padding: "10px 14px",
  fontSize: 15, fontFamily: "inherit", resize: "none", minHeight: 44, maxHeight: 200,
  outline: "none"
};
const sendBtn = (color) => ({
  background: color, color: "#fff", border: "none",
  padding: "0 22px", borderRadius: 10, cursor: "pointer", fontWeight: 600,
  fontSize: 15
});
const dotsRow = { display: "flex", gap: 4, padding: "10px 14px" };
const dot = (i) => ({
  width: 8, height: 8, borderRadius: 4, background: "#888",
  animation: `bounce 1.2s infinite ${i * 0.2}s`
});

const QUICK_CHIPS = [
  "No me ha quedado claro, otro ejemplo",
  "Hazme una pregunta de examen",
  "Conecta con otro tema",
  "Resume lo que llevamos"
];

export default function ChatView({ subject, topic, mode, onBack }) {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showAnki, setShowAnki] = useState(false);
  const scrollRef = useRef(null);

  function buildSystemPrompt() {
    const settings = loadSettings();
    let sys = subject.systemPrompt;
    if (settings.factoryMode) sys += "\n\n" + FACTORY_MODE_ADDON;
    sys += "\n\n" + SESSION_TIME_ADDON(settings.sessionMinutes);

    if (mode === "exam") {
      sys += `\n\nMODO EXAMEN SORPRESA: el alumno está haciendo un examen sorpresa del punto ${topic.id} (${topic.title}) que estudió hace días. Pregúntale directamente algo del punto sin previo aviso ("A ver, sin mirar nada: cuéntame qué era X"). Si no se acuerda, NO se lo des — ayúdale a recuperarlo con pistas socráticas. Al final, evalúa lo que ha retenido.`;
    } else {
      sys += `\n\nINICIO DE SESIÓN: el alumno acaba de seleccionar el punto ${topic.id} — ${topic.title} (${topic.sub}). Empieza la FASE 1 del método: pregúntale qué sabe ya de esto, presenta UNA idea central, y pídele que reformule con sus palabras. No le sueltes el temario entero.`;
    }
    return sys;
  }

  useEffect(() => {
    setTopicStatus(subject.id, topic.id, "in-progress");
    const kickoff = mode === "exam"
      ? `Empieza el examen sorpresa sobre el punto ${topic.id}: ${topic.title}.`
      : `Quiero estudiar el punto ${topic.id}: ${topic.title} (${topic.sub}).`;
    sendMessage(kickoff, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [msgs, loading]);

  async function sendMessage(text, isKickoff = false) {
    if (!text.trim() || loading) return;
    const newUserMsg = { role: "user", content: text };
    const baseMsgs = isKickoff ? [] : msgs;
    const next = [...baseMsgs, newUserMsg];
    setMsgs(isKickoff ? [{ role: "user", content: text, hidden: true }] : next);
    setInput("");
    setLoading(true);
    try {
      const apiMessages = next.map(m => ({ role: m.role, content: m.content }));
      const reply = await callClaude({
        systemPrompt: buildSystemPrompt(),
        messages: apiMessages,
        maxTokens: 1200
      });
      setMsgs(prev => {
        const base = isKickoff ? [] : prev;
        return [...(isKickoff ? [] : base), { role: "assistant", content: reply }];
      });
    } catch (e) {
      setMsgs(prev => [...prev, { role: "assistant", content: `⚠️ Error: ${e.message}. Comprueba tu API key en .env.local.` }]);
    } finally {
      setLoading(false);
    }
  }

  function handleSend() {
    sendMessage(input);
  }

  function markMastered() {
    if (confirm("¿Marcar este punto como dominado?")) {
      setTopicStatus(subject.id, topic.id, "mastered");
      onBack();
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const visibleMsgs = msgs.filter(m => !m.hidden);

  return (
    <div style={page}>
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-6px); opacity: 1; }
        }
      `}</style>
      <div style={header(subject.color)}>
        <button style={backBtn} onClick={onBack}>←</button>
        <div style={headerAvatar(subject.color)}>{subject.emoji}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontFamily: "Georgia, serif", fontSize: 17, color: "#e8e0d4" }}>
            {subject.professor.name}
          </div>
          <div style={{ color: subject.color, fontSize: 12, fontWeight: 600,
            overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {mode === "exam" ? "🎲 Examen sorpresa · " : ""}Punto {topic.id} — {topic.title}
          </div>
        </div>
      </div>

      <div style={messages} ref={scrollRef}>
        {visibleMsgs.map((m, i) => (
          <div key={i} style={msgRow(m.role)}>
            <div style={msgBubble(m.role, subject.color)}>{m.content}</div>
          </div>
        ))}
        {loading && (
          <div style={msgRow("assistant")}>
            <div style={{ ...msgBubble("assistant", subject.color), padding: 0 }}>
              <div style={dotsRow}>
                <div style={dot(0)}></div>
                <div style={dot(1)}></div>
                <div style={dot(2)}></div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div style={chips}>
        {QUICK_CHIPS.map((c, i) => (
          <button key={i} style={chip(subject.color)} onClick={() => sendMessage(c)} disabled={loading}>
            {c}
          </button>
        ))}
        <button style={chip(subject.color)} onClick={markMastered} disabled={loading}>
          ✅ Marcar dominado
        </button>
        <button style={chip(subject.color)} onClick={() => setShowAnki(true)} disabled={loading || visibleMsgs.length < 2}>
          📇 Exportar a Anki
        </button>
      </div>

      <div style={inputBar}>
        <textarea
          style={textarea}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Escribe tu respuesta… (Enter para enviar, Shift+Enter salto de línea)"
          rows={1}
        />
        <button style={sendBtn(subject.color)} onClick={handleSend} disabled={loading || !input.trim()}>
          Enviar
        </button>
      </div>

      {showAnki && (
        <AnkiModal
          subject={subject}
          topic={topic}
          messages={visibleMsgs}
          onClose={() => setShowAnki(false)}
        />
      )}
    </div>
  );
}
